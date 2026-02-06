"""Agent data models for Claude Agent Teams."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class AgentRole(str, Enum):
    """Available agent roles."""

    RESEARCHER = "researcher"
    MANAGER = "manager"
    PRODUCT_MANAGER = "product_manager"
    ARCHITECT = "architect"
    DEVELOPER = "developer"
    TESTER = "tester"
    REVIEWER = "reviewer"

    @property
    def display_name(self) -> str:
        """Get display name for role."""
        return self.value.replace("_", " ").title()

    @property
    def default_model(self) -> "ModelType":
        """Get default model for this role."""
        # Opus for complex reasoning roles
        if self in (
            AgentRole.RESEARCHER,
            AgentRole.MANAGER,
            AgentRole.PRODUCT_MANAGER,
            AgentRole.ARCHITECT,
        ):
            return ModelType.OPUS
        # Sonnet for implementation roles
        return ModelType.SONNET

    @property
    def description(self) -> str:
        """Get description of what this role does."""
        descriptions = {
            AgentRole.RESEARCHER: "Technical research and evaluation",
            AgentRole.MANAGER: "Task coordination and planning",
            AgentRole.PRODUCT_MANAGER: "Requirements and user stories",
            AgentRole.ARCHITECT: "System design and interfaces",
            AgentRole.DEVELOPER: "Code implementation",
            AgentRole.TESTER: "Test creation and QA",
            AgentRole.REVIEWER: "Code review and security",
        }
        return descriptions.get(self, "")


class AgentStatus(str, Enum):
    """Agent execution status."""

    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    WAITING = "waiting"  # blocked by dependencies
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

    @property
    def icon(self) -> str:
        """Get status icon."""
        icons = {
            AgentStatus.IDLE: "⏸",
            AgentStatus.STARTING: "🔄",
            AgentStatus.RUNNING: "▶",
            AgentStatus.WAITING: "⏳",
            AgentStatus.COMPLETED: "✅",
            AgentStatus.FAILED: "❌",
            AgentStatus.PAUSED: "⏸",
        }
        return icons.get(self, "❓")

    @property
    def color(self) -> str:
        """Get status color for display."""
        colors = {
            AgentStatus.IDLE: "dim",
            AgentStatus.STARTING: "yellow",
            AgentStatus.RUNNING: "blue",
            AgentStatus.WAITING: "yellow",
            AgentStatus.COMPLETED: "green",
            AgentStatus.FAILED: "red",
            AgentStatus.PAUSED: "yellow",
        }
        return colors.get(self, "white")


class ModelType(str, Enum):
    """Claude model type."""

    OPUS = "opus"
    SONNET = "sonnet"

    @property
    def full_name(self) -> str:
        """Get full model name for API."""
        names = {
            ModelType.OPUS: "claude-opus-4-5-20251101",
            ModelType.SONNET: "claude-sonnet-4-5-20250929",
        }
        return names.get(self, "claude-sonnet-4-5-20250929")


@dataclass
class AgentConfig:
    """Configuration for a single agent."""

    role: AgentRole
    model: ModelType = ModelType.SONNET
    enabled: bool = True
    depends_on: list[str] = field(default_factory=list)
    max_iterations: int = 40
    file_ownership: list[str] = field(default_factory=list)
    custom_prompt: Optional[str] = None

    def __post_init__(self):
        """Set default model based on role if not specified."""
        if self.model is None:
            self.model = self.role.default_model

    def to_dict(self) -> dict:
        """Convert to dictionary for YAML serialization."""
        return {
            "role": self.role.value,
            "model": self.model.value,
            "enabled": self.enabled,
            "depends_on": self.depends_on,
            "max_iterations": self.max_iterations,
            "file_ownership": self.file_ownership,
            "custom_prompt": self.custom_prompt,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AgentConfig":
        """Create from dictionary."""
        return cls(
            role=AgentRole(data["role"]),
            model=ModelType(data.get("model", "sonnet")),
            enabled=data.get("enabled", True),
            depends_on=data.get("depends_on", []),
            max_iterations=data.get("max_iterations", 40),
            file_ownership=data.get("file_ownership", []),
            custom_prompt=data.get("custom_prompt"),
        )


@dataclass
class AgentState:
    """Runtime state of a single agent."""

    role: AgentRole
    status: AgentStatus = AgentStatus.IDLE
    current_task: Optional[str] = None
    iteration_count: int = 0
    progress_percent: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    output_file: Optional[Path] = None
    error_message: Optional[str] = None
    last_output: Optional[str] = None

    @property
    def is_active(self) -> bool:
        """Check if agent is currently active."""
        return self.status in (AgentStatus.RUNNING, AgentStatus.STARTING)

    @property
    def is_done(self) -> bool:
        """Check if agent has finished (success or failure)."""
        return self.status in (AgentStatus.COMPLETED, AgentStatus.FAILED)

    @property
    def duration_seconds(self) -> Optional[int]:
        """Get duration in seconds."""
        if not self.started_at:
            return None
        end = self.completed_at or datetime.now()
        return int((end - self.started_at).total_seconds())

    @property
    def duration_display(self) -> str:
        """Get human-readable duration."""
        seconds = self.duration_seconds
        if seconds is None:
            return "-"
        if seconds < 60:
            return f"{seconds}s"
        minutes = seconds // 60
        remaining = seconds % 60
        return f"{minutes}m {remaining}s"

    @property
    def display_status(self) -> str:
        """Get display string with icon."""
        return f"{self.status.icon} {self.status.value.upper()}"

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "role": self.role.value,
            "status": self.status.value,
            "current_task": self.current_task,
            "iteration_count": self.iteration_count,
            "progress_percent": self.progress_percent,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "output_file": str(self.output_file) if self.output_file else None,
            "error_message": self.error_message,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AgentState":
        """Create from dictionary."""
        return cls(
            role=AgentRole(data["role"]),
            status=AgentStatus(data.get("status", "idle")),
            current_task=data.get("current_task"),
            iteration_count=data.get("iteration_count", 0),
            progress_percent=data.get("progress_percent", 0),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            output_file=Path(data["output_file"]) if data.get("output_file") else None,
            error_message=data.get("error_message"),
        )


# Default agent workflow dependencies
DEFAULT_DEPENDENCIES = {
    AgentRole.RESEARCHER: [],
    AgentRole.MANAGER: [AgentRole.RESEARCHER.value],
    AgentRole.PRODUCT_MANAGER: [],
    AgentRole.ARCHITECT: [AgentRole.MANAGER.value],
    AgentRole.DEVELOPER: [AgentRole.ARCHITECT.value],
    AgentRole.TESTER: [AgentRole.DEVELOPER.value],
    AgentRole.REVIEWER: [AgentRole.TESTER.value],
}


def get_default_agent_configs() -> dict[str, AgentConfig]:
    """Get default agent configurations for a full development team."""
    configs = {}
    for role in AgentRole:
        configs[role.value] = AgentConfig(
            role=role,
            model=role.default_model,
            enabled=True,
            depends_on=DEFAULT_DEPENDENCIES.get(role, []),
            max_iterations=40,
        )
    return configs
