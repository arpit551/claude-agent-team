"""Main Textual application for the dashboard."""

from datetime import datetime

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Footer, Header, Static

from cat.data import TaskLoader, StatsLoader, TaskStatus
from cat.data.loader import DashboardLoader
from cat.data.models import DashboardState
from cat.data.watcher import TaskWatcher
from cat.dashboard.kanban import KanbanBoard
from cat.dashboard.stats_panel import StatsPanel


class DashboardApp(App):
    """Claude Agent Teams Dashboard Application."""

    CSS = """
    Screen {
        layout: grid;
        grid-size: 1;
        grid-rows: auto 1fr auto;
    }

    #header-panel {
        height: 3;
        background: $primary;
        color: $text;
        text-align: center;
        padding: 1;
    }

    #main-content {
        layout: grid;
        grid-size: 1;
        grid-rows: 1fr auto;
    }

    #kanban-container {
        height: 100%;
        padding: 1;
    }

    #stats-container {
        height: auto;
        max-height: 8;
        border-top: solid $primary;
        padding: 1;
    }

    .column {
        width: 1fr;
        height: 100%;
        border: solid $secondary;
        padding: 1;
    }

    .column-header {
        text-align: center;
        text-style: bold;
        padding-bottom: 1;
    }

    .task-card {
        background: $surface;
        border: solid $primary-lighten-2;
        padding: 1;
        margin-bottom: 1;
        height: auto;
    }

    .task-card.pending {
        border-left: thick $warning;
    }

    .task-card.in_progress {
        border-left: thick $primary;
    }

    .task-card.completed {
        border-left: thick $success;
    }

    .task-title {
        text-style: bold;
    }

    .task-status {
        color: $text-muted;
    }

    .progress-bar {
        color: $success;
    }

    #footer-help {
        dock: bottom;
        height: 1;
        background: $surface;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("d", "toggle_dark", "Toggle Dark"),
        Binding("t", "toggle_stats", "Toggle Stats"),
    ]

    show_stats: reactive[bool] = reactive(True)
    state: reactive[DashboardState] = reactive(DashboardState())

    def __init__(self, watch: bool = False):
        super().__init__()
        self.watch_enabled = watch
        self.loader = DashboardLoader()
        self.watcher = None

    def compose(self) -> ComposeResult:
        """Create the dashboard layout."""
        yield Header(show_clock=True)

        with Container(id="main-content"):
            with Container(id="kanban-container"):
                yield KanbanBoard(id="kanban")

            with Container(id="stats-container"):
                yield StatsPanel(id="stats")

        yield Footer()

    def on_mount(self) -> None:
        """Initialize the dashboard."""
        self.title = "Claude Agent Teams"
        self.sub_title = "Dashboard"

        # Load initial data
        self.state = self.loader.load()
        self._update_display()

        # Start file watcher if enabled
        if self.watch_enabled:
            self.watcher = TaskWatcher(callback=self._on_file_change)
            self.watcher.set_loop(self.app._loop)
            self.watcher.start()

    def on_unmount(self) -> None:
        """Cleanup on exit."""
        if self.watcher:
            self.watcher.stop()

    def action_refresh(self) -> None:
        """Refresh the dashboard data."""
        self.state = self.loader.refresh(self.state)
        self._update_display()
        self.notify("Dashboard refreshed")

    def action_toggle_stats(self) -> None:
        """Toggle statistics panel visibility."""
        self.show_stats = not self.show_stats
        stats_container = self.query_one("#stats-container")
        stats_container.display = self.show_stats

    def _on_file_change(self) -> None:
        """Handle file change events from watcher."""
        self.call_from_thread(self.action_refresh)

    def _update_display(self) -> None:
        """Update all display components."""
        kanban = self.query_one("#kanban", KanbanBoard)
        kanban.update_tasks(self.state)

        stats = self.query_one("#stats", StatsPanel)
        stats.update_stats(self.state)
