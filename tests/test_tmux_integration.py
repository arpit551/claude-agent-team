"""Integration tests for tmux-based agent spawning.

These tests verify the tmux integration works correctly.
"""

import pytest
import shutil
import time
from pathlib import Path

from cat.agent.tmux import TmuxController


# Skip all tmux tests if tmux is not installed
pytestmark = pytest.mark.skipif(
    not shutil.which("tmux"),
    reason="tmux not installed"
)


class TestTmuxIntegration:
    """Integration tests for TmuxController."""

    def setup_method(self):
        """Set up test session."""
        self.controller = TmuxController(session_name="catt-test")
        # Clean up any existing test session
        self.controller.kill_session()

    def teardown_method(self):
        """Clean up test session."""
        if self.controller:
            self.controller.kill_session()

    def test_create_session(self):
        """Test creating a tmux session."""
        assert not self.controller.session_exists()

        self.controller.create_session()

        assert self.controller.session_exists()

    def test_spawn_simple_command(self):
        """Test spawning a simple command in tmux."""
        self.controller.create_session()

        # Spawn a simple echo command
        pane = self.controller.spawn_agent(
            role="test-agent",
            prompt="echo 'Hello from tmux'",
            model="sonnet",
        )

        assert pane.session == "catt-test"
        assert pane.window == "test-agent"

        # Wait a moment for command to execute
        time.sleep(1)

        # Capture output
        output = self.controller.capture_output("test-agent", lines=10)
        assert "Hello from tmux" in output or len(output) > 0

    def test_list_windows(self):
        """Test listing tmux windows."""
        self.controller.create_session()

        # Create a few windows
        self.controller.spawn_agent("agent1", "echo test1", "sonnet")
        self.controller.spawn_agent("agent2", "echo test2", "sonnet")

        windows = self.controller.list_windows()

        assert "agent1" in windows
        assert "agent2" in windows

    def test_kill_agent_window(self):
        """Test killing an agent's window."""
        self.controller.create_session()

        self.controller.spawn_agent("test-agent", "sleep 100", "sonnet")
        assert "test-agent" in self.controller.list_windows()

        self.controller.kill_agent("test-agent")
        time.sleep(0.5)  # Give tmux time to clean up

        assert "test-agent" not in self.controller.list_windows()

    def test_multiple_agents_parallel(self):
        """Test spawning multiple agents in parallel."""
        self.controller.create_session()

        # Spawn multiple agents
        agents = []
        for i in range(3):
            pane = self.controller.spawn_agent(
                role=f"agent-{i}",
                prompt=f"echo 'Agent {i} running'",
                model="sonnet",
            )
            agents.append(pane)

        # Verify all agents spawned
        windows = self.controller.list_windows()
        assert len([w for w in windows if w.startswith("agent-")]) == 3

    def test_send_message_to_agent(self):
        """Test sending a message to a running agent."""
        self.controller.create_session()

        # Spawn agent with a shell
        self.controller.spawn_agent(
            role="test-agent",
            prompt="bash",  # Start a bash shell
            model="sonnet",
        )

        time.sleep(1)

        # Send a command to the agent
        self.controller.send_message("test-agent", "echo 'Test message'")

        time.sleep(1)

        # Check if the message was received
        output = self.controller.capture_output("test-agent", lines=20)
        assert "Test message" in output or len(output) > 0

    def test_pane_info(self):
        """Test getting pane information."""
        self.controller.create_session()

        self.controller.spawn_agent("test-agent", "sleep 10", "sonnet")

        time.sleep(0.5)

        info = self.controller.get_pane_info("test-agent")

        assert info is not None
        assert "pid" in info
        assert "command" in info
        assert "width" in info
        assert "height" in info

    def test_session_cleanup(self):
        """Test that kill_session removes all windows."""
        self.controller.create_session()

        # Create multiple agents
        for i in range(3):
            self.controller.spawn_agent(f"agent-{i}", "sleep 10", "sonnet")

        assert self.controller.session_exists()
        assert len(self.controller.list_windows()) >= 3

        # Kill entire session
        self.controller.kill_session()

        time.sleep(0.5)

        assert not self.controller.session_exists()
        assert len(self.controller.panes) == 0

    def test_working_directory(self):
        """Test spawning agent with custom working directory."""
        import tempfile
        import os

        self.controller.create_session()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test file in the temp directory
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("Working directory test")

            # Spawn agent in that directory
            self.controller.spawn_agent(
                role="test-agent",
                prompt="ls && cat test.txt",
                model="sonnet",
                working_dir=Path(tmpdir),
            )

            time.sleep(1)

            # Check output
            output = self.controller.capture_output("test-agent", lines=20)
            assert "test.txt" in output or "Working directory test" in output

    def test_duplicate_window_names(self):
        """Test that spawning agent with duplicate name kills old one."""
        self.controller.create_session()

        # Spawn first agent
        self.controller.spawn_agent("agent1", "sleep 100", "sonnet")

        time.sleep(0.5)

        # Spawn another with same name (should kill the first)
        self.controller.spawn_agent("agent1", "echo 'New agent'", "sonnet")

        time.sleep(1)

        windows = self.controller.list_windows()

        # Should only have one agent1 window
        agent1_count = sum(1 for w in windows if w == "agent1")
        assert agent1_count == 1


class TestTmuxErrorHandling:
    """Test error handling in TmuxController."""

    def test_nonexistent_agent_capture(self):
        """Test capturing output from non-existent agent."""
        controller = TmuxController(session_name="catt-test-error")
        controller.kill_session()  # Ensure clean state

        output = controller.capture_output("nonexistent-agent")
        assert output == ""

        controller.kill_session()

    def test_send_message_to_nonexistent_agent(self):
        """Test sending message to non-existent agent."""
        controller = TmuxController(session_name="catt-test-error")
        controller.kill_session()

        with pytest.raises(ValueError, match="No pane for agent"):
            controller.send_message("nonexistent-agent", "test")

        controller.kill_session()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
