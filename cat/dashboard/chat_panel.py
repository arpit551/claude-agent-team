"""Chat panel widget for agent interaction."""

from typing import Optional

from textual.app import ComposeResult
from textual.containers import Vertical, ScrollableContainer
from textual.reactive import reactive
from textual.widgets import Static, Input
from textual.message import Message

from cat.agent.models import AgentRole


class ChatMessage(Static):
    """A single chat message."""

    DEFAULT_CSS = """
    ChatMessage {
        width: 100%;
        height: auto;
        padding: 0 1;
        margin-bottom: 1;
    }

    ChatMessage.user {
        background: $primary-darken-3;
    }

    ChatMessage.agent {
        background: $surface;
    }

    ChatMessage .sender {
        text-style: bold;
    }

    ChatMessage .content {
        padding-left: 2;
    }
    """

    def __init__(self, sender: str, content: str, is_user: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.sender = sender
        self.content = content
        self.is_user = is_user
        if is_user:
            self.add_class("user")
        else:
            self.add_class("agent")

    def render(self) -> str:
        """Render the message."""
        sender_color = "cyan" if self.is_user else "green"
        return f"[{sender_color}]{self.sender}:[/{sender_color}] {self.content}"


class ChatPanel(Static):
    """Panel for chatting with agents."""

    DEFAULT_CSS = """
    ChatPanel {
        width: 100%;
        height: auto;
        max-height: 15;
        border-top: solid $secondary;
        padding: 1;
        display: none;
    }

    ChatPanel.visible {
        display: block;
    }

    ChatPanel > .chat-header {
        height: 1;
        padding-bottom: 1;
    }

    ChatPanel > .chat-header .title {
        text-style: bold;
    }

    ChatPanel > .chat-header .hint {
        color: $text-muted;
        dock: right;
    }

    ChatPanel > ScrollableContainer {
        height: 8;
        border: solid $secondary;
        background: $surface;
    }

    ChatPanel > Input {
        margin-top: 1;
    }
    """

    class MessageSubmitted(Message):
        """Message submitted event."""

        def __init__(self, role: AgentRole, message: str):
            super().__init__()
            self.role = role
            self.message = message

    visible: reactive[bool] = reactive(False)
    current_agent: reactive[Optional[AgentRole]] = reactive(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.messages: list[tuple[str, str, bool]] = []  # (sender, content, is_user)

    def compose(self) -> ComposeResult:
        """Create the panel layout."""
        with Vertical(classes="chat-header"):
            yield Static("CHAT", classes="title")
            yield Static("[c] toggle", classes="hint")

        with ScrollableContainer(id="chat-messages"):
            pass  # Messages mounted dynamically

        yield Input(placeholder="Type message and press Enter...")

    def on_mount(self) -> None:
        """Initialize the panel."""
        self._update_visibility()

    def watch_visible(self, visible: bool) -> None:
        """React to visibility changes."""
        self._update_visibility()

    def watch_current_agent(self, agent: Optional[AgentRole]) -> None:
        """React to agent selection changes."""
        self._update_header()
        self._clear_messages()

    def _update_visibility(self) -> None:
        """Update panel visibility."""
        if self.visible:
            self.add_class("visible")
        else:
            self.remove_class("visible")

    def _update_header(self) -> None:
        """Update the header with current agent."""
        title = self.query_one(".title", Static)
        if self.current_agent:
            title.update(f"CHAT ({self.current_agent.display_name})")
        else:
            title.update("CHAT")

    def _clear_messages(self) -> None:
        """Clear all messages."""
        container = self.query_one("#chat-messages", ScrollableContainer)
        container.remove_children()
        self.messages.clear()

    def add_message(self, sender: str, content: str, is_user: bool = False) -> None:
        """Add a message to the chat.

        Args:
            sender: Message sender name
            content: Message content
            is_user: Whether this is a user message
        """
        self.messages.append((sender, content, is_user))

        container = self.query_one("#chat-messages", ScrollableContainer)
        msg = ChatMessage(sender, content, is_user)
        container.mount(msg)

        # Scroll to bottom
        container.scroll_end(animate=False)

    def add_agent_output(self, output: str) -> None:
        """Add agent output to the chat.

        Args:
            output: Output text
        """
        if self.current_agent:
            # Truncate long output
            if len(output) > 200:
                output = output[:200] + "..."
            self.add_message(self.current_agent.display_name, output, is_user=False)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        message = event.value.strip()
        if not message:
            return

        # Clear input
        event.input.clear()

        if not self.current_agent:
            self.add_message("System", "No agent selected", is_user=False)
            return

        # Add user message
        self.add_message("You", message, is_user=True)

        # Post message event
        self.post_message(self.MessageSubmitted(self.current_agent, message))

    def toggle(self) -> None:
        """Toggle panel visibility."""
        self.visible = not self.visible

    def set_agent(self, role: AgentRole) -> None:
        """Set the current agent for chat.

        Args:
            role: Agent role
        """
        self.current_agent = role
