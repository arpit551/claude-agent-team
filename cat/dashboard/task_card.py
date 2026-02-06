"""Task card widget for the Kanban board."""

from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static

from cat.data.models import Task, TaskStatus


class TaskCard(Container):
    """A card displaying a single task."""

    DEFAULT_CSS = """
    TaskCard {
        height: auto;
        padding: 1;
        margin-bottom: 1;
        background: $surface;
        border: solid $primary-lighten-3;
    }

    TaskCard:hover {
        background: $surface-lighten-1;
    }

    TaskCard.pending {
        border-left: thick $warning;
    }

    TaskCard.in_progress {
        border-left: thick $primary;
    }

    TaskCard.completed {
        border-left: thick $success;
    }

    TaskCard > .task-id {
        color: $text-muted;
        text-style: dim;
    }

    TaskCard > .task-content {
        padding: 0 0 1 0;
    }

    TaskCard > .task-active-form {
        color: $primary;
        text-style: italic;
    }

    TaskCard > .task-progress {
        padding-top: 1;
    }

    TaskCard > .task-progress .progress-bar {
        color: $success;
    }

    TaskCard > .task-progress .progress-empty {
        color: $text-muted;
    }
    """

    def __init__(self, task: Task, **kwargs):
        super().__init__(**kwargs)
        self.task = task
        self.add_class(task.status.value)

    def compose(self) -> ComposeResult:
        yield Static(f"#{self.task.id}", classes="task-id")

        # Add null check for content
        content = (self.task.content or "")[:60]
        yield Static(content, classes="task-content")

        # Add null check for active_form
        if self.task.active_form:
            active_form = (self.task.active_form or "")[:50]
            yield Static(active_form, classes="task-active-form")

        if self.task.status == TaskStatus.IN_PROGRESS:
            progress = self._render_progress()
            yield Static(progress, classes="task-progress")

    def _render_progress(self) -> str:
        """Render the progress bar."""
        filled = self.task.progress // 10
        empty = 10 - filled
        bar = f"[green]{'█' * filled}[/green][dim]{'░' * empty}[/dim]"
        return f"{bar} {self.task.progress}%"
