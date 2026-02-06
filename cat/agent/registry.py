"""Agent registry for tracking spawned agents."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from cat.agent.models import AgentRole, AgentState, AgentStatus


@dataclass
class AgentRegistry:
    """Registry for tracking all spawned agents and their states."""

    agents: dict[str, AgentState] = field(default_factory=dict)
    state_file: Optional[Path] = None
    _dirty: bool = False

    def __post_init__(self):
        """Initialize the registry."""
        if self.state_file and self.state_file.exists():
            self.load()

    def register(self, role: AgentRole) -> AgentState:
        """Register a new agent.

        Args:
            role: Agent role

        Returns:
            New AgentState
        """
        state = AgentState(role=role, status=AgentStatus.IDLE)
        self.agents[role.value] = state
        self._dirty = True
        return state

    def get(self, role: AgentRole) -> Optional[AgentState]:
        """Get agent state by role.

        Args:
            role: Agent role

        Returns:
            AgentState or None
        """
        return self.agents.get(role.value)

    def get_or_register(self, role: AgentRole) -> AgentState:
        """Get or register an agent.

        Args:
            role: Agent role

        Returns:
            AgentState
        """
        state = self.get(role)
        if state is None:
            state = self.register(role)
        return state

    def update_status(
        self,
        role: AgentRole,
        status: AgentStatus,
        current_task: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> AgentState:
        """Update agent status.

        Args:
            role: Agent role
            status: New status
            current_task: Current task description
            error_message: Error message if failed

        Returns:
            Updated AgentState
        """
        state = self.get_or_register(role)
        state.status = status
        state.current_task = current_task
        state.error_message = error_message

        # Track timing
        if status == AgentStatus.STARTING:
            state.started_at = datetime.now()
        elif status in (AgentStatus.COMPLETED, AgentStatus.FAILED):
            state.completed_at = datetime.now()

        self._dirty = True
        return state

    def update_progress(
        self,
        role: AgentRole,
        progress_percent: int,
        iteration_count: Optional[int] = None,
    ) -> AgentState:
        """Update agent progress.

        Args:
            role: Agent role
            progress_percent: Progress percentage (0-100)
            iteration_count: Current iteration count

        Returns:
            Updated AgentState
        """
        state = self.get_or_register(role)
        state.progress_percent = min(100, max(0, progress_percent))
        if iteration_count is not None:
            state.iteration_count = iteration_count
        self._dirty = True
        return state

    def set_tmux_pane(self, role: AgentRole, pane: str) -> AgentState:
        """Set tmux pane for agent.

        Args:
            role: Agent role
            pane: Tmux pane target string

        Returns:
            Updated AgentState
        """
        state = self.get_or_register(role)
        state.tmux_pane = pane
        self._dirty = True
        return state

    def set_output_file(self, role: AgentRole, path: Path) -> AgentState:
        """Set output file for agent.

        Args:
            role: Agent role
            path: Output file path

        Returns:
            Updated AgentState
        """
        state = self.get_or_register(role)
        state.output_file = path
        self._dirty = True
        return state

    def set_last_output(self, role: AgentRole, output: str) -> AgentState:
        """Set last captured output for agent.

        Args:
            role: Agent role
            output: Output text

        Returns:
            Updated AgentState
        """
        state = self.get_or_register(role)
        state.last_output = output
        self._dirty = True
        return state

    @property
    def active_agents(self) -> list[AgentState]:
        """Get list of currently active agents."""
        return [
            state for state in self.agents.values()
            if state.is_active
        ]

    @property
    def completed_agents(self) -> list[AgentState]:
        """Get list of completed agents."""
        return [
            state for state in self.agents.values()
            if state.status == AgentStatus.COMPLETED
        ]

    @property
    def failed_agents(self) -> list[AgentState]:
        """Get list of failed agents."""
        return [
            state for state in self.agents.values()
            if state.status == AgentStatus.FAILED
        ]

    @property
    def waiting_agents(self) -> list[AgentState]:
        """Get list of agents waiting on dependencies."""
        return [
            state for state in self.agents.values()
            if state.status == AgentStatus.WAITING
        ]

    @property
    def total_progress(self) -> int:
        """Calculate overall progress percentage."""
        if not self.agents:
            return 0
        total = sum(state.progress_percent for state in self.agents.values())
        return int(total / len(self.agents))

    def all_completed(self) -> bool:
        """Check if all agents have completed."""
        return all(
            state.status == AgentStatus.COMPLETED
            for state in self.agents.values()
        )

    def any_failed(self) -> bool:
        """Check if any agent has failed."""
        return any(
            state.status == AgentStatus.FAILED
            for state in self.agents.values()
        )

    def save(self, path: Optional[Path] = None) -> None:
        """Save registry state to file.

        Args:
            path: File path (uses self.state_file if not provided)
        """
        save_path = path or self.state_file
        if not save_path:
            return

        save_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "agents": {
                role: state.to_dict()
                for role, state in self.agents.items()
            },
            "saved_at": datetime.now().isoformat(),
        }

        with open(save_path, "w") as f:
            json.dump(data, f, indent=2)

        self._dirty = False

    def load(self, path: Optional[Path] = None) -> None:
        """Load registry state from file.

        Args:
            path: File path (uses self.state_file if not provided)
        """
        load_path = path or self.state_file
        if not load_path or not load_path.exists():
            return

        with open(load_path) as f:
            data = json.load(f)

        self.agents = {
            role: AgentState.from_dict(state_data)
            for role, state_data in data.get("agents", {}).items()
        }
        self._dirty = False

    def save_if_dirty(self) -> None:
        """Save if there are unsaved changes."""
        if self._dirty:
            self.save()

    def reset(self) -> None:
        """Reset all agents to idle state."""
        for state in self.agents.values():
            state.status = AgentStatus.IDLE
            state.tmux_pane = None
            state.current_task = None
            state.iteration_count = 0
            state.progress_percent = 0
            state.started_at = None
            state.completed_at = None
            state.error_message = None
            state.last_output = None
        self._dirty = True

    def to_dict(self) -> dict:
        """Convert registry to dictionary."""
        return {
            role: state.to_dict()
            for role, state in self.agents.items()
        }

    def __len__(self) -> int:
        return len(self.agents)

    def __iter__(self):
        return iter(self.agents.values())


def get_registry(state_file: Optional[Path] = None) -> AgentRegistry:
    """Get an AgentRegistry instance.

    Args:
        state_file: Path to state file for persistence

    Returns:
        AgentRegistry instance
    """
    return AgentRegistry(state_file=state_file)
