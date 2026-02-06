"""
Integration tests for workflow engine - Iteration 15.

Focus on testing new features added in iterations 8-14:
- Watcher integration
- MessageBus integration
- ProgressTracker integration
- Performance monitoring
- Error handling
"""

import pytest
import tempfile
import time
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from cat.workflow.engine import WorkflowEngine
from cat.workflow.spawner import AgentSpawner
from cat.workflow.collector import OutputCollector
from cat.workflow.watcher import OutputWatcher
from cat.workflow.messaging import MessageBus, Message, MessageType
from cat.workflow.progress import ProgressTracker
from cat.workflow.performance import PerformanceMonitor
from cat.agent.models import AgentRole, AgentStatus, AgentConfig, ModelType
from cat.agent.controller import AgentController
from cat.agent.registry import AgentRegistry
from cat.interactive.config import ProjectConfig


class TestWorkflowEngineIntegration:
    """Test the complete workflow engine with new features."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            # Create .catt directory structure
            config_dir = workspace / ".catt"
            config_dir.mkdir(parents=True)
            (config_dir / "output").mkdir(parents=True)
            (config_dir / "messages").mkdir(parents=True)
            (config_dir / "logs").mkdir(parents=True)
            yield workspace

    @pytest.fixture
    def project_config(self, temp_workspace):
        """Create a project configuration."""
        config = ProjectConfig(
            name="test-project",
            description="Test project for integration tests",
            use_case="build_feature",
            working_dir=temp_workspace,
        )
        # Add test agents
        config.agents = {
            "researcher": AgentConfig(
                role=AgentRole.RESEARCHER,
                model=ModelType.SONNET,
            ),
            "developer": AgentConfig(
                role=AgentRole.DEVELOPER,
                model=ModelType.SONNET,
            ),
        }
        config.ensure_directories()
        return config

    @pytest.fixture
    def engine(self, project_config):
        """Create a workflow engine."""
        return WorkflowEngine(config=project_config, watch_enabled=False)

    def test_engine_initialization(self, engine, project_config):
        """Test engine initializes correctly with all new components."""
        assert engine.config == project_config
        assert engine.spawner is not None
        assert engine.collector is not None
        assert engine.controller is not None
        assert engine.registry is not None

        # New components from iteration 14
        assert engine.message_bus is not None
        assert engine.progress_tracker is not None

    def test_message_bus_integration(self, engine):
        """Test MessageBus is properly integrated."""
        assert engine.message_bus is not None
        assert engine.message_bus.message_dir.exists()

        # Test we can send a message
        msg = Message(
            from_role=AgentRole.RESEARCHER,
            to_role=AgentRole.DEVELOPER,
            msg_type=MessageType.COORDINATE,
            content="Test message",
            timestamp=datetime.now(),
        )
        engine.message_bus.send(msg)

        # Verify message was stored
        messages = engine.message_bus.get_messages(from_role=AgentRole.RESEARCHER)
        assert len(messages) > 0

    def test_progress_tracker_integration(self, engine):
        """Test ProgressTracker is properly integrated."""
        assert engine.progress_tracker is not None
        assert engine.progress_tracker.registry == engine.registry

        # Should be able to update progress
        # (actual functionality tested in unit tests)

    def test_watcher_disabled_in_test(self, engine):
        """Test watcher is disabled when watch_enabled=False."""
        assert engine.watcher is None
        assert engine.watch_enabled is False

    def test_watcher_enabled(self, project_config):
        """Test watcher is initialized when enabled."""
        engine = WorkflowEngine(config=project_config, watch_enabled=True)
        assert engine.watcher is not None
        assert engine.watch_enabled is True

        # Clean up
        engine.stop()

    def test_message_parsing_callback(self, engine, temp_workspace):
        """Test message parsing from output files."""
        output_dir = temp_workspace / ".catt" / "output"
        output_file = output_dir / "researcher-2024-01-01.log"

        # Write test output with messages
        # Note: markers must match MessageType enum values (lowercase)
        output_file.write_text("""
[finding] Found critical bug in authentication
[progress] Task 50% complete
Normal output line
[coordinate] @developer - Need your input on API design
""")

        # Parse messages
        engine._parse_output_for_messages(AgentRole.RESEARCHER, output_file)

        # Check messages were captured
        messages = engine.message_bus.get_messages(from_role=AgentRole.RESEARCHER)
        # Debug: check if any messages were captured
        all_messages = engine.message_bus._messages
        assert len(all_messages) >= 3, f"Expected at least 3 total messages, got {len(all_messages)}. Messages: {[str(m.msg_type) for m in all_messages]}"
        assert len(messages) >= 3, f"Expected at least 3 messages from RESEARCHER, got {len(messages)}"

    def test_stop_method(self, engine):
        """Test stop method cleans up properly."""
        # Should not raise
        engine.stop()

        # Verify components are stopped
        if engine.watcher and engine.watcher.use_watchdog and engine.watcher.observer:
            assert not engine.watcher.is_alive()


class TestMessageBusIntegration:
    """Test MessageBus integration in workflow."""

    @pytest.fixture
    def temp_dir(self):
        """Create temp directory for message storage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def message_bus(self, temp_dir):
        """Create a message bus."""
        return MessageBus(temp_dir / "messages")

    def test_message_storage_and_retrieval(self, message_bus):
        """Test messages are stored and can be retrieved."""
        msg = Message(
            from_role=AgentRole.RESEARCHER,
            to_role=AgentRole.DEVELOPER,
            msg_type=MessageType.FINDING,
            content="Found a bug",
            timestamp=datetime.now(),
        )

        message_bus.send(msg)

        # Retrieve messages
        messages = message_bus.get_messages(from_role=AgentRole.RESEARCHER)
        assert len(messages) == 1
        assert messages[0].content == "Found a bug"

    def test_broadcast_messages(self, message_bus):
        """Test broadcast messages (no recipient)."""
        msg = Message(
            from_role=AgentRole.RESEARCHER,
            to_role=None,  # Broadcast
            msg_type=MessageType.PROGRESS,
            content="50% complete",
            timestamp=datetime.now(),
        )

        message_bus.send(msg)
        messages = message_bus.get_messages(from_role=AgentRole.RESEARCHER)
        assert len(messages) == 1


class TestOutputWatcherIntegration:
    """Test OutputWatcher integration."""

    @pytest.fixture
    def temp_dir(self):
        """Create temp directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_watcher_initialization(self, temp_dir):
        """Test watcher initializes correctly."""
        callback_called = []

        def callback(role, path):
            callback_called.append((role, path))

        watcher = OutputWatcher(temp_dir, callback, use_watchdog=False)

        # Start watcher
        watcher.start()
        # Can't reliably test if polling thread is running

        # Stop watcher
        watcher.stop()
        # Should not raise

    def test_watcher_start_stop(self, temp_dir):
        """Test watcher start/stop lifecycle."""
        callback_called = []

        def callback(role, path):
            callback_called.append((role, path))

        watcher = OutputWatcher(temp_dir, callback, use_watchdog=False)

        # Start and stop should not raise
        watcher.start()
        watcher.stop()


class TestPerformanceMonitorIntegration:
    """Test performance monitoring integration."""

    def test_performance_benchmark(self):
        """Test performance benchmark context manager."""
        from cat.workflow.performance import Benchmark

        bench = Benchmark("test_operation")

        with bench:
            time.sleep(0.01)

        # Should have measured some time
        assert bench.elapsed > 0
        assert bench.elapsed >= 0.01


class TestErrorRecovery:
    """Test error recovery scenarios."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            config_dir = workspace / ".catt"
            config_dir.mkdir(parents=True)
            (config_dir / "output").mkdir(parents=True)
            yield workspace

    def test_handle_missing_config(self):
        """Test handling missing configuration file."""
        # Should handle gracefully
        with tempfile.TemporaryDirectory() as tmpdir:
            # No config file exists
            result = ProjectConfig.load_or_none(Path(tmpdir) / ".catt" / "catt.yaml")
            assert result is None

    def test_handle_invalid_config(self, temp_workspace):
        """Test handling invalid configuration."""
        config_file = temp_workspace / ".catt" / "catt.yaml"
        config_file.write_text("invalid: yaml: content: [[[")

        with pytest.raises(Exception):
            ProjectConfig.load(config_file)


class TestConfigurationSystem:
    """Test configuration system with new settings."""

    def test_performance_settings(self):
        """Test performance settings are loaded."""
        from cat.interactive.config import PerformanceSettings

        settings = PerformanceSettings(
            cache_enabled=True,
            cache_ttl=2.0,
            benchmark_enabled=True,
        )

        assert settings.cache_enabled is True
        assert settings.cache_ttl == 2.0
        assert settings.benchmark_enabled is True

        # Test serialization
        data = settings.to_dict()
        loaded = PerformanceSettings.from_dict(data)
        assert loaded.cache_enabled == settings.cache_enabled

    def test_watcher_settings(self):
        """Test watcher settings are loaded."""
        from cat.interactive.config import WatcherSettings

        settings = WatcherSettings(
            enabled=True,
            use_watchdog=False,
            poll_interval=1.5,
        )

        assert settings.enabled is True
        assert settings.use_watchdog is False
        assert settings.poll_interval == 1.5

        # Test serialization
        data = settings.to_dict()
        loaded = WatcherSettings.from_dict(data)
        assert loaded.poll_interval == settings.poll_interval

    def test_logging_settings(self):
        """Test logging settings are loaded."""
        from cat.interactive.config import LoggingSettings

        settings = LoggingSettings(
            level="DEBUG",
            file=".catt/logs/test.log",
            colored=False,
        )

        assert settings.level == "DEBUG"
        assert settings.colored is False

        # Test serialization
        data = settings.to_dict()
        loaded = LoggingSettings.from_dict(data)
        assert loaded.level == settings.level

    def test_workflow_settings(self):
        """Test workflow settings are loaded."""
        from cat.interactive.config import WorkflowSettings

        settings = WorkflowSettings(
            fail_fast=True,
            agent_timeout=7200,
            max_iterations=50,
        )

        assert settings.fail_fast is True
        assert settings.agent_timeout == 7200

        # Test serialization
        data = settings.to_dict()
        loaded = WorkflowSettings.from_dict(data)
        assert loaded.max_iterations == settings.max_iterations
