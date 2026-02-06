"""Monitor Claude Code sessions and read agent state."""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class ClaudeSession:
    """Represents a Claude Code session."""

    session_id: str
    working_dir: Path
    created_at: datetime
    last_activity: datetime
    status: str  # "active", "idle", "completed"
    output_file: Optional[Path] = None

    @property
    def is_active(self) -> bool:
        """Check if session appears active."""
        return self.status == "active"


class ClaudeStateReader:
    """Reads Claude Code session state from ~/.claude/sessions/."""

    def __init__(self, sessions_dir: Optional[Path] = None):
        """Initialize the state reader.

        Args:
            sessions_dir: Path to Claude sessions directory
                         (defaults to ~/.claude/sessions/)
        """
        if sessions_dir is None:
            sessions_dir = Path.home() / ".claude" / "sessions"
        self.sessions_dir = sessions_dir

    def list_sessions(self) -> list[ClaudeSession]:
        """List all available Claude sessions.

        Returns:
            List of ClaudeSession objects
        """
        if not self.sessions_dir.exists():
            return []

        sessions = []
        for session_path in self.sessions_dir.iterdir():
            if not session_path.is_dir():
                continue

            try:
                session = self._read_session(session_path)
                if session:
                    sessions.append(session)
            except Exception:
                continue

        return sorted(sessions, key=lambda s: s.last_activity, reverse=True)

    def _read_session(self, session_path: Path) -> Optional[ClaudeSession]:
        """Read a single session's metadata.

        Args:
            session_path: Path to session directory

        Returns:
            ClaudeSession or None if invalid
        """
        # Look for session metadata files
        # This is a simplified implementation - actual structure may vary
        meta_file = session_path / "metadata.json"
        if not meta_file.exists():
            # Fallback: infer from directory structure
            return ClaudeSession(
                session_id=session_path.name,
                working_dir=session_path,
                created_at=datetime.fromtimestamp(session_path.stat().st_ctime),
                last_activity=datetime.fromtimestamp(session_path.stat().st_mtime),
                status="idle",
            )

        with open(meta_file) as f:
            metadata = json.load(f)

        return ClaudeSession(
            session_id=metadata.get("session_id", session_path.name),
            working_dir=Path(metadata.get("working_dir", session_path)),
            created_at=datetime.fromisoformat(metadata["created_at"]),
            last_activity=datetime.fromisoformat(metadata["last_activity"]),
            status=metadata.get("status", "idle"),
            output_file=Path(metadata["output_file"]) if metadata.get("output_file") else None,
        )

    def find_session(self, working_dir: Path) -> Optional[ClaudeSession]:
        """Find a session by working directory.

        Args:
            working_dir: Working directory to search for

        Returns:
            ClaudeSession or None if not found
        """
        for session in self.list_sessions():
            if session.working_dir == working_dir:
                return session
        return None

    def read_session_output(self, session_id: str, lines: int = 100) -> str:
        """Read recent output from a Claude session.

        Args:
            session_id: Session identifier
            lines: Number of lines to read

        Returns:
            Output text
        """
        session_path = self.sessions_dir / session_id
        if not session_path.exists():
            return ""

        # Look for output file
        output_file = session_path / "output.txt"
        if not output_file.exists():
            # Try alternative locations
            output_file = session_path / "transcript.txt"

        if not output_file.exists():
            return ""

        # Read last N lines
        try:
            with open(output_file) as f:
                all_lines = f.readlines()
                return "".join(all_lines[-lines:])
        except Exception:
            return ""

    def watch_session(self, session_id: str) -> Optional[Path]:
        """Get path to watch for session updates.

        Args:
            session_id: Session identifier

        Returns:
            Path to watch, or None if not found
        """
        session_path = self.sessions_dir / session_id
        if not session_path.exists():
            return None

        output_file = session_path / "output.txt"
        if output_file.exists():
            return output_file

        return session_path


class AgentOutputMonitor:
    """Monitor agent output using file watching instead of tmux."""

    def __init__(self, output_dir: Path):
        """Initialize the monitor.

        Args:
            output_dir: Directory where agent output files are stored
        """
        self.output_dir = output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

    def get_agent_output_file(self, role: str) -> Path:
        """Get the output file path for an agent.

        Args:
            role: Agent role name

        Returns:
            Path to output file
        """
        return self.output_dir / f"{role}.log"

    def read_output(self, role: str, lines: int = 100) -> str:
        """Read recent output from an agent.

        Args:
            role: Agent role name
            lines: Number of lines to read from end

        Returns:
            Output text
        """
        output_file = self.get_agent_output_file(role)
        if not output_file.exists():
            return ""

        try:
            with open(output_file) as f:
                all_lines = f.readlines()
                return "".join(all_lines[-lines:])
        except Exception:
            return ""

    def append_output(self, role: str, text: str) -> None:
        """Append output to agent's log file.

        Args:
            role: Agent role name
            text: Text to append
        """
        output_file = self.get_agent_output_file(role)
        with open(output_file, "a") as f:
            f.write(text)
            if not text.endswith("\n"):
                f.write("\n")

    def clear_output(self, role: str) -> None:
        """Clear an agent's output file.

        Args:
            role: Agent role name
        """
        output_file = self.get_agent_output_file(role)
        if output_file.exists():
            output_file.unlink()

    def watch_file(self, role: str) -> Path:
        """Get path to watch for updates.

        Args:
            role: Agent role name

        Returns:
            Path to output file
        """
        return self.get_agent_output_file(role)
