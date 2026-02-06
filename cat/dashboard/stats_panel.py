"""Statistics panel widget for the dashboard."""

from datetime import datetime
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Static

from cat.data.models import DashboardState


class StatsPanel(Container):
    """Panel showing statistics and progress summary."""

    DEFAULT_CSS = """
    StatsPanel {
        height: auto;
        padding: 1;
        background: $surface;
    }

    StatsPanel > .stats-row {
        height: auto;
        padding: 0 1;
    }

    StatsPanel .stat-item {
        width: 1fr;
        text-align: center;
        padding: 0 2;
    }

    StatsPanel .stat-value {
        text-style: bold;
        color: $primary;
    }

    StatsPanel .stat-label {
        color: $text-muted;
    }

    StatsPanel .progress-summary {
        width: 2fr;
        text-align: center;
    }

    StatsPanel .progress-bar-large {
        color: $success;
    }

    StatsPanel .last-refresh {
        color: $text-muted;
        text-style: dim;
        text-align: right;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.state: Optional[DashboardState] = None

    def compose(self) -> ComposeResult:
        with Horizontal(classes="stats-row"):
            yield Static("", classes="stat-item", id="stat-pending")
            yield Static("", classes="stat-item", id="stat-in-progress")
            yield Static("", classes="stat-item", id="stat-completed")
            yield Static("", classes="stat-item", id="stat-total")
            yield Static("", classes="progress-summary", id="progress-summary")
            yield Static("", classes="last-refresh", id="last-refresh")

    def update_stats(self, state: DashboardState) -> None:
        """Update the statistics display."""
        self.state = state

        pending = len(state.pending_tasks)
        in_progress = len(state.in_progress_tasks)
        completed = len(state.completed_tasks)
        total = len(state.all_tasks)
        progress = state.total_progress

        # Update stat items
        self._update_stat("stat-pending", "📋 TODO", pending, "yellow")
        self._update_stat("stat-in-progress", "🔄 IN PROGRESS", in_progress, "blue")
        self._update_stat("stat-completed", "✅ DONE", completed, "green")
        self._update_stat("stat-total", "📊 TOTAL", total, "white")

        # Update progress bar
        progress_widget = self.query_one("#progress-summary", Static)
        bar = self._render_progress_bar(progress)
        progress_widget.update(f"Progress: {bar} {progress}%")

        # Update last refresh time
        refresh_widget = self.query_one("#last-refresh", Static)
        if state.last_refresh:
            time_str = state.last_refresh.strftime("%H:%M:%S")
            refresh_widget.update(f"Updated: {time_str}")

    def _update_stat(self, widget_id: str, label: str, value: int, color: str) -> None:
        """Update a single stat item."""
        try:
            widget = self.query_one(f"#{widget_id}", Static)
            widget.update(f"{label}: [{color}]{value}[/{color}]")
        except Exception:
            pass

    def _render_progress_bar(self, progress: int) -> str:
        """Render a progress bar."""
        width = 20
        filled = int(progress / 100 * width)
        empty = width - filled
        return f"[green]{'█' * filled}[/green][dim]{'░' * empty}[/dim]"
