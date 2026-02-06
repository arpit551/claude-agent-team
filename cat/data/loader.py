"""Data loaders for Claude Code files."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from cat.data.models import Task, TaskFile, TaskStatus, TeamStats, DashboardState


class TaskLoader:
    """Loads tasks from Claude Code's todo files."""

    def __init__(self, todos_path: Optional[Path] = None):
        self.todos_path = todos_path or Path.home() / ".claude" / "todos"

    def load_all(self) -> list[TaskFile]:
        """Load all task files."""
        task_files = []

        if not self.todos_path.exists():
            return task_files

        for file_path in sorted(self.todos_path.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            task_file = self.load_file(file_path)
            if task_file and task_file.tasks:
                task_files.append(task_file)

        return task_files

    def load_file(self, file_path: Path) -> Optional[TaskFile]:
        """Load a single task file."""
        try:
            with open(file_path) as f:
                data = json.load(f)

            if not isinstance(data, list):
                return None

            tasks = []
            for i, task_data in enumerate(data):
                task_id = f"{file_path.stem[:8]}-{i+1}"
                task = Task.from_dict(task_data, task_id, file_path)
                tasks.append(task)

            modified_at = datetime.fromtimestamp(file_path.stat().st_mtime)

            return TaskFile(
                file_path=file_path,
                tasks=tasks,
                modified_at=modified_at,
            )
        except (json.JSONDecodeError, OSError):
            return None

    def load_recent(self, limit: int = 10) -> list[TaskFile]:
        """Load the most recently modified task files."""
        all_files = self.load_all()
        return all_files[:limit]

    def get_active_tasks(self) -> list[Task]:
        """Get all tasks that are currently in progress."""
        tasks = []
        for tf in self.load_all():
            for task in tf.tasks:
                if task.status == TaskStatus.IN_PROGRESS:
                    tasks.append(task)
        return tasks


class StatsLoader:
    """Loads statistics from Claude Code's stats cache."""

    def __init__(self, stats_path: Optional[Path] = None):
        self.stats_path = stats_path or Path.home() / ".claude" / "stats-cache.json"

    def load(self) -> Optional[TeamStats]:
        """Load statistics from cache file."""
        if not self.stats_path.exists():
            return None

        try:
            with open(self.stats_path) as f:
                data = json.load(f)
            return TeamStats.from_dict(data)
        except (json.JSONDecodeError, OSError):
            return None


class DashboardLoader:
    """Loads all data needed for the dashboard."""

    def __init__(
        self,
        todos_path: Optional[Path] = None,
        stats_path: Optional[Path] = None,
    ):
        self.task_loader = TaskLoader(todos_path)
        self.stats_loader = StatsLoader(stats_path)

    def load(self, recent_limit: int = 20) -> DashboardState:
        """Load complete dashboard state."""
        return DashboardState(
            task_files=self.task_loader.load_recent(recent_limit),
            stats=self.stats_loader.load(),
            last_refresh=datetime.now(),
        )

    def refresh(self, state: DashboardState, recent_limit: int = 20) -> DashboardState:
        """Refresh dashboard state while preserving selection."""
        return DashboardState(
            task_files=self.task_loader.load_recent(recent_limit),
            stats=self.stats_loader.load(),
            selected_file_index=state.selected_file_index,
            selected_task_index=state.selected_task_index,
            last_refresh=datetime.now(),
        )
