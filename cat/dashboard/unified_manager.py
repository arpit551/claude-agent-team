"""Unified Agent & Task Manager - Combines Agent monitoring with Kanban board.

NOTE: This module needs refactoring to use AgentController instead of tmux.
Current implementation still uses subprocess calls to tmux - marked for migration.
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Header, Footer, Static, Label, Input
from textual.binding import Binding
from textual.reactive import reactive
from textual.message import Message
from rich.text import Text
from rich.panel import Panel
from rich.console import Console
from rich.table import Table
import subprocess
from typing import Optional, List
from pathlib import Path
import json
from datetime import datetime
from dataclasses import dataclass


@dataclass
class Agent:
    """Represents an agent process."""
    name: str
    model: str
    output: str = ""
    status: str = "running"
    activity: str = "Active"


@dataclass
class Task:
    """Represents a task."""
    id: str
    content: str
    status: str  # todo, in_progress, done
    active_form: str = ""


class CommandInput(Static):
    """Input widget for sending commands to agents."""

    def __init__(self, session_name: str = "test-calc"):
        super().__init__()
        self.session_name = session_name
        self.selected_agent: Optional[str] = None

    def compose(self) -> ComposeResult:
        yield Label("💬 Send Command to Agent", classes="panel-title")
        input_widget = Input(placeholder="Type command and press Enter...")
        input_widget.id = "command-input"
        yield input_widget

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle command submission."""
        if not self.selected_agent or not event.value.strip():
            return

        command = event.value.strip()

        try:
            # Send command to agent via tmux
            subprocess.run(
                ["tmux", "send-keys", "-t", f"{self.session_name}:{self.selected_agent}", command, "Enter"],
                check=False
            )

            # Clear input
            event.input.value = ""

            # Show feedback
            event.input.placeholder = f"✅ Sent to {self.selected_agent}!"

            # Reset placeholder after 2 seconds
            def reset_placeholder():
                event.input.placeholder = "Type command and press Enter..."

            self.set_timer(2, reset_placeholder)

        except Exception as e:
            event.input.placeholder = f"❌ Error: {str(e)}"


class AgentListPanel(Static):
    """Shows list of active agents."""

    selected_agent: reactive[Optional[str]] = reactive(None)
    agents: reactive[List[Agent]] = reactive([])

    def __init__(self, session_name: str = "test-calc"):
        super().__init__()
        self.session_name = session_name

    def compose(self) -> ComposeResult:
        yield Label("🤖 Active Agents", classes="panel-title")
        scroll = VerticalScroll()
        scroll.id = "agent-list-container"
        yield scroll

    def on_mount(self) -> None:
        self.refresh_agents()
        self.set_interval(2, self.refresh_agents)

    def refresh_agents(self) -> None:
        """Refresh the agent list from tmux."""
        try:
            result = subprocess.run(
                ["tmux", "list-windows", "-t", self.session_name, "-F", "#{window_name}"],
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode == 0:
                windows = result.stdout.strip().split('\n')
                # Filter out 'main' window
                windows = [w for w in windows if w and w != 'main']

                new_agents = []
                for window in windows:
                    # Capture model info and status from output
                    output = self.capture_agent_output(window)
                    model = self.detect_model(output)
                    status = self.detect_status(output)
                    activity = self.get_current_activity(output)

                    agent = Agent(
                        name=window,
                        model=model,
                        output=output,
                        status=status
                    )
                    # Store activity as part of output for display
                    agent.activity = activity
                    new_agents.append(agent)

                self.agents = new_agents
                self.update_display()

        except Exception as e:
            pass

    def capture_agent_output(self, agent_name: str, lines: int = 30) -> str:
        """Capture output from an agent."""
        try:
            result = subprocess.run(
                ["tmux", "capture-pane", "-t", f"{self.session_name}:{agent_name}", "-p", "-S", f"-{lines}"],
                capture_output=True,
                text=True,
                check=False
            )
            return result.stdout if result.returncode == 0 else ""
        except:
            return ""

    def detect_model(self, output: str) -> str:
        """Detect model from output."""
        if "Opus" in output:
            return "opus"
        elif "Sonnet" in output:
            return "sonnet"
        return "unknown"

    def detect_status(self, output: str) -> str:
        """Detect agent status."""
        # Check for completion signals
        if "<promise>" in output and "COMPLETE</promise>" in output:
            return "done"
        elif "COMPLETE" in output or "✻ Done" in output:
            return "done"
        elif "Error" in output or "Failed" in output or "❌" in output:
            return "error"
        elif "Waiting" in output or "waiting" in output:
            return "waiting"
        elif "⏺" in output or "Cogitating" in output or "thinking" in output:
            return "thinking"
        return "running"

    def get_current_activity(self, output: str) -> str:
        """Extract what the agent is currently doing."""
        # Look for activity indicators in the output
        lines = output.strip().split('\n')

        # Check last few lines for activity
        for line in reversed(lines[-10:]):
            line = line.strip()
            # Look for common patterns
            if line.startswith('⏺'):
                # Extract action after the indicator
                return line[2:60].strip() if len(line) > 2 else "Working..."
            elif any(action in line.lower() for action in ['writing', 'reading', 'creating', 'implementing', 'testing', 'researching']):
                return line[:60].strip()

        return "Active"

    def update_display(self) -> None:
        """Update the agent list display."""
        container = self.query_one("#agent-list-container")
        container.remove_children()

        for agent in self.agents:
            # Status emoji
            if agent.status == "done":
                status_emoji = "✅"
            elif agent.status == "error":
                status_emoji = "❌"
            elif agent.status == "waiting":
                status_emoji = "⏸️"
            elif agent.status == "thinking":
                status_emoji = "💭"
            else:
                status_emoji = "🔄"

            # Truncate activity for display
            activity = agent.activity[:40] + "..." if len(agent.activity) > 40 else agent.activity

            # Highlight selected
            if agent.name == self.selected_agent:
                label = f"▶ {status_emoji} {agent.name}\n   ({agent.model})\n   {activity}"
                style = "reverse bold"
            else:
                label = f"  {status_emoji} {agent.name}\n   ({agent.model})\n   {activity}"
                style = ""

            widget = Label(label)
            if style:
                widget.styles.background = "blue"
                widget.styles.color = "white"
            container.mount(widget)


class AgentOutputPanel(Static):
    """Shows output from selected agent."""

    agent_name: reactive[Optional[str]] = reactive(None)
    output: reactive[str] = reactive("")

    def __init__(self, session_name: str = "test-calc"):
        super().__init__()
        self.session_name = session_name

    def compose(self) -> ComposeResult:
        yield Label("📺 Agent Output", classes="panel-title")
        scroll = VerticalScroll(Static("Select an agent to view output"))
        scroll.id = "output-container"
        yield scroll

    def on_mount(self) -> None:
        self.set_interval(2, self.refresh_output)

    def watch_agent_name(self, new_name: Optional[str]) -> None:
        """When agent selection changes, update display."""
        self.refresh_output()

    def refresh_output(self) -> None:
        """Refresh the output display."""
        if not self.agent_name:
            return

        try:
            result = subprocess.run(
                ["tmux", "capture-pane", "-t", f"{self.session_name}:{self.agent_name}", "-p", "-S", "-40"],
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode == 0:
                self.output = result.stdout
                container = self.query_one("#output-container")
                container.remove_children()

                # Show last 40 lines
                lines = self.output.split('\n')[-40:]
                content = '\n'.join(lines)

                container.mount(Static(content))
        except:
            pass


class KanbanPanel(Static):
    """Shows task kanban board."""

    tasks: reactive[List[Task]] = reactive([])

    def compose(self) -> ComposeResult:
        yield Label("📋 Task Board", classes="panel-title")

        todo_col = Vertical(Static("TODO", classes="column-header"))
        todo_col.id = "todo-column"

        progress_col = Vertical(Static("IN PROGRESS", classes="column-header"))
        progress_col.id = "progress-column"

        done_col = Vertical(Static("DONE", classes="column-header"))
        done_col.id = "done-column"

        container = Horizontal(todo_col, progress_col, done_col)
        container.id = "kanban-container"

        yield container

    def on_mount(self) -> None:
        self.refresh_tasks()
        self.set_interval(5, self.refresh_tasks)

    def refresh_tasks(self) -> None:
        """Load tasks from Claude's todo directory."""
        try:
            todo_dir = Path.home() / ".claude" / "todos"
            if not todo_dir.exists():
                return

            tasks = []
            for task_file in sorted(todo_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)[:20]:
                try:
                    with open(task_file) as f:
                        data = json.load(f)

                        status_map = {
                            "pending": "todo",
                            "in_progress": "in_progress",
                            "completed": "done"
                        }

                        tasks.append(Task(
                            id=data.get("id", ""),
                            content=data.get("content", "")[:50],
                            status=status_map.get(data.get("status", "pending"), "todo"),
                            active_form=data.get("activeForm", "")[:40]
                        ))
                except:
                    continue

            self.tasks = tasks
            self.update_kanban()
        except:
            pass

    def update_kanban(self) -> None:
        """Update kanban columns."""
        # Clear columns
        todo_col = self.query_one("#todo-column")
        progress_col = self.query_one("#progress-column")
        done_col = self.query_one("#done-column")

        for col in [todo_col, progress_col, done_col]:
            # Remove all except header
            for child in list(col.children)[1:]:
                child.remove()

        # Add tasks to columns
        for task in self.tasks:
            task_widget = Static(f"• {task.content}")
            task_widget.styles.padding = (0, 1)
            task_widget.styles.margin = (0, 0, 1, 0)

            if task.status == "todo":
                todo_col.mount(task_widget)
            elif task.status == "in_progress":
                progress_col.mount(task_widget)
            elif task.status == "done":
                done_col.mount(task_widget)


class StatsPanel(Static):
    """Shows statistics."""

    def __init__(self, session_name: str = "test-calc"):
        super().__init__()
        self.session_name = session_name

    def compose(self) -> ComposeResult:
        yield Label("📊 Statistics", classes="panel-title")
        stats = Static()
        stats.id = "stats-content"
        yield stats

    def on_mount(self) -> None:
        self.set_interval(3, self.refresh_stats)
        self.refresh_stats()

    def refresh_stats(self) -> None:
        """Update statistics."""
        try:
            # Count agents
            result = subprocess.run(
                ["tmux", "list-windows", "-t", self.session_name, "-F", "#{window_name}"],
                capture_output=True,
                text=True,
                check=False
            )

            agent_count = 0
            if result.returncode == 0:
                windows = result.stdout.strip().split('\n')
                agent_count = len([w for w in windows if w and w != 'main'])

            # Count tasks
            todo_dir = Path.home() / ".claude" / "todos"
            task_counts = {"todo": 0, "in_progress": 0, "done": 0}

            if todo_dir.exists():
                for task_file in todo_dir.glob("*.json"):
                    try:
                        with open(task_file) as f:
                            data = json.load(f)
                            status = data.get("status", "pending")
                            if status == "pending":
                                task_counts["todo"] += 1
                            elif status == "in_progress":
                                task_counts["in_progress"] += 1
                            elif status == "completed":
                                task_counts["done"] += 1
                    except:
                        continue

            stats_text = f"""
Active Agents: {agent_count}
Session: {self.session_name}

Tasks:
  📋 TODO: {task_counts['todo']}
  🔄 In Progress: {task_counts['in_progress']}
  ✅ Done: {task_counts['done']}

Updated: {datetime.now().strftime('%H:%M:%S')}
"""

            stats_widget = self.query_one("#stats-content")
            stats_widget.update(stats_text)
        except:
            pass


class UnifiedManager(App):
    """Unified Agent & Task Manager."""

    CSS = """
    Screen {
        layout: grid;
        grid-size: 3 4;
        grid-columns: 1fr 2fr 1fr;
        grid-rows: auto 1fr auto auto;
    }

    Header {
        column-span: 3;
    }

    Footer {
        column-span: 3;
    }

    #command-panel {
        border: solid magenta;
        column-span: 3;
        height: 5;
    }

    #agent-panel {
        border: solid blue;
        height: 100%;
    }

    #output-panel {
        border: solid green;
        height: 100%;
    }

    #kanban-panel {
        border: solid yellow;
        height: 100%;
    }

    #stats-panel {
        border: solid cyan;
        column-span: 3;
        height: 10;
    }

    .panel-title {
        background: $accent;
        color: $text;
        padding: 0 1;
        text-align: center;
        text-style: bold;
    }

    .column-header {
        background: $primary;
        color: $text;
        text-align: center;
        padding: 0 1;
        text-style: bold;
    }

    #kanban-container {
        height: 100%;
    }

    #todo-column, #progress-column, #done-column {
        width: 1fr;
        border-right: solid $primary;
        padding: 1;
    }

    #output-container {
        height: 100%;
        overflow-y: scroll;
    }

    #agent-list-container {
        height: 100%;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("up", "previous_agent", "Previous Agent", show=False),
        Binding("down", "next_agent", "Next Agent", show=False),
        Binding("ctrl+k", "kill_agent", "Kill Agent"),
        Binding("c", "focus_command", "Command", show=True),
        Binding("i", "broadcast", "Broadcast", show=True),
        Binding("a", "attach_tmux", "Attach Tmux"),
        Binding("h", "show_help", "Help", show=True),
        Binding("?", "show_help", "Help", show=False),
    ]

    TITLE = "🚀 CATT Unified Manager"

    def __init__(self, session_name: str = "test-calc"):
        super().__init__()
        self.session_name = session_name

    def compose(self) -> ComposeResult:
        yield Header()

        agent_panel = AgentListPanel(self.session_name)
        agent_panel.id = "agent-panel"
        yield agent_panel

        output_panel = AgentOutputPanel(self.session_name)
        output_panel.id = "output-panel"
        yield output_panel

        kanban_panel = KanbanPanel()
        kanban_panel.id = "kanban-panel"
        yield kanban_panel

        command_panel = CommandInput(self.session_name)
        command_panel.id = "command-panel"
        yield command_panel

        stats_panel = StatsPanel(self.session_name)
        stats_panel.id = "stats-panel"
        yield stats_panel

        yield Footer()

    def action_refresh(self) -> None:
        """Manually refresh all panels."""
        self.query_one(AgentListPanel).refresh_agents()
        self.query_one(AgentOutputPanel).refresh_output()
        self.query_one(KanbanPanel).refresh_tasks()
        self.query_one(StatsPanel).refresh_stats()

    def action_next_agent(self) -> None:
        """Select next agent."""
        agent_panel = self.query_one(AgentListPanel)
        if not agent_panel.agents:
            return

        if agent_panel.selected_agent is None:
            agent_panel.selected_agent = agent_panel.agents[0].name
        else:
            # Find current index
            names = [a.name for a in agent_panel.agents]
            try:
                current_idx = names.index(agent_panel.selected_agent)
                next_idx = (current_idx + 1) % len(names)
                agent_panel.selected_agent = names[next_idx]
            except ValueError:
                agent_panel.selected_agent = names[0]

        # Update output panel
        output_panel = self.query_one(AgentOutputPanel)
        output_panel.agent_name = agent_panel.selected_agent

        # Update command input
        command_panel = self.query_one(CommandInput)
        command_panel.selected_agent = agent_panel.selected_agent

        agent_panel.update_display()

    def action_previous_agent(self) -> None:
        """Select previous agent."""
        agent_panel = self.query_one(AgentListPanel)
        if not agent_panel.agents:
            return

        if agent_panel.selected_agent is None:
            agent_panel.selected_agent = agent_panel.agents[-1].name
        else:
            names = [a.name for a in agent_panel.agents]
            try:
                current_idx = names.index(agent_panel.selected_agent)
                prev_idx = (current_idx - 1) % len(names)
                agent_panel.selected_agent = names[prev_idx]
            except ValueError:
                agent_panel.selected_agent = names[0]

        # Update output panel
        output_panel = self.query_one(AgentOutputPanel)
        output_panel.agent_name = agent_panel.selected_agent

        # Update command input
        command_panel = self.query_one(CommandInput)
        command_panel.selected_agent = agent_panel.selected_agent

        agent_panel.update_display()

    def action_kill_agent(self) -> None:
        """Kill the selected agent."""
        agent_panel = self.query_one(AgentListPanel)
        if agent_panel.selected_agent:
            try:
                subprocess.run(
                    ["tmux", "kill-window", "-t", f"{self.session_name}:{agent_panel.selected_agent}"],
                    check=False
                )
                # Refresh
                self.action_refresh()
            except:
                pass

    def action_attach_tmux(self) -> None:
        """Attach to the tmux session."""
        self.exit()
        subprocess.run(["tmux", "attach", "-t", self.session_name])

    def action_focus_command(self) -> None:
        """Focus the command input."""
        try:
            command_input = self.query_one("#command-input", Input)
            command_input.focus()
        except:
            pass

    def action_broadcast(self) -> None:
        """Broadcast a command to all agents."""
        agent_panel = self.query_one(AgentListPanel)
        if not agent_panel.agents:
            return

        # TODO: Show a dialog to input broadcast message
        # For now, just focus command input
        self.action_focus_command()

    def action_show_help(self) -> None:
        """Show help information."""
        help_text = """
🚀 UNIFIED MANAGER HELP

NAVIGATION:
  ↑/↓         Navigate between agents
  Enter       Select agent

COMMANDS:
  c           Focus command input (send to selected agent)
  i           Broadcast to all agents
  r           Refresh all panels

AGENT MANAGEMENT:
  Ctrl+K      Kill selected agent
  a           Attach to raw tmux session

STATUS INDICATORS:
  ✅ Done     Agent completed work
  ❌ Error    Agent encountered error
  ⏸️ Waiting  Agent is waiting
  💭 Thinking Agent is processing
  🔄 Running  Agent actively working

OTHER:
  h or ?      Show this help
  q           Quit manager

QUICK START:
  1. Press ↑/↓ to select an agent
  2. Watch live output in center panel
  3. See tasks in right panel
  4. Press 'c' to send commands
  5. Press 'q' to quit

Press any key to close this help...
"""
        # For now, just print to console
        # TODO: Show in a modal dialog
        print(help_text)


def run_unified_manager(session_name: str = "test-calc") -> None:
    """Run the unified manager."""
    app = UnifiedManager(session_name=session_name)
    app.run()


if __name__ == "__main__":
    run_unified_manager()
