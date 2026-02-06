"""Output collector for monitoring agent progress."""

import asyncio
import logging
import re
import time
from pathlib import Path
from typing import Callable, Optional

from cat.agent.models import AgentRole, AgentStatus
from cat.agent.registry import AgentRegistry
from cat.agent.controller import AgentController
from cat.interactive.config import ProjectConfig
from cat.workflow.exceptions import OutputCollectionError, AgentTimeoutError
from cat.workflow.performance import LRUCache, timed, benchmark

logger = logging.getLogger(__name__)


class OutputCollector:
    """Collects and monitors agent outputs for completion signals."""

    def __init__(
        self,
        config: ProjectConfig,
        controller: AgentController,
        registry: AgentRegistry,
        poll_interval: float = 2.0,
        agent_timeout: int = 3600,  # 1 hour default
    ):
        self.config = config
        self.controller = controller
        self.registry = registry
        self.poll_interval = poll_interval
        self.agent_timeout = agent_timeout
        self._running = False
        self._callbacks: dict[str, list[Callable]] = {
            "output": [],
            "completed": [],
            "failed": [],
            "progress": [],
            "timeout": [],
        }
        self._agent_start_times: dict[AgentRole, float] = {}

        # Output caching for performance
        self._output_cache = LRUCache(max_size=50)
        self._last_output_hash: dict[AgentRole, int] = {}

    def on_output(self, callback: Callable[[AgentRole, str], None]) -> None:
        """Register callback for agent output.

        Args:
            callback: Function called with (role, output_text)
        """
        self._callbacks["output"].append(callback)

    def on_completed(self, callback: Callable[[AgentRole], None]) -> None:
        """Register callback for agent completion.

        Args:
            callback: Function called with role
        """
        self._callbacks["completed"].append(callback)

    def on_failed(self, callback: Callable[[AgentRole, str], None]) -> None:
        """Register callback for agent failure.

        Args:
            callback: Function called with (role, error_message)
        """
        self._callbacks["failed"].append(callback)

    def on_progress(self, callback: Callable[[AgentRole, int], None]) -> None:
        """Register callback for progress updates.

        Args:
            callback: Function called with (role, progress_percent)
        """
        self._callbacks["progress"].append(callback)

    def on_timeout(self, callback: Callable[[AgentRole, int], None]) -> None:
        """Register callback for agent timeout.

        Args:
            callback: Function called with (role, timeout_seconds)
        """
        self._callbacks["timeout"].append(callback)

    def _emit(self, event: str, *args) -> None:
        """Emit an event to all registered callbacks."""
        for callback in self._callbacks.get(event, []):
            try:
                callback(*args)
            except Exception as e:
                logger.warning(f"Callback error for {event}: {e}")

    @timed("check_agent")
    def check_agent(self, role: AgentRole) -> Optional[str]:
        """Check agent output for completion or errors.

        Args:
            role: Agent role to check

        Returns:
            Completion signal if found, None otherwise

        Raises:
            OutputCollectionError: If output cannot be collected
            AgentTimeoutError: If agent has exceeded timeout
        """
        try:
            # Check for timeout
            state = self.registry.get(role)
            if state and state.started_at:
                # Track start time
                if role not in self._agent_start_times:
                    self._agent_start_times[role] = time.time()

                # Check timeout
                elapsed = time.time() - self._agent_start_times[role]
                if elapsed > self.agent_timeout:
                    error = AgentTimeoutError(
                        role,
                        self.agent_timeout,
                        state.iteration_count,
                    )
                    logger.error(f"Agent timeout: {error}")
                    self.registry.update_status(
                        role,
                        AgentStatus.FAILED,
                        error_message=str(error),
                    )
                    self._emit("timeout", role, self.agent_timeout)
                    raise error

            # Collect output with caching
            cache_key = f"{role.value}_output"
            cached_output = self._output_cache.get(cache_key, max_age=1.0)  # 1 second cache

            if cached_output is not None:
                output = cached_output
                logger.debug(f"Using cached output for {role.display_name}")
            else:
                with benchmark(f"capture_output_{role.value}"):
                    output = self.controller.capture_output(role.value, lines=100)

                if output:
                    # Cache the output
                    self._output_cache.put(cache_key, output)

            if not output:
                return None

            # Check if output changed (avoid redundant processing)
            output_hash = hash(output)
            if role in self._last_output_hash and self._last_output_hash[role] == output_hash:
                logger.debug(f"Output unchanged for {role.display_name}")
                return None

            self._last_output_hash[role] = output_hash

            # Save last output to registry
            self.registry.set_last_output(role, output)

            # Save output to file
            output_file = self.config.config_dir / "logs" / f"{role.value}.log"
            output_file.parent.mkdir(parents=True, exist_ok=True)

            try:
                with open(output_file, "a") as f:
                    f.write(output + "\n---\n")
            except IOError as e:
                logger.warning(f"Could not write log file for {role.display_name}: {e}")

            # Emit output event
            self._emit("output", role, output)

            # Check for completion signal
            completion_signal = self.config.get_completion_signal(role)
            pattern = rf"<promise>{completion_signal}</promise>"

            if re.search(pattern, output, re.IGNORECASE):
                logger.info(f"{role.display_name} completed with signal: {completion_signal}")
                return completion_signal

            # Check for critical error patterns
            error_patterns = [
                (r"FATAL:", "Fatal error encountered"),
                (r"failed with exit code (\d+)", "Process exited with error code"),
                (r"Permission denied", "Permission denied"),
                (r"No space left on device", "Disk full"),
            ]

            for pattern, description in error_patterns:
                match = re.search(pattern, output, re.IGNORECASE)
                if match:
                    logger.warning(f"{role.display_name}: {description}")
                    # Don't immediately fail - agent might recover
                    # But log for visibility

            return None

        except AgentTimeoutError:
            # Re-raise timeout errors
            raise

        except Exception as e:
            error = OutputCollectionError(role, "Failed to collect output", original_error=e)
            logger.error(f"Collection error: {error}", exc_info=True)
            raise error

    def poll_once(self) -> list[AgentRole]:
        """Poll all active agents once.

        Returns:
            List of agents that completed

        Note:
            Handles timeouts and errors gracefully. Failed agents
            are marked in registry but don't stop polling.
        """
        completed = []

        for state in self.registry.active_agents:
            role = state.role

            try:
                signal = self.check_agent(role)

                if signal:
                    # Agent completed
                    self.registry.update_status(role, AgentStatus.COMPLETED)
                    self.registry.update_progress(role, 100)
                    self._emit("completed", role)
                    completed.append(role)
                else:
                    # Update iteration count based on output patterns
                    # Look for iteration markers in output
                    try:
                        output = self.controller.capture_output(role.value, lines=50)
                        if output:
                            # Simple heuristic: count prompts/responses
                            iteration_markers = output.count("Human:") + output.count("Assistant:")
                            if iteration_markers > 0:
                                self.registry.update_progress(
                                    role,
                                    iteration_count=state.iteration_count + 1,
                                    progress_percent=min(95, state.iteration_count * 2)
                                )
                    except Exception as e:
                        logger.debug(f"Could not update progress for {role.display_name}: {e}")

            except AgentTimeoutError as e:
                # Agent timed out - mark as failed
                logger.error(f"Agent timeout: {e}")
                self._emit("failed", role, str(e))
                # Registry already updated in check_agent

            except OutputCollectionError as e:
                # Collection error - log but continue
                logger.warning(f"Collection error: {e}")
                # Don't fail the agent yet - might be transient

            except Exception as e:
                # Unexpected error - mark agent as failed
                logger.error(f"Unexpected error polling {role.display_name}: {e}", exc_info=True)
                self.registry.update_status(
                    role,
                    AgentStatus.FAILED,
                    error_message=f"Polling error: {e}",
                )
                self._emit("failed", role, str(e))

        return completed

    async def poll_async(self, timeout: Optional[float] = None) -> bool:
        """Poll agents asynchronously until all complete or timeout.

        Args:
            timeout: Maximum time to poll (None for no timeout)

        Returns:
            True if all agents completed, False if timeout
        """
        self._running = True
        start_time = time.time()

        while self._running:
            # Check timeout
            if timeout and (time.time() - start_time) > timeout:
                return False

            # Poll all active agents
            completed = self.poll_once()

            # Check if all done
            if self.registry.all_completed():
                return True

            # Check for failures
            if self.registry.any_failed():
                return False

            # Wait before next poll
            await asyncio.sleep(self.poll_interval)

        return False

    def poll_blocking(self, timeout: Optional[float] = None) -> bool:
        """Poll agents in blocking mode until all complete or timeout.

        Args:
            timeout: Maximum time to poll (None for no timeout)

        Returns:
            True if all agents completed, False if timeout
        """
        self._running = True
        start_time = time.time()

        while self._running:
            # Check timeout
            if timeout and (time.time() - start_time) > timeout:
                return False

            # Poll all active agents
            completed = self.poll_once()

            # Check if all done
            if self.registry.all_completed():
                return True

            # Check for failures
            if self.registry.any_failed():
                return False

            # Wait before next poll
            time.sleep(self.poll_interval)

        return False

    def stop(self) -> None:
        """Stop polling."""
        self._running = False

    def wait_for_agent(self, role: AgentRole, timeout: Optional[float] = None) -> bool:
        """Wait for a specific agent to complete.

        Args:
            role: Agent role to wait for
            timeout: Maximum time to wait

        Returns:
            True if agent completed, False if timeout or failure
        """
        start_time = time.time()

        while True:
            # Check timeout
            if timeout and (time.time() - start_time) > timeout:
                return False

            # Check agent status
            state = self.registry.get(role)
            if state and state.status == AgentStatus.COMPLETED:
                return True
            if state and state.status == AgentStatus.FAILED:
                return False

            # Poll the agent
            signal = self.check_agent(role)
            if signal:
                self.registry.update_status(role, AgentStatus.COMPLETED)
                self.registry.update_progress(role, 100)
                self._emit("completed", role)
                return True

            time.sleep(self.poll_interval)

    def get_agent_output(self, role: AgentRole) -> str:
        """Get the full output log for an agent.

        Args:
            role: Agent role

        Returns:
            Output text
        """
        log_file = self.config.config_dir / "logs" / f"{role.value}.log"
        if log_file.exists():
            return log_file.read_text()
        return ""
