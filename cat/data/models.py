"""Data models for tasks, teams, and statistics."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class TaskStatus(str, Enum):
    """Task status values matching Claude Code's format."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


@dataclass
class Task:
    """A task from Claude Code's todo system."""

    id: str
    content: str
    active_form: str
    status: TaskStatus
    file_path: Optional[Path] = None
    assignee: Optional[str] = None
    progress: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: dict, task_id: str, file_path: Optional[Path] = None) -> "Task":
        """Create a Task from Claude Code's JSON format."""
        status = TaskStatus(data.get("status", "pending"))

        # Use actual progress if provided, otherwise use defaults based on status
        if "progress" in data:
            progress = data["progress"]
        else:
            progress = 100 if status == TaskStatus.COMPLETED else (50 if status == TaskStatus.IN_PROGRESS else 0)

        return cls(
            id=task_id,
            content=data.get("content") or "",  # Convert None to empty string
            active_form=data.get("activeForm") or "",  # Convert None to empty string
            status=status,
            file_path=file_path,
            progress=progress,
        )

    @property
    def display_status(self) -> str:
        """Get a display-friendly status string."""
        icons = {
            TaskStatus.PENDING: "📋",
            TaskStatus.IN_PROGRESS: "🔄",
            TaskStatus.COMPLETED: "✅",
        }
        return f"{icons.get(self.status, '❓')} {self.status.value.replace('_', ' ').title()}"

    @property
    def progress_bar(self) -> str:
        """Get a text-based progress bar."""
        filled = self.progress // 10
        empty = 10 - filled
        return f"{'█' * filled}{'░' * empty}"


@dataclass
class TaskFile:
    """A collection of tasks from a single file."""

    file_path: Path
    tasks: list[Task] = field(default_factory=list)
    modified_at: Optional[datetime] = None

    @property
    def pending_count(self) -> int:
        return sum(1 for t in self.tasks if t.status == TaskStatus.PENDING)

    @property
    def in_progress_count(self) -> int:
        return sum(1 for t in self.tasks if t.status == TaskStatus.IN_PROGRESS)

    @property
    def completed_count(self) -> int:
        return sum(1 for t in self.tasks if t.status == TaskStatus.COMPLETED)

    @property
    def progress_percent(self) -> int:
        if not self.tasks:
            return 0
        return int(self.completed_count / len(self.tasks) * 100)


@dataclass
class TeamStats:
    """Statistics from Claude Code's stats-cache.json."""

    total_sessions: int = 0
    total_messages: int = 0
    last_computed_date: Optional[str] = None
    daily_activity: list[dict] = field(default_factory=list)
    model_usage: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "TeamStats":
        """Create TeamStats from Claude Code's stats-cache.json format."""
        return cls(
            total_sessions=data.get("totalSessions", 0),
            total_messages=data.get("totalMessages", 0),
            last_computed_date=data.get("lastComputedDate"),
            daily_activity=data.get("dailyActivity", []),
            model_usage=data.get("modelUsage", {}),
        )

    def get_token_summary(self) -> dict[str, int]:
        """Get total tokens by model."""
        summary = {}
        for model, usage in self.model_usage.items():
            short_name = model.split("-")[1] if "-" in model else model
            total = usage.get("inputTokens", 0) + usage.get("outputTokens", 0)
            summary[short_name] = total
        return summary


@dataclass
class DashboardState:
    """Current state of the dashboard."""

    task_files: list[TaskFile] = field(default_factory=list)
    stats: Optional[TeamStats] = None
    selected_file_index: int = 0
    selected_task_index: int = 0
    last_refresh: Optional[datetime] = None

    @property
    def all_tasks(self) -> list[Task]:
        """Get all tasks across all files."""
        tasks = []
        for tf in self.task_files:
            tasks.extend(tf.tasks)
        return tasks

    @property
    def pending_tasks(self) -> list[Task]:
        return [t for t in self.all_tasks if t.status == TaskStatus.PENDING]

    @property
    def in_progress_tasks(self) -> list[Task]:
        return [t for t in self.all_tasks if t.status == TaskStatus.IN_PROGRESS]

    @property
    def completed_tasks(self) -> list[Task]:
        return [t for t in self.all_tasks if t.status == TaskStatus.COMPLETED]

    @property
    def total_progress(self) -> int:
        """Overall progress percentage."""
        total = len(self.all_tasks)
        if total == 0:
            return 0
        return int(len(self.completed_tasks) / total * 100)
