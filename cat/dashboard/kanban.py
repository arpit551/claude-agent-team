"""Kanban board widget for the dashboard."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Static

from cat.data.models import DashboardState, Task, TaskStatus
from cat.dashboard.task_card import TaskCard


class KanbanColumn(Container):
    """A single column in the Kanban board."""

    DEFAULT_CSS = """
    KanbanColumn {
        width: 1fr;
        height: 100%;
        border: solid $secondary;
        padding: 0 1;
    }

    KanbanColumn > .column-header {
        text-align: center;
        text-style: bold;
        padding: 1;
        background: $surface;
        border-bottom: solid $secondary;
    }

    KanbanColumn > .column-content {
        height: 1fr;
        padding: 1 0;
    }

    KanbanColumn.pending > .column-header {
        color: $warning;
    }

    KanbanColumn.in_progress > .column-header {
        color: $primary;
    }

    KanbanColumn.completed > .column-header {
        color: $success;
    }
    """

    def __init__(
        self,
        title: str,
        status: TaskStatus,
        tasks: list[Task] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.title = title
        self.status = status
        self.tasks = tasks or []
        self.add_class(status.value)

    def compose(self) -> ComposeResult:
        yield Static(self.title, classes="column-header")
        with ScrollableContainer(classes="column-content"):
            for task in self.tasks:
                yield TaskCard(task)

    def update_tasks(self, tasks: list[Task]) -> None:
        """Update the tasks in this column."""
        self.tasks = tasks

        # Update header with count
        header = self.query_one(".column-header", Static)
        icon = {"pending": "📋", "in_progress": "🔄", "completed": "✅"}.get(
            self.status.value, "❓"
        )
        header.update(f"{icon} {self.title} ({len(tasks)})")

        # Replace task cards
        content = self.query_one(".column-content")
        content.remove_children()
        for task in tasks:
            content.mount(TaskCard(task))


class KanbanBoard(Container):
    """Three-column Kanban board showing TODO, IN PROGRESS, and DONE."""

    DEFAULT_CSS = """
    KanbanBoard {
        layout: horizontal;
        height: 100%;
        padding: 1;
    }

    KanbanBoard > .board-header {
        dock: top;
        height: 3;
        text-align: center;
        padding: 1;
        background: $primary;
    }

    KanbanBoard > .board-columns {
        height: 100%;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.pending_tasks: list[Task] = []
        self.in_progress_tasks: list[Task] = []
        self.completed_tasks: list[Task] = []

    def compose(self) -> ComposeResult:
        with Horizontal(classes="board-columns"):
            yield KanbanColumn(
                "TODO",
                TaskStatus.PENDING,
                self.pending_tasks,
                id="col-pending",
            )
            yield KanbanColumn(
                "IN PROGRESS",
                TaskStatus.IN_PROGRESS,
                self.in_progress_tasks,
                id="col-in-progress",
            )
            yield KanbanColumn(
                "DONE",
                TaskStatus.COMPLETED,
                self.completed_tasks,
                id="col-completed",
            )

    def update_tasks(self, state: DashboardState) -> None:
        """Update all columns with new task data."""
        self.pending_tasks = state.pending_tasks
        self.in_progress_tasks = state.in_progress_tasks
        self.completed_tasks = state.completed_tasks

        # Update each column
        try:
            pending_col = self.query_one("#col-pending", KanbanColumn)
            pending_col.update_tasks(self.pending_tasks)

            in_progress_col = self.query_one("#col-in-progress", KanbanColumn)
            in_progress_col.update_tasks(self.in_progress_tasks)

            completed_col = self.query_one("#col-completed", KanbanColumn)
            completed_col.update_tasks(self.completed_tasks)
        except Exception:
            # Columns may not be mounted yet
            pass
