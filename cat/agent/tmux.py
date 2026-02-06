"""Tmux controller for spawning Claude Code agents."""

import subprocess
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class TmuxPane:
    """Represents a tmux pane."""

    session: str
    window: str
    pane: int = 0

    @property
    def target(self) -> str:
        """Get tmux target string."""
        return f"{self.session}:{self.window}.{self.pane}"

    @property
    def window_target(self) -> str:
        """Get tmux window target string."""
        return f"{self.session}:{self.window}"


class TmuxController:
    """Manages tmux sessions for agent spawning."""

    SESSION_NAME = "catt-agents"

    def __init__(self, session_name: Optional[str] = None):
        self.session = session_name or self.SESSION_NAME
        self.panes: dict[str, TmuxPane] = {}
        self._ensure_tmux_available()

    def _ensure_tmux_available(self) -> None:
        """Verify tmux is installed."""
        if not shutil.which("tmux"):
            raise RuntimeError(
                "tmux is not installed. Install with: brew install tmux (macOS)"
            )

    def _run_tmux(self, *args, check: bool = True, capture: bool = False) -> Optional[str]:
        """Execute a tmux command."""
        cmd = ["tmux"] + list(args)
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=check,
            )
            if capture:
                return result.stdout.strip()
            return None
        except subprocess.CalledProcessError as e:
            if not check:
                return None
            raise RuntimeError(f"tmux command failed: {' '.join(cmd)}\n{e.stderr}")

    def session_exists(self) -> bool:
        """Check if the session already exists."""
        result = self._run_tmux(
            "list-sessions", "-F", "#{session_name}",
            check=False, capture=True
        )
        if result:
            return self.session in result.split("\n")
        return False

    def create_session(self) -> None:
        """Create the CATT agent session if not exists."""
        if self.session_exists():
            return

        # Create new session in detached mode
        self._run_tmux(
            "new-session", "-d",
            "-s", self.session,
            "-n", "main"
        )

    def kill_session(self) -> None:
        """Kill the entire agent session."""
        if self.session_exists():
            self._run_tmux("kill-session", "-t", self.session, check=False)
        self.panes.clear()

    def kill_window(self, window_name: str) -> None:
        """Kill a window by name if it exists.

        Args:
            window_name: Name of the window to kill
        """
        target = f"{self.session}:{window_name}"
        self._run_tmux("kill-window", "-t", target, check=False)

    def spawn_agent(
        self,
        role: str,
        prompt: str,
        model: str = "sonnet",
        working_dir: Optional[Path] = None,
    ) -> TmuxPane:
        """Spawn a new Claude Code agent in a tmux window.

        Args:
            role: Agent role name (used as window name)
            prompt: The prompt to send to Claude Code
            model: Model to use (opus or sonnet)
            working_dir: Working directory for the agent

        Returns:
            TmuxPane representing the agent's pane
        """
        self.create_session()

        # Kill any existing window with this name to avoid duplicates
        self.kill_window(role)

        # Create new window for agent
        self._run_tmux(
            "new-window",
            "-t", self.session,
            "-n", role,
        )

        pane = TmuxPane(
            session=self.session,
            window=role,
            pane=0,
        )

        # Change to working directory if specified
        if working_dir:
            self._run_tmux(
                "send-keys",
                "-t", pane.target,
                f"cd {working_dir}",
                "Enter"
            )

        # Build and send the Claude Code command
        # Escape single quotes in prompt
        escaped_prompt = prompt.replace("'", "'\"'\"'")
        claude_cmd = f"claude --dangerously-skip-permissions --model {model} '{escaped_prompt}'"

        self._run_tmux(
            "send-keys",
            "-t", pane.target,
            claude_cmd,
            "Enter"
        )

        self.panes[role] = pane
        return pane

    def send_message(self, role: str, message: str) -> None:
        """Send a message to an agent's pane.

        Args:
            role: Agent role name
            message: Message to send
        """
        if role not in self.panes:
            raise ValueError(f"No pane for agent: {role}")

        pane = self.panes[role]
        escaped = message.replace("'", "'\"'\"'")

        self._run_tmux(
            "send-keys",
            "-t", pane.target,
            escaped,
            "Enter"
        )

    def capture_output(self, role: str, lines: int = 50) -> str:
        """Capture recent output from an agent's pane.

        Args:
            role: Agent role name
            lines: Number of lines to capture

        Returns:
            Captured output text
        """
        if role not in self.panes:
            return ""

        pane = self.panes[role]
        output = self._run_tmux(
            "capture-pane",
            "-t", pane.target,
            "-p",
            "-S", f"-{lines}",
            capture=True
        )
        return output or ""

    def kill_agent(self, role: str) -> None:
        """Kill an agent's window.

        Args:
            role: Agent role name
        """
        if role in self.panes:
            pane = self.panes[role]
            self._run_tmux(
                "kill-window",
                "-t", pane.window_target,
                check=False
            )
            del self.panes[role]

    def list_windows(self) -> list[str]:
        """List all windows in the session.

        Returns:
            List of window names
        """
        if not self.session_exists():
            return []

        output = self._run_tmux(
            "list-windows",
            "-t", self.session,
            "-F", "#{window_name}",
            capture=True
        )
        if output:
            return output.split("\n")
        return []

    def attach(self) -> None:
        """Attach to the agent session (for debugging)."""
        if self.session_exists():
            subprocess.run(["tmux", "attach", "-t", self.session])

    def select_window(self, role: str) -> None:
        """Select a window to view.

        Args:
            role: Agent role name
        """
        if role in self.panes:
            pane = self.panes[role]
            self._run_tmux(
                "select-window",
                "-t", pane.window_target,
                check=False
            )

    def get_pane_info(self, role: str) -> Optional[dict]:
        """Get information about a pane.

        Args:
            role: Agent role name

        Returns:
            Dictionary with pane info or None
        """
        if role not in self.panes:
            return None

        pane = self.panes[role]
        output = self._run_tmux(
            "display-message",
            "-t", pane.target,
            "-p",
            "#{pane_pid}|#{pane_current_command}|#{pane_width}|#{pane_height}",
            capture=True
        )

        if output:
            parts = output.split("|")
            if len(parts) >= 4:
                return {
                    "pid": parts[0],
                    "command": parts[1],
                    "width": int(parts[2]),
                    "height": int(parts[3]),
                }
        return None

    def is_agent_active(self, role: str) -> bool:
        """Check if an agent's process is still running.

        Args:
            role: Agent role name

        Returns:
            True if the agent appears to be running
        """
        info = self.get_pane_info(role)
        if info and info.get("command"):
            # Check if claude is still running
            return "claude" in info["command"].lower()
        return False


# Convenience function
def get_tmux_controller(session_name: Optional[str] = None) -> TmuxController:
    """Get a TmuxController instance."""
    return TmuxController(session_name)
