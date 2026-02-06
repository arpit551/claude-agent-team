"""Tmux Agent Manager - Interactive TUI for managing agent sessions."""

from datetime import datetime
from typing import Optional

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.reactive import reactive
from textual.widgets import Header, Footer, Static, Button, Input, ListView, ListItem, Label
from textual.timer import Timer

from cat.agent.tmux import TmuxController


class AgentListItem(ListItem):
    """A list item for an agent."""

    def __init__(self, role: str, model: str, active: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.role = role
        self.model = model
        self.is_active = active


class AgentOutputViewer(ScrollableContainer):
    """Widget to display agent output."""

    DEFAULT_CSS = """
    AgentOutputViewer {
        height: 1fr;
        border: solid $primary;
        padding: 1;
        background: $surface;
    }

    AgentOutputViewer > .output-line {
        color: $text;
    }

    AgentOutputViewer > .output-header {
        color: $primary;
        text-style: bold;
        padding-bottom: 1;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_agent: Optional[str] = None

    def update_output(self, role: str, output: str):
        """Update the output display."""
        self.current_agent = role
        self.remove_children()

        # Add header
        header = Static(
            f"📺 Output from: {role}",
            classes="output-header"
        )
        self.mount(header)

        # Add output lines
        if output:
            for line in output.split('\n'):
                if line.strip():
                    self.mount(Static(line, classes="output-line"))
        else:
            self.mount(Static("(No output yet)", classes="output-line"))


class AgentSidebar(Container):
    """Sidebar showing list of agents."""

    DEFAULT_CSS = """
    AgentSidebar {
        width: 35;
        height: 100%;
        border-right: solid $primary;
        padding: 1;
    }

    AgentSidebar > .sidebar-header {
        text-align: center;
        text-style: bold;
        color: $primary;
        padding-bottom: 1;
    }

    AgentSidebar ListView {
        height: 1fr;
    }

    AgentSidebar ListItem {
        padding: 1;
        margin-bottom: 1;
    }

    AgentSidebar ListItem:hover {
        background: $surface-lighten-1;
    }

    AgentSidebar ListItem.-active {
        background: $primary;
        color: $text;
    }

    AgentSidebar .agent-info {
        padding-left: 2;
    }

    AgentSidebar .agent-model {
        color: $text-muted;
    }

    AgentSidebar .agent-status {
        color: $success;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.agents: list[tuple[str, str]] = []

    def compose(self) -> ComposeResult:
        yield Static("🤖 Active Agents", classes="sidebar-header")
        yield ListView(id="agent-list")

    def update_agents(self, agents: list[tuple[str, str]]):
        """Update the list of agents."""
        self.agents = agents
        agent_list = self.query_one("#agent-list", ListView)
        agent_list.clear()

        for role, model in agents:
            item = AgentListItem(role, model)
            # Create content for the list item
            content = f"🔹 {role}\n   ({model})"
            item.append(Static(content, classes="agent-info"))
            agent_list.append(item)


class CommandInput(Container):
    """Command input area at the bottom."""

    DEFAULT_CSS = """
    CommandInput {
        height: 5;
        border-top: solid $primary;
        padding: 1;
    }

    CommandInput Input {
        width: 1fr;
    }

    CommandInput .input-label {
        color: $primary;
        padding-bottom: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("💬 Send command to agent:", classes="input-label")
        yield Input(placeholder="Type a command and press Enter...", id="command-input")


class TmuxManagerApp(App):
    """Interactive Tmux Agent Manager."""

    CSS = """
    Screen {
        layout: grid;
        grid-size: 2 2;
        grid-columns: 35 1fr;
        grid-rows: 1fr auto;
    }

    #sidebar {
        row-span: 2;
    }

    #output-viewer {
        height: 1fr;
    }

    #command-input-container {
        height: auto;
    }

    .info-bar {
        background: $surface;
        padding: 1;
        text-align: center;
    }

    .button-group {
        layout: horizontal;
        height: auto;
        padding: 1;
    }

    .button-group Button {
        margin-right: 2;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("up", "previous_agent", "Previous Agent", show=False),
        Binding("down", "next_agent", "Next Agent", show=False),
        Binding("ctrl+k", "kill_agent", "Kill Agent"),
        Binding("ctrl+l", "clear_output", "Clear Output"),
        Binding("a", "attach_tmux", "Attach Tmux"),
    ]

    current_agent: reactive[Optional[str]] = reactive(None)
    refresh_interval: int = 2  # seconds

    def __init__(self, session_name: str = "catt-agents", **kwargs):
        super().__init__(**kwargs)
        self.controller = TmuxController(session_name=session_name)
        self.refresh_timer: Optional[Timer] = None

    def compose(self) -> ComposeResult:
        """Create the UI layout."""
        yield Header(show_clock=True)

        # Sidebar with agent list
        yield AgentSidebar(id="sidebar")

        # Main output viewer
        yield AgentOutputViewer(id="output-viewer")

        # Command input at bottom
        yield CommandInput(id="command-input-container")

        yield Footer()

    def on_mount(self) -> None:
        """Initialize the manager."""
        self.title = "Tmux Agent Manager"
        self.sub_title = f"Session: {self.controller.session}"

        # Load agents
        self._refresh_agents()

        # Start auto-refresh timer
        self.refresh_timer = self.set_interval(
            self.refresh_interval,
            self._auto_refresh
        )

        # Focus on agent list
        agent_list = self.query_one("#agent-list", ListView)
        agent_list.focus()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle agent selection."""
        if isinstance(event.item, AgentListItem):
            self.current_agent = event.item.role
            self._update_output()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle command submission."""
        if event.input.id == "command-input":
            command = event.value.strip()
            if command and self.current_agent:
                try:
                    self.controller.send_message(self.current_agent, command)
                    self.notify(f"Sent: {command}", title="Command Sent")
                    event.input.value = ""
                    # Refresh output after a moment
                    self.set_timer(1, self._update_output)
                except Exception as e:
                    self.notify(f"Error: {e}", severity="error")

    def action_refresh(self) -> None:
        """Manually refresh data."""
        self._refresh_agents()
        self._update_output()
        self.notify("Refreshed", title="Data Updated")

    def action_previous_agent(self) -> None:
        """Select previous agent."""
        agent_list = self.query_one("#agent-list", ListView)
        if agent_list.index > 0:
            agent_list.index -= 1

    def action_next_agent(self) -> None:
        """Select next agent."""
        agent_list = self.query_one("#agent-list", ListView)
        if agent_list.index < len(agent_list.children) - 1:
            agent_list.index += 1

    def action_kill_agent(self) -> None:
        """Kill the current agent."""
        if self.current_agent:
            try:
                self.controller.kill_agent(self.current_agent)
                self.notify(f"Killed agent: {self.current_agent}", severity="warning")
                self.current_agent = None
                self._refresh_agents()
            except Exception as e:
                self.notify(f"Error: {e}", severity="error")

    def action_clear_output(self) -> None:
        """Clear the output viewer."""
        output_viewer = self.query_one("#output-viewer", AgentOutputViewer)
        output_viewer.remove_children()
        self.notify("Output cleared")

    def action_attach_tmux(self) -> None:
        """Attach to tmux session (exit app)."""
        self.exit(message=f"attach:{self.controller.session}")

    def _refresh_agents(self) -> None:
        """Refresh the list of agents."""
        windows = self.controller.list_windows()

        # Filter out 'main' window and get agent info
        agents = []
        for window in windows:
            if window != "main":
                # Get model from controller's panes dict
                model = "unknown"
                if window in self.controller.panes:
                    # Try to detect model from window name or default to sonnet
                    model = "opus" if any(x in window.lower() for x in ["researcher", "architect", "manager"]) else "sonnet"
                agents.append((window, model))

        # Update sidebar
        sidebar = self.query_one("#sidebar", AgentSidebar)
        sidebar.update_agents(agents)

        # Select first agent if none selected
        if not self.current_agent and agents:
            self.current_agent = agents[0][0]
            self._update_output()

    def _update_output(self) -> None:
        """Update the output viewer for current agent."""
        if not self.current_agent:
            return

        try:
            output = self.controller.capture_output(self.current_agent, lines=50)
            output_viewer = self.query_one("#output-viewer", AgentOutputViewer)
            output_viewer.update_output(self.current_agent, output)
        except Exception as e:
            self.notify(f"Error capturing output: {e}", severity="error")

    def _auto_refresh(self) -> None:
        """Auto-refresh callback."""
        if self.current_agent:
            self._update_output()


def run_tmux_manager(session_name: str = "catt-agents") -> None:
    """Run the Tmux Manager TUI."""
    app = TmuxManagerApp(session_name=session_name)
    result = app.run()

    # If user chose to attach, do it
    if result and isinstance(result, str) and result.startswith("attach:"):
        session = result.split(":")[1]
        import subprocess
        subprocess.run(["tmux", "attach", "-t", session])


if __name__ == "__main__":
    run_tmux_manager()
