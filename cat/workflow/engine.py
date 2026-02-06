"""Workflow engine for orchestrating agent execution."""

import json
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
from cat.agent.tmux import TmuxController
from cat.interactive.config import ProjectConfig
from cat.workflow.spawner import AgentSpawner
from cat.workflow.collector import OutputCollector


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
    ):
        self.config = config
        self.max_iterations_per_agent = max_iterations
        self.console = console or Console()

        # State file paths
        self.state_file = config.config_dir / "state.json"
        self.registry_file = config.config_dir / "agents.json"

        # Initialize components
        self.tmux = TmuxController()
        self.registry = AgentRegistry(state_file=self.registry_file)
        self.spawner = AgentSpawner(config, self.tmux, self.registry)
        self.collector = OutputCollector(config, self.tmux, self.registry)

        # Workflow state
        self.state = WorkflowState(max_iterations=max_iterations * len(config.enabled_agents))

        # Register callbacks
        self.collector.on_completed(self._on_agent_completed)
        self.collector.on_failed(self._on_agent_failed)

    def _on_agent_completed(self, role: AgentRole) -> None:
        """Handle agent completion."""
        self.console.print(f"[green]✓[/green] {role.display_name} completed")
        self._save_state()

        # Try to spawn next ready agent
        next_role = self.spawner.spawn_next_ready()
        if next_role:
            self.console.print(f"[blue]→[/blue] Starting {next_role.display_name}")

    def _on_agent_failed(self, role: AgentRole, error: str) -> None:
        """Handle agent failure."""
        self.console.print(f"[red]✗[/red] {role.display_name} failed: {error}")
        self._save_state()

    def _save_state(self) -> None:
        """Save workflow and registry state."""
        # Save workflow state
        state_data = {
            "workflow": self.state.to_dict(),
            "agents": self.registry.to_dict(),
            "saved_at": datetime.now().isoformat(),
        }
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, "w") as f:
            json.dump(state_data, f, indent=2)

        # Save registry
        self.registry.save()

    def _load_state(self) -> bool:
        """Load saved state for resumption.

        Returns:
            True if state was loaded
        """
        if not self.state_file.exists():
            return False

        with open(self.state_file) as f:
            data = json.load(f)

        self.state = WorkflowState.from_dict(data.get("workflow", {}))
        self.registry.load()
        return True

    def run(self, resume: bool = False) -> bool:
        """Run the workflow.

        Args:
            resume: Whether to resume from saved state

        Returns:
            True if workflow completed successfully
        """
        # Load state if resuming
        if resume and self._load_state():
            self.console.print("[yellow]Resuming from saved state...[/yellow]")
        else:
            # Initialize fresh state
            self.registry.reset()
            for agent in self.config.enabled_agents:
                self.registry.register(agent.role)

        self.state.started_at = datetime.now()
        self.state.phase = "running"
        self._save_state()

        try:
            # Create tmux session
            self.tmux.create_session()

            # Start with live progress display
            return self._run_with_progress()

        except KeyboardInterrupt:
            self.console.print("\n[yellow]Interrupted - state saved[/yellow]")
            self._save_state()
            return False

        except Exception as e:
            self.state.error = str(e)
            self.state.phase = "failed"
            self._save_state()
            self.console.print(f"[red]Error: {e}[/red]")
            return False

    def _run_with_progress(self) -> bool:
        """Run workflow with live progress display."""
        # Spawn initial agents (those with no dependencies)
        ready = self.spawner.get_ready_agents()
        for agent_config in ready:
            if self.spawner.spawn_agent(agent_config):
                self.console.print(f"[blue]→[/blue] Started {agent_config.role.display_name}")

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

                # Check if done
                if self.registry.all_completed():
                    progress.update(task, completed=len(self.config.enabled_agents))
                    self.state.phase = "completed"
                    self.state.completed_at = datetime.now()
                    self._save_state()
                    self.console.print("\n[green]✓ Workflow completed![/green]")
                    return True

                # Check for failures
                if self.registry.any_failed():
                    self.state.phase = "failed"
                    self._save_state()
                    self.console.print("\n[red]✗ Workflow failed[/red]")
                    return False

                # Update description with current agent
                active = self.registry.active_agents
                if active:
                    desc = f"Running: {active[0].role.display_name}"
                    if len(active) > 1:
                        desc += f" (+{len(active)-1} more)"
                    progress.update(task, description=desc)

                poll_count += 1
                self.state.total_iterations = poll_count
                time.sleep(2)

        # Timeout
        self.state.phase = "timeout"
        self.state.error = "Maximum iterations reached"
        self._save_state()
        self.console.print("\n[yellow]Timeout - maximum iterations reached[/yellow]")
        return False

    def status(self) -> None:
        """Print current workflow status."""
        # Load latest state
        self._load_state()

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
        self.collector.stop()
        self._save_state()

    def cleanup(self) -> None:
        """Clean up tmux session."""
        self.tmux.kill_session()
