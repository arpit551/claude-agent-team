"""Workflow engine for orchestrating agent execution."""

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

from cat.agent.models import AgentRole, AgentStatus
from cat.agent.registry import AgentRegistry
from cat.agent.controller import AgentController
from cat.interactive.config import ProjectConfig
from cat.workflow.spawner import AgentSpawner
from cat.workflow.collector import OutputCollector
from cat.workflow.watcher import OutputWatcher
from cat.workflow.messaging import MessageBus, Message, MessageType
from cat.workflow.progress import ProgressTracker
from cat.workflow.exceptions import (
    WorkflowError,
    WorkflowTimeoutError,
    ConfigurationError,
    StateError,
    AgentTimeoutError,
)

logger = logging.getLogger(__name__)


@dataclass
class WorkflowState:
    """State of workflow execution."""

    phase: str = "initializing"
    total_iterations: int = 0
    max_iterations: int = 200
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "phase": self.phase,
            "total_iterations": self.total_iterations,
            "max_iterations": self.max_iterations,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WorkflowState":
        return cls(
            phase=data.get("phase", "initializing"),
            total_iterations=data.get("total_iterations", 0),
            max_iterations=data.get("max_iterations", 200),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            error=data.get("error"),
        )


class WorkflowEngine:
    """Engine for orchestrating multi-agent workflow execution."""

    def __init__(
        self,
        config: ProjectConfig,
        max_iterations: int = 40,
        console: Optional[Console] = None,
        agent_timeout: int = 3600,
        fail_fast: bool = False,
        watch_enabled: bool = True,
        use_watchdog: bool = True,
    ):
        self.config = config
        self.max_iterations_per_agent = max_iterations
        self.console = console or Console()
        self.agent_timeout = agent_timeout
        self.fail_fast = fail_fast  # If True, stop on first failure
        self.watch_enabled = watch_enabled
        self.use_watchdog = use_watchdog

        # Validate configuration
        self._validate_config()

        # State file paths
        self.state_file = config.config_dir / "state.json"
        self.registry_file = config.config_dir / "agents.json"

        # Initialize components
        try:
            self.controller = AgentController(output_dir=config.config_dir / "output")
            self.registry = AgentRegistry(state_file=self.registry_file)
            self.spawner = AgentSpawner(config, self.controller, self.registry)
            self.collector = OutputCollector(
                config,
                self.controller,
                self.registry,
                agent_timeout=agent_timeout,
            )

            # Initialize new components
            self.message_bus = MessageBus(config.config_dir / "messages")
            self.progress_tracker = ProgressTracker(self.registry, self.console)

            # Initialize file watcher (if enabled)
            self.watcher: Optional[OutputWatcher] = None
            if watch_enabled:
                output_dir = config.config_dir / "output"
                self.watcher = OutputWatcher(
                    output_dir,
                    callback=self._on_output_change,
                    use_watchdog=use_watchdog,
                )

        except Exception as e:
            raise ConfigurationError(f"Failed to initialize workflow: {e}")

        # Workflow state
        self.state = WorkflowState(max_iterations=max_iterations * len(config.enabled_agents))

        # Register callbacks
        self.collector.on_completed(self._on_agent_completed)
        self.collector.on_failed(self._on_agent_failed)
        self.collector.on_timeout(self._on_agent_timeout)

    def _on_output_change(self, file_path: Path) -> None:
        """Handle file output change detected by watcher.

        Args:
            file_path: Path to the changed file
        """
        # Trigger immediate collector poll for the agent whose output changed
        try:
            # Extract agent role from filename (format: role-YYYY-MM-DD.log)
            filename = file_path.stem
            role_name = filename.rsplit("-", 3)[0]  # Remove date parts

            # Find matching agent
            for agent_state in self.registry:
                if agent_state.role.value == role_name:
                    logger.debug(f"Output changed for {agent_state.role.display_name}")
                    # Read and parse output for messages
                    self._parse_output_for_messages(agent_state.role, file_path)
                    break

        except Exception as e:
            logger.warning(f"Failed to handle output change for {file_path}: {e}")

    def _parse_output_for_messages(self, role: AgentRole, output_file: Path) -> None:
        """Parse agent output for inter-agent messages.

        Args:
            role: Agent role that produced the output
            output_file: Path to output file
        """
        if not output_file.exists():
            return

        try:
            with open(output_file) as f:
                # Read only new lines (could track position, but for now read all)
                for line in f:
                    # Look for message markers: [FINDING], [COORD], [PROGRESS], [BLOCKED], etc.
                    line = line.strip()
                    if not line:
                        continue

                    # Parse message format: [TYPE] content
                    for msg_type in MessageType:
                        marker = f"[{msg_type.value}]"
                        if line.startswith(marker):
                            content = line[len(marker):].strip()

                            # Create and send message
                            message = Message(
                                from_role=role,
                                to_role=None,  # Broadcast
                                msg_type=msg_type,
                                content=content,
                                timestamp=datetime.now(),
                            )
                            self.message_bus.send(message)
                            logger.debug(f"Captured message from {role.display_name}: {msg_type.value}")
                            break

        except Exception as e:
            logger.warning(f"Failed to parse output for messages: {e}")

    def _on_agent_completed(self, role: AgentRole) -> None:
        """Handle agent completion."""
        self.console.print(f"[green]✓[/green] {role.display_name} completed")
        self.progress_tracker.update_agent(role, AgentStatus.COMPLETED)
        self._save_state()

        # Try to spawn next ready agent
        next_role = self.spawner.spawn_next_ready()
        if next_role:
            self.console.print(f"[blue]→[/blue] Starting {next_role.display_name}")

    def _on_agent_failed(self, role: AgentRole, error: str) -> None:
        """Handle agent failure."""
        self.console.print(f"[red]✗[/red] {role.display_name} failed: {error}")
        self.progress_tracker.update_agent(role, AgentStatus.FAILED)
        self._save_state()

    def _on_agent_timeout(self, role: AgentRole, timeout_seconds: int) -> None:
        """Handle agent timeout."""
        self.console.print(
            f"[yellow]⏱[/yellow] {role.display_name} timed out after {timeout_seconds}s"
        )
        self.progress_tracker.update_agent(role, AgentStatus.FAILED)
        self._save_state()

    def _validate_config(self) -> None:
        """Validate workflow configuration.

        Raises:
            ConfigurationError: If configuration is invalid
        """
        if not self.config.enabled_agents:
            raise ConfigurationError("No agents configured")

        if not self.config.working_dir.exists():
            raise ConfigurationError(
                f"Working directory does not exist: {self.config.working_dir}"
            )

        # Check for required directories
        required_dirs = [self.config.config_dir]
        for dir_path in required_dirs:
            if not dir_path.parent.exists():
                raise ConfigurationError(
                    f"Parent directory does not exist: {dir_path.parent}"
                )

    def _save_state(self) -> None:
        """Save workflow and registry state.

        Raises:
            StateError: If state cannot be saved
        """
        try:
            # Save workflow state
            state_data = {
                "workflow": self.state.to_dict(),
                "agents": self.registry.to_dict(),
                "saved_at": datetime.now().isoformat(),
            }
            self.state_file.parent.mkdir(parents=True, exist_ok=True)

            # Write atomically (write to temp file, then rename)
            temp_file = self.state_file.with_suffix(".tmp")
            with open(temp_file, "w") as f:
                json.dump(state_data, f, indent=2)
            temp_file.replace(self.state_file)

            # Save registry
            self.registry.save()

            logger.debug(f"State saved to {self.state_file}")

        except Exception as e:
            error = StateError(f"Failed to save state: {e}")
            logger.error(error, exc_info=True)
            raise error

    def _load_state(self) -> bool:
        """Load saved state for resumption.

        Returns:
            True if state was loaded

        Raises:
            StateError: If state file is corrupted
        """
        if not self.state_file.exists():
            return False

        try:
            with open(self.state_file) as f:
                data = json.load(f)

            # Validate data structure
            if "workflow" not in data:
                raise StateError("State file missing 'workflow' key")

            self.state = WorkflowState.from_dict(data["workflow"])
            self.registry.load()

            logger.info(f"State loaded from {self.state_file}")
            return True

        except json.JSONDecodeError as e:
            raise StateError(f"Corrupted state file: {e}")

        except Exception as e:
            raise StateError(f"Failed to load state: {e}")

    def run(self, resume: bool = False) -> bool:
        """Run the workflow.

        Args:
            resume: Whether to resume from saved state

        Returns:
            True if workflow completed successfully
        """
        try:
            # Load state if resuming
            if resume:
                try:
                    if self._load_state():
                        self.console.print("[yellow]Resuming from saved state...[/yellow]")
                    else:
                        self.console.print("[yellow]No saved state found, starting fresh...[/yellow]")
                        resume = False
                except StateError as e:
                    self.console.print(f"[yellow]Warning: {e}[/yellow]")
                    self.console.print("[yellow]Starting fresh workflow...[/yellow]")
                    resume = False

            if not resume:
                # Initialize fresh state
                self.registry.reset()
                for agent in self.config.enabled_agents:
                    self.registry.register(agent.role)

            self.state.started_at = datetime.now()
            self.state.phase = "running"

            try:
                self._save_state()
            except StateError as e:
                self.console.print(f"[yellow]Warning: Could not save state: {e}[/yellow]")
                # Continue anyway - state saving is not critical

            # Start file watcher
            if self.watcher:
                try:
                    self.watcher.start()
                    logger.info("File watcher started")
                except Exception as e:
                    logger.warning(f"Failed to start file watcher: {e}")
                    self.console.print(f"[yellow]Warning: File watching disabled: {e}[/yellow]")

            # Start with live progress display
            return self._run_with_progress()

        except KeyboardInterrupt:
            self.console.print("\n[yellow]Interrupted - saving state...[/yellow]")
            try:
                self._save_state()
                self.console.print("[green]State saved successfully[/green]")
            except StateError as e:
                self.console.print(f"[yellow]Warning: Could not save state: {e}[/yellow]")
            return False

        except WorkflowError as e:
            # Known workflow errors
            self.state.error = str(e)
            self.state.phase = "failed"
            try:
                self._save_state()
            except StateError:
                pass  # Ignore save errors during error handling

            if e.recoverable:
                self.console.print(f"[yellow]Recoverable error: {e}[/yellow]")
                self.console.print("[yellow]You can try resuming with --resume[/yellow]")
            else:
                self.console.print(f"[red]Error: {e}[/red]")

            return False

        except Exception as e:
            # Unexpected errors
            logger.error(f"Unexpected workflow error: {e}", exc_info=True)
            self.state.error = f"Unexpected error: {e}"
            self.state.phase = "failed"

            try:
                self._save_state()
            except StateError:
                pass  # Ignore save errors during error handling

            self.console.print(f"[red]Unexpected error: {e}[/red]")
            self.console.print("[dim]See logs for details[/dim]")
            return False

    def _run_with_progress(self) -> bool:
        """Run workflow with live progress display.

        Implements graceful degradation:
        - Continues on agent failures if fail_fast=False
        - Spawns independent agents even if dependencies fail
        - Reports partial success
        """
        # Spawn initial agents (those with no dependencies)
        ready = self.spawner.get_ready_agents()
        spawn_failures = 0

        for agent_config in ready:
            if self.spawner.spawn_agent(agent_config):
                self.console.print(f"[blue]→[/blue] Started {agent_config.role.display_name}")
            else:
                spawn_failures += 1
                if self.fail_fast:
                    self.console.print("[red]Fail-fast mode: stopping on first failure[/red]")
                    return False

        if spawn_failures == len(ready):
            self.console.print("[red]Failed to spawn any agents[/red]")
            return False

        # Poll until complete
        poll_count = 0
        max_polls = self.state.max_iterations * 30  # ~1 minute per iteration

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console,
        ) as progress:
            task = progress.add_task(
                "Running workflow...",
                total=len(self.config.enabled_agents)
            )

            while poll_count < max_polls:
                # Update progress bar
                completed_count = len(self.registry.completed_agents)
                progress.update(task, completed=completed_count)

                # Poll agents
                newly_completed = self.collector.poll_once()

                # Spawn next ready agents
                for role in newly_completed:
                    next_role = self.spawner.spawn_next_ready()
                    if next_role:
                        self.console.print(f"[blue]→[/blue] Started {next_role.display_name}")

                # Check if done (all completed or no more progress possible)
                if self.registry.all_completed():
                    progress.update(task, completed=len(self.config.enabled_agents))
                    self.state.phase = "completed"
                    self.state.completed_at = datetime.now()
                    try:
                        self._save_state()
                    except StateError:
                        pass  # Ignore save errors on success
                    self.console.print("\n[green]✓ Workflow completed![/green]")
                    return True

                # Check for failures
                if self.registry.any_failed():
                    if self.fail_fast:
                        self.state.phase = "failed"
                        try:
                            self._save_state()
                        except StateError:
                            pass
                        self.console.print("\n[red]✗ Workflow failed (fail-fast mode)[/red]")
                        return False

                    # In graceful mode, check if any progress is still possible
                    active_or_waiting = len(self.registry.active_agents) + len(
                        [s for s in self.registry if s.status == AgentStatus.WAITING]
                    )
                    if active_or_waiting == 0:
                        # No agents running or waiting - check for partial success
                        completed = len(self.registry.completed_agents)
                        failed = len(self.registry.failed_agents)
                        total = len(self.config.enabled_agents)

                        self.state.phase = "partial"
                        try:
                            self._save_state()
                        except StateError:
                            pass

                        self.console.print(
                            f"\n[yellow]Workflow stopped: {completed}/{total} agents completed, "
                            f"{failed} failed[/yellow]"
                        )
                        return completed > 0  # Partial success if any completed

                # Update description with current agent
                active = self.registry.active_agents
                if active:
                    desc = f"Running: {active[0].role.display_name}"
                    if len(active) > 1:
                        desc += f" (+{len(active)-1} more)"
                    progress.update(task, description=desc)

                poll_count += 1
                self.state.total_iterations = poll_count

                # Periodic state save (every 10 iterations)
                if poll_count % 10 == 0:
                    try:
                        self._save_state()
                    except StateError:
                        pass  # Ignore save errors during execution

                time.sleep(2)

        # Timeout
        completed = len(self.registry.completed_agents)
        total = len(self.config.enabled_agents)

        timeout_error = WorkflowTimeoutError(
            poll_count,
            max_polls,
            completed,
            total,
        )

        self.state.phase = "timeout"
        self.state.error = str(timeout_error)

        try:
            self._save_state()
        except StateError:
            pass

        self.console.print(f"\n[yellow]{timeout_error}[/yellow]")
        self.console.print("[yellow]You can resume with --resume[/yellow]")

        return False

    def get_messages(self, role: Optional[AgentRole] = None, limit: int = 50) -> list:
        """Get messages from the message bus.

        Args:
            role: Optional role filter (get messages for this agent)
            limit: Maximum number of messages to return

        Returns:
            List of messages
        """
        return self.message_bus.get_messages(recipient=role, limit=limit)

    def status(self, use_progress_tracker: bool = False) -> None:
        """Print current workflow status.

        Args:
            use_progress_tracker: If True, use enhanced progress tracker display
        """
        # Load latest state
        self._load_state()

        if use_progress_tracker:
            # Use enhanced progress tracker display
            self.progress_tracker.display_summary()
            return

        # Header
        self.console.print()
        info = Table.grid(padding=(0, 2))
        info.add_column(style="bold")
        info.add_column()
        info.add_row("Project:", self.config.name)
        info.add_row("Phase:", self.state.phase)
        info.add_row("Progress:", f"{self.registry.total_progress}%")
        info.add_row("Iterations:", str(self.state.total_iterations))
        if self.state.started_at:
            info.add_row("Started:", self.state.started_at.strftime("%H:%M:%S"))
        self.console.print(Panel(info, title="[bold]Workflow Status[/bold]"))

        # Agents table
        table = Table(title="Agents", show_header=True)
        table.add_column("Role", style="cyan")
        table.add_column("Status")
        table.add_column("Progress")
        table.add_column("Iterations")
        table.add_column("Duration")

        for state in self.registry:
            status_style = {
                AgentStatus.IDLE: "dim",
                AgentStatus.STARTING: "yellow",
                AgentStatus.RUNNING: "blue",
                AgentStatus.WAITING: "yellow",
                AgentStatus.COMPLETED: "green",
                AgentStatus.FAILED: "red",
            }.get(state.status, "white")

            table.add_row(
                state.role.display_name,
                f"[{status_style}]{state.display_status}[/{status_style}]",
                f"{state.progress_percent}%",
                str(state.iteration_count),
                state.duration_display,
            )

        self.console.print()
        self.console.print(table)
        self.console.print()

    def stop(self) -> None:
        """Stop the workflow and cleanup."""
        if self.watcher:
            try:
                self.watcher.stop()
            except Exception as e:
                logger.warning(f"Failed to stop watcher: {e}")
        self.collector.stop()
        self._save_state()

    def cleanup(self) -> None:
        """Clean up agent processes."""
        if self.watcher:
            try:
                self.watcher.stop()
            except Exception as e:
                logger.warning(f"Failed to stop watcher: {e}")
        self.controller.cleanup()
