"""Output collector for monitoring agent progress."""

import asyncio
import re
import time
from pathlib import Path
from typing import Callable, Optional

from cat.agent.models import AgentRole, AgentStatus
from cat.agent.registry import AgentRegistry
from cat.agent.tmux import TmuxController
from cat.interactive.config import ProjectConfig


class OutputCollector:
    """Collects and monitors agent outputs for completion signals."""

    def __init__(
        self,
        config: ProjectConfig,
        tmux: TmuxController,
        registry: AgentRegistry,
        poll_interval: float = 2.0,
    ):
        self.config = config
        self.tmux = tmux
        self.registry = registry
        self.poll_interval = poll_interval
        self._running = False
        self._callbacks: dict[str, list[Callable]] = {
            "output": [],
            "completed": [],
            "failed": [],
            "progress": [],
        }

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

    def _emit(self, event: str, *args) -> None:
        """Emit an event to all registered callbacks."""
        for callback in self._callbacks.get(event, []):
            try:
                callback(*args)
            except Exception:
                pass  # Don't let callback errors stop collection

    def check_agent(self, role: AgentRole) -> Optional[str]:
        """Check agent output for completion or errors.

        Args:
            role: Agent role to check

        Returns:
            Completion signal if found, None otherwise
        """
        output = self.tmux.capture_output(role.value, lines=100)
        if not output:
            return None

        # Save last output to registry
        self.registry.set_last_output(role, output)

        # Save output to file
        output_file = self.config.config_dir / "logs" / f"{role.value}.log"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "a") as f:
            f.write(output + "\n---\n")

        # Emit output event
        self._emit("output", role, output)

        # Check for completion signal
        completion_signal = self.config.get_completion_signal(role)
        pattern = rf"<promise>{completion_signal}</promise>"

        if re.search(pattern, output, re.IGNORECASE):
            return completion_signal

        # Check for error patterns
        error_patterns = [
            r"Error:",
            r"FATAL:",
            r"failed with exit code",
            r"Permission denied",
        ]
        for pattern in error_patterns:
            if re.search(pattern, output, re.IGNORECASE):
                # Don't immediately fail - could be a recoverable error
                pass

        return None

    def poll_once(self) -> list[AgentRole]:
        """Poll all active agents once.

        Returns:
            List of agents that completed
        """
        completed = []

        for state in self.registry.active_agents:
            role = state.role
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
                output = self.tmux.capture_output(role.value, lines=50)
                if output:
                    # Simple heuristic: count prompts/responses
                    iteration_markers = output.count("Human:") + output.count("Assistant:")
                    if iteration_markers > 0:
                        self.registry.update_progress(
                            role,
                            iteration_count=state.iteration_count + 1,
                            progress_percent=min(95, state.iteration_count * 2)
                        )

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
