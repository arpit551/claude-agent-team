"""Unit tests for AgentController."""

import tempfile
from pathlib import Path

import pytest

from cat.agent.controller import AgentController, AgentProcess


class TestAgentController:
    """Tests for AgentController class."""

    def test_initialization(self):
        """Test AgentController initializes correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"
            controller = AgentController(output_dir=output_dir)

            assert controller.output_dir == output_dir
            assert output_dir.exists()
            assert output_dir.is_dir()
            assert len(controller.agents) == 0

    def test_initialization_default_dir(self):
        """Test AgentController creates default output directory."""
        controller = AgentController()
        assert controller.output_dir.name == "output"
        assert controller.output_dir.exists()

    def test_spawn_agent(self):
        """Test spawning an agent creates AgentProcess."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"
            controller = AgentController(output_dir=output_dir)

            agent = controller.spawn_agent(
                role="researcher",
                prompt="Test prompt",
                model="sonnet",
                working_dir=Path(tmpdir)
            )

            assert isinstance(agent, AgentProcess)
            assert agent.role == "researcher"
            assert agent.working_dir == Path(tmpdir)
            assert agent.output_file.exists()
            assert agent.task_id.startswith("researcher_")

    def test_spawn_multiple_agents(self):
        """Test spawning multiple agents."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"
            controller = AgentController(output_dir=output_dir)

            agent1 = controller.spawn_agent("researcher", "Prompt 1", "sonnet")
            agent2 = controller.spawn_agent("architect", "Prompt 2", "opus")

            assert len(controller.agents) == 2
            assert "researcher" in controller.agents
            assert "architect" in controller.agents

    def test_get_agent(self):
        """Test retrieving an agent by role."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"
            controller = AgentController(output_dir=output_dir)

            spawned = controller.spawn_agent("tester", "Test", "sonnet")
            retrieved = controller.get_agent("tester")

            assert retrieved is not None
            assert retrieved.role == "tester"
            assert retrieved.task_id == spawned.task_id

    def test_get_nonexistent_agent(self):
        """Test retrieving a non-existent agent returns None."""
        controller = AgentController()
        agent = controller.get_agent("nonexistent")
        assert agent is None

    def test_kill_agent(self):
        """Test killing an agent."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"
            controller = AgentController(output_dir=output_dir)

            controller.spawn_agent("developer", "Code", "sonnet")
            result = controller.kill_agent("developer")

            assert result is True

    def test_kill_nonexistent_agent(self):
        """Test killing a non-existent agent returns False."""
        controller = AgentController()
        result = controller.kill_agent("nonexistent")
        assert result is False

    def test_capture_output(self):
        """Test capturing agent output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"
            controller = AgentController(output_dir=output_dir)

            agent = controller.spawn_agent("reviewer", "Review", "sonnet")

            # Write some test data
            agent.output_file.write_text("Line 1\nLine 2\nLine 3\n")

            output = controller.capture_output("reviewer", lines=2)
            assert "Line 2" in output
            assert "Line 3" in output

    def test_capture_output_nonexistent_agent(self):
        """Test capturing output from non-existent agent returns empty string."""
        controller = AgentController()
        output = controller.capture_output("nonexistent")
        assert output == ""

    def test_is_agent_running(self):
        """Test checking if agent is running."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"
            controller = AgentController(output_dir=output_dir)

            controller.spawn_agent("manager", "Manage", "opus")

            # In current implementation, process is None so not running
            assert controller.is_agent_running("manager") is False

    def test_list_agents(self):
        """Test listing all agents."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"
            controller = AgentController(output_dir=output_dir)

            controller.spawn_agent("agent1", "Task 1", "sonnet")
            controller.spawn_agent("agent2", "Task 2", "opus")
            controller.spawn_agent("agent3", "Task 3", "sonnet")

            agents = controller.list_agents()
            assert len(agents) == 3
            assert all(isinstance(a, AgentProcess) for a in agents)

    def test_kill_all(self):
        """Test killing all agents."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"
            controller = AgentController(output_dir=output_dir)

            controller.spawn_agent("agent1", "Task 1", "sonnet")
            controller.spawn_agent("agent2", "Task 2", "opus")

            controller.kill_all()
            # Agents still in dict but killed
            assert len(controller.agents) == 2

    def test_cleanup(self):
        """Test cleanup removes all agents."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"
            controller = AgentController(output_dir=output_dir)

            controller.spawn_agent("agent1", "Task 1", "sonnet")
            controller.spawn_agent("agent2", "Task 2", "opus")

            controller.cleanup()
            assert len(controller.agents) == 0


class TestAgentProcess:
    """Tests for AgentProcess dataclass."""

    def test_agent_process_creation(self):
        """Test creating an AgentProcess."""
        import time

        agent = AgentProcess(
            role="tester",
            task_id="test-123",
            working_dir=Path("/tmp"),
            output_file=Path("/tmp/output.log"),
            started_at=time.time()
        )

        assert agent.role == "tester"
        assert agent.task_id == "test-123"
        assert agent.is_running is False

    def test_duration_seconds(self):
        """Test calculating duration."""
        import time

        start = time.time()
        agent = AgentProcess(
            role="test",
            task_id="123",
            working_dir=Path("/tmp"),
            output_file=Path("/tmp/out.log"),
            started_at=start
        )

        time.sleep(0.1)
        duration = agent.duration_seconds
        assert duration >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
