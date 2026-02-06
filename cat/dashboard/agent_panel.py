"""Agent panel widget for the dashboard."""

from typing import Optional

from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical
from textual.reactive import reactive
from textual.widgets import Static

from cat.agent.models import AgentRole, AgentState, AgentStatus


class AgentCard(Static):
    """A card displaying a single agent's status."""

    DEFAULT_CSS = """
    AgentCard {
        width: 100%;
        height: auto;
        min-height: 4;
        padding: 1;
        margin-bottom: 1;
        border: solid $secondary;
        background: $surface;
    }

    AgentCard.selected {
        border: solid $primary;
        background: $primary-darken-2;
    }

    AgentCard.idle {
        border-left: thick $text-muted;
    }

    AgentCard.starting {
        border-left: thick $warning;
    }

    AgentCard.running {
        border-left: thick $primary;
    }

    AgentCard.waiting {
        border-left: thick $warning;
    }

    AgentCard.completed {
        border-left: thick $success;
    }

    AgentCard.failed {
        border-left: thick $error;
    }

    AgentCard .agent-name {
        text-style: bold;
    }

    AgentCard .agent-model {
        color: $text-muted;
    }

    AgentCard .agent-status {
        margin-top: 1;
    }

    AgentCard .agent-task {
        color: $text-muted;
        max-width: 100%;
    }

    AgentCard .agent-progress {
        color: $success;
    }
    """

    selected: reactive[bool] = reactive(False)

    def __init__(
        self,
        state: AgentState,
        model: str = "sonnet",
        selected: bool = False,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.state = state
        self.model = model
        self.selected = selected
        self._update_classes()

    def _update_classes(self) -> None:
        """Update CSS classes based on state."""
        # Remove old status classes
        for status in AgentStatus:
            self.remove_class(status.value)

        # Add current status class
        self.add_class(self.state.status.value)

        # Selected state
        if self.selected:
            self.add_class("selected")
        else:
            self.remove_class("selected")

    def watch_selected(self, selected: bool) -> None:
        """React to selection changes."""
        self._update_classes()
        self.refresh()

    def update_state(self, state: AgentState) -> None:
        """Update the displayed state."""
        self.state = state
        self._update_classes()
        self.refresh()

    def render(self) -> str:
        """Render the agent card."""
        state = self.state
        cursor = "[>]" if self.selected else "[ ]"

        # Status line
        status_str = f"{state.status.icon} {state.status.value.upper()}"

        # Model and iterations
        info = f"{self.model}"
        if state.iteration_count > 0:
            info += f" | {state.iteration_count} iter"
        if state.duration_seconds and state.duration_seconds > 0:
            info += f" | {state.duration_display}"

        # Progress bar for running agents
        progress_bar = ""
        if state.status == AgentStatus.RUNNING and state.progress_percent > 0:
            filled = state.progress_percent // 5
            empty = 20 - filled
            progress_bar = f"\n{'█' * filled}{'░' * empty} {state.progress_percent}%"

        # Current task
        task_str = ""
        if state.current_task:
            task_str = f"\n[dim]{state.current_task[:40]}...[/dim]"

        return f"{cursor} [bold]{state.role.display_name}[/bold] {status_str}\n    [dim]{info}[/dim]{progress_bar}{task_str}"


class AgentPanel(Static):
    """Panel showing all agents and their status."""

    DEFAULT_CSS = """
    AgentPanel {
        width: 100%;
        height: 100%;
        padding: 1;
        border: solid $primary;
    }

    AgentPanel > .panel-title {
        text-align: center;
        text-style: bold;
        padding-bottom: 1;
    }

    AgentPanel > ScrollableContainer {
        height: 100%;
    }
    """

    selected_index: reactive[int] = reactive(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.agents: list[tuple[AgentState, str]] = []  # (state, model)
        self._cards: list[AgentCard] = []

    def compose(self) -> ComposeResult:
        """Create the panel layout."""
        yield Static("AGENTS", classes="panel-title")
        with ScrollableContainer():
            pass  # Cards will be mounted dynamically

    def update_agents(self, agents: list[tuple[AgentState, str]]) -> None:
        """Update the agent list.

        Args:
            agents: List of (AgentState, model) tuples
        """
        self.agents = agents

        # Get container
        container = self.query_one(ScrollableContainer)

        # Remove old cards
        container.remove_children()
        self._cards.clear()

        # Create new cards
        for i, (state, model) in enumerate(agents):
            card = AgentCard(
                state=state,
                model=model,
                selected=(i == self.selected_index),
            )
            self._cards.append(card)
            container.mount(card)

    def watch_selected_index(self, index: int) -> None:
        """React to selection changes."""
        for i, card in enumerate(self._cards):
            card.selected = (i == index)

    def select_next(self) -> None:
        """Select the next agent."""
        if self._cards:
            self.selected_index = (self.selected_index + 1) % len(self._cards)

    def select_previous(self) -> None:
        """Select the previous agent."""
        if self._cards:
            self.selected_index = (self.selected_index - 1) % len(self._cards)

    @property
    def selected_agent(self) -> Optional[AgentState]:
        """Get the currently selected agent state."""
        if self.agents and 0 <= self.selected_index < len(self.agents):
            return self.agents[self.selected_index][0]
        return None

    def refresh_agent(self, role: AgentRole, state: AgentState) -> None:
        """Refresh a specific agent's display.

        Args:
            role: Agent role
            state: New state
        """
        for i, (existing_state, model) in enumerate(self.agents):
            if existing_state.role == role:
                self.agents[i] = (state, model)
                if i < len(self._cards):
                    self._cards[i].update_state(state)
                break
