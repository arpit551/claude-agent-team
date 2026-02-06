"""Enhanced progress tracking and visualization."""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
    TimeElapsedColumn,
)
from rich.table import Table
from rich.text import Text

from cat.agent.models import AgentRole, AgentStatus
from cat.agent.registry import AgentRegistry

logger = logging.getLogger(__name__)


@dataclass
class AgentProgress:
    """Progress information for a single agent."""

    role: AgentRole
    status: AgentStatus
    progress_percent: int = 0
    iteration_count: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    last_output: str = ""
    error: Optional[str] = None

    @property
    def duration(self) -> Optional[timedelta]:
        """Get duration since start."""
        if not self.started_at:
            return None
        end = self.completed_at or datetime.now()
        return end - self.started_at

    @property
    def duration_str(self) -> str:
        """Get formatted duration string."""
        if not self.duration:
            return "-"

        total_seconds = int(self.duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"

    @property
    def status_symbol(self) -> str:
        """Get status symbol."""
        return {
            AgentStatus.IDLE: "○",
            AgentStatus.STARTING: "◐",
            AgentStatus.RUNNING: "●",
            AgentStatus.WAITING: "◑",
            AgentStatus.COMPLETED: "✓",
            AgentStatus.FAILED: "✗",
            AgentStatus.ERROR: "⚠",
        }.get(self.status, "?")

    @property
    def status_color(self) -> str:
        """Get status color."""
        return {
            AgentStatus.IDLE: "dim",
            AgentStatus.STARTING: "yellow",
            AgentStatus.RUNNING: "blue",
            AgentStatus.WAITING: "yellow",
            AgentStatus.COMPLETED: "green",
            AgentStatus.FAILED: "red",
            AgentStatus.ERROR: "red",
        }.get(self.status, "white")


class ProgressTracker:
    """Track and visualize workflow progress."""

    def __init__(
        self,
        registry: AgentRegistry,
        console: Optional[Console] = None,
    ):
        """Initialize progress tracker.

        Args:
            registry: Agent registry
            console: Rich console for output
        """
        self.registry = registry
        self.console = console or Console()

        # Progress tracking
        self._agent_progress: dict[AgentRole, AgentProgress] = {}

    def update_agent(
        self,
        role: AgentRole,
        status: Optional[AgentStatus] = None,
        progress: Optional[int] = None,
        iteration: Optional[int] = None,
        output: Optional[str] = None,
        error: Optional[str] = None,
    ) -> None:
        """Update agent progress.

        Args:
            role: Agent role
            status: New status
            progress: Progress percentage (0-100)
            iteration: Iteration count
            output: Latest output snippet
            error: Error message
        """
        if role not in self._agent_progress:
            self._agent_progress[role] = AgentProgress(
                role=role,
                status=AgentStatus.IDLE,
            )

        agent = self._agent_progress[role]

        if status is not None:
            old_status = agent.status
            agent.status = status

            # Track timing
            if status == AgentStatus.RUNNING and old_status != AgentStatus.RUNNING:
                agent.started_at = datetime.now()
            elif status == AgentStatus.COMPLETED:
                agent.completed_at = datetime.now()

        if progress is not None:
            agent.progress_percent = min(100, max(0, progress))

        if iteration is not None:
            agent.iteration_count = iteration

        if output is not None:
            agent.last_output = output[:100]  # Truncate

        if error is not None:
            agent.error = error

    def get_agent_progress(self, role: AgentRole) -> Optional[AgentProgress]:
        """Get progress for an agent.

        Args:
            role: Agent role

        Returns:
            Agent progress or None
        """
        return self._agent_progress.get(role)

    def get_all_progress(self) -> dict[AgentRole, AgentProgress]:
        """Get progress for all agents.

        Returns:
            Dictionary of role to progress
        """
        return self._agent_progress.copy()

    def render_table(self) -> Table:
        """Render progress as a table.

        Returns:
            Rich table
        """
        table = Table(title="Agent Progress", show_header=True, expand=True)
        table.add_column("Agent", style="cyan", no_wrap=True)
        table.add_column("Status", style="bold")
        table.add_column("Progress", justify="right")
        table.add_column("Iterations", justify="right")
        table.add_column("Duration", justify="right")
        table.add_column("Output", style="dim")

        for state in sorted(
            self._agent_progress.values(),
            key=lambda s: s.role.value,
        ):
            # Status with symbol
            status_text = Text()
            status_text.append(f"{state.status_symbol} ", style=state.status_color)
            status_text.append(state.status.value, style=state.status_color)

            # Progress bar
            if state.status in (AgentStatus.RUNNING, AgentStatus.COMPLETED):
                progress_bar = f"{'█' * (state.progress_percent // 10)}"
                progress_bar += f"{'░' * (10 - state.progress_percent // 10)}"
                progress_text = f"{progress_bar} {state.progress_percent}%"
            else:
                progress_text = "-"

            # Output snippet
            output_text = state.last_output if state.last_output else "-"
            if state.error:
                output_text = f"❌ {state.error[:50]}"

            table.add_row(
                state.role.display_name,
                status_text,
                progress_text,
                str(state.iteration_count) if state.iteration_count > 0 else "-",
                state.duration_str,
                output_text,
            )

        return table

    def render_summary(self) -> Panel:
        """Render summary panel.

        Returns:
            Rich panel with summary
        """
        total = len(self._agent_progress)
        completed = sum(
            1 for a in self._agent_progress.values() if a.status == AgentStatus.COMPLETED
        )
        failed = sum(
            1 for a in self._agent_progress.values() if a.status == AgentStatus.FAILED
        )
        running = sum(
            1 for a in self._agent_progress.values() if a.status == AgentStatus.RUNNING
        )

        summary = Text()
        summary.append(f"Total: {total}  ", style="bold")
        summary.append(f"✓ {completed}  ", style="green")
        summary.append(f"● {running}  ", style="blue")
        summary.append(f"✗ {failed}", style="red")

        return Panel(summary, title="Summary", border_style="blue")

    def render_full(self) -> Group:
        """Render full progress display.

        Returns:
            Rich Group with all elements
        """
        return Group(
            self.render_summary(),
            self.render_table(),
        )

    def print_progress(self) -> None:
        """Print current progress to console."""
        self.console.print(self.render_full())

    def sync_from_registry(self) -> None:
        """Sync progress from registry.

        Updates internal state from the agent registry.
        """
        for state in self.registry:
            self.update_agent(
                role=state.role,
                status=state.status,
                progress=state.progress_percent,
                iteration=state.iteration_count,
                output=state.last_output if hasattr(state, "last_output") else None,
                error=state.error if hasattr(state, "error") else None,
            )


class LiveProgressDisplay:
    """Live updating progress display."""

    def __init__(
        self,
        tracker: ProgressTracker,
        console: Optional[Console] = None,
    ):
        """Initialize live display.

        Args:
            tracker: Progress tracker
            console: Rich console
        """
        self.tracker = tracker
        self.console = console or Console()
        self._live: Optional[Live] = None

    def __enter__(self) -> "LiveProgressDisplay":
        """Enter context - start live display."""
        self._live = Live(
            self.tracker.render_full(),
            console=self.console,
            refresh_per_second=2,
        )
        self._live.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context - stop live display."""
        if self._live:
            self._live.__exit__(exc_type, exc_val, exc_tb)

    def update(self) -> None:
        """Update the live display."""
        if self._live:
            self._live.update(self.tracker.render_full())


def create_rich_progress() -> Progress:
    """Create a rich progress bar.

    Returns:
        Configured Progress instance
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        expand=True,
    )
