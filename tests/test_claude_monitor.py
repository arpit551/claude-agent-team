"""Unit tests for ClaudeStateReader and AgentOutputMonitor."""

import tempfile
from pathlib import Path
from datetime import datetime

import pytest

from cat.agent.claude_monitor import (
    ClaudeStateReader,
    ClaudeSession,
    AgentOutputMonitor,
)


class TestClaudeStateReader:
    """Tests for ClaudeStateReader class."""

    def test_initialization(self):
        """Test ClaudeStateReader initializes correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            reader = ClaudeStateReader(sessions_dir=sessions_dir)

            assert reader.sessions_dir == sessions_dir

    def test_initialization_default_dir(self):
        """Test ClaudeStateReader uses default directory."""
        reader = ClaudeStateReader()
        assert reader.sessions_dir == Path.home() / ".claude" / "sessions"

    def test_list_sessions_empty(self):
        """Test listing sessions when directory doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "nonexistent"
            reader = ClaudeStateReader(sessions_dir=sessions_dir)

            sessions = reader.list_sessions()
            assert sessions == []

    def test_list_sessions(self):
        """Test listing sessions from directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            sessions_dir.mkdir()

            # Create mock session directories
            (sessions_dir / "session1").mkdir()
            (sessions_dir / "session2").mkdir()

            reader = ClaudeStateReader(sessions_dir=sessions_dir)
            sessions = reader.list_sessions()

            assert len(sessions) == 2

    def test_find_session(self):
        """Test finding a session by working directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            sessions_dir.mkdir()

            # Create session with metadata
            session_dir = sessions_dir / "session1"
            session_dir.mkdir()

            working_dir = Path(tmpdir) / "project"
            working_dir.mkdir()

            metadata = {
                "session_id": "session1",
                "working_dir": str(working_dir),
                "created_at": datetime.now().isoformat(),
                "last_activity": datetime.now().isoformat(),
                "status": "active"
            }

            import json
            (session_dir / "metadata.json").write_text(json.dumps(metadata))

            reader = ClaudeStateReader(sessions_dir=sessions_dir)
            found = reader.find_session(working_dir)

            assert found is not None
            assert found.session_id == "session1"

    def test_find_nonexistent_session(self):
        """Test finding a non-existent session returns None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            sessions_dir.mkdir()

            reader = ClaudeStateReader(sessions_dir=sessions_dir)
            found = reader.find_session(Path("/nonexistent"))

            assert found is None

    def test_read_session_output(self):
        """Test reading session output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            sessions_dir.mkdir()

            session_dir = sessions_dir / "test-session"
            session_dir.mkdir()

            # Write test output
            output_file = session_dir / "output.txt"
            output_file.write_text("Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n")

            reader = ClaudeStateReader(sessions_dir=sessions_dir)
            output = reader.read_session_output("test-session", lines=3)

            assert "Line 3" in output
            assert "Line 4" in output
            assert "Line 5" in output

    def test_read_nonexistent_session_output(self):
        """Test reading output from non-existent session."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            reader = ClaudeStateReader(sessions_dir=sessions_dir)

            output = reader.read_session_output("nonexistent")
            assert output == ""

    def test_watch_session(self):
        """Test getting watch path for session."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            sessions_dir.mkdir()

            session_dir = sessions_dir / "test-session"
            session_dir.mkdir()

            output_file = session_dir / "output.txt"
            output_file.touch()

            reader = ClaudeStateReader(sessions_dir=sessions_dir)
            watch_path = reader.watch_session("test-session")

            assert watch_path == output_file


class TestClaudeSession:
    """Tests for ClaudeSession dataclass."""

    def test_session_creation(self):
        """Test creating a ClaudeSession."""
        now = datetime.now()
        session = ClaudeSession(
            session_id="test-123",
            working_dir=Path("/tmp/project"),
            created_at=now,
            last_activity=now,
            status="active"
        )

        assert session.session_id == "test-123"
        assert session.status == "active"
        assert session.is_active is True

    def test_session_inactive(self):
        """Test inactive session."""
        now = datetime.now()
        session = ClaudeSession(
            session_id="test-123",
            working_dir=Path("/tmp/project"),
            created_at=now,
            last_activity=now,
            status="completed"
        )

        assert session.is_active is False


class TestAgentOutputMonitor:
    """Tests for AgentOutputMonitor class."""

    def test_initialization(self):
        """Test AgentOutputMonitor initializes correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"
            monitor = AgentOutputMonitor(output_dir)

            assert monitor.output_dir == output_dir
            assert output_dir.exists()

    def test_get_agent_output_file(self):
        """Test getting agent output file path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"
            monitor = AgentOutputMonitor(output_dir)

            file_path = monitor.get_agent_output_file("researcher")
            assert file_path == output_dir / "researcher.log"

    def test_read_output(self):
        """Test reading agent output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"
            monitor = AgentOutputMonitor(output_dir)

            # Write test data
            output_file = monitor.get_agent_output_file("tester")
            output_file.write_text("Line 1\nLine 2\nLine 3\n")

            output = monitor.read_output("tester", lines=2)
            assert "Line 2" in output
            assert "Line 3" in output

    def test_read_nonexistent_output(self):
        """Test reading output from non-existent agent."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"
            monitor = AgentOutputMonitor(output_dir)

            output = monitor.read_output("nonexistent")
            assert output == ""

    def test_append_output(self):
        """Test appending output to agent log."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"
            monitor = AgentOutputMonitor(output_dir)

            monitor.append_output("developer", "First line")
            monitor.append_output("developer", "Second line")

            output = monitor.read_output("developer")
            assert "First line" in output
            assert "Second line" in output

    def test_clear_output(self):
        """Test clearing agent output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"
            monitor = AgentOutputMonitor(output_dir)

            # Write and then clear
            monitor.append_output("architect", "Test data")
            monitor.clear_output("architect")

            output_file = monitor.get_agent_output_file("architect")
            assert not output_file.exists()

    def test_watch_file(self):
        """Test getting watch file path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"
            monitor = AgentOutputMonitor(output_dir)

            watch_path = monitor.watch_file("reviewer")
            assert watch_path == output_dir / "reviewer.log"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
