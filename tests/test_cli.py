"""Integration tests for CLI commands."""

import json
import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from cat.cli import app

runner = CliRunner()


class TestInit:
    """Tests for catt init command."""

    def test_init_no_interactive_creates_config(self):
        """Test that init --no-interactive creates a default config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(
                app,
                ["init", "--no-interactive", "--dir", tmpdir]
            )
            assert result.exit_code == 0
            assert "✓" in result.stdout
            assert "config saved" in result.stdout

            config_path = Path(tmpdir) / ".catt" / "project.yaml"
            assert config_path.exists()

    def test_init_creates_catt_directory(self):
        """Test that init creates .catt directory structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner.invoke(
                app,
                ["init", "--no-interactive", "--dir", tmpdir]
            )

            catt_dir = Path(tmpdir) / ".catt"
            assert catt_dir.exists()
            assert catt_dir.is_dir()


class TestTeam:
    """Tests for catt team commands."""

    def test_team_list_shows_templates(self):
        """Test that team list shows available templates."""
        result = runner.invoke(app, ["team", "list"])
        assert result.exit_code == 0
        assert "code-review" in result.stdout or "code-revi" in result.stdout
        assert "development" in result.stdout or "developme" in result.stdout

    def test_team_spawn_shows_prompt(self):
        """Test that team spawn shows spawn prompt."""
        result = runner.invoke(app, ["team", "spawn", "dev"])
        assert result.exit_code == 0
        assert "Spawn Prompt" in result.stdout
        assert "development" in result.stdout.lower()


class TestAgent:
    """Tests for catt agent commands."""

    def test_agent_list_with_config(self):
        """Test agent list command with a config file."""
        import os
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create config first
            runner.invoke(
                app,
                ["init", "--no-interactive", "--dir", tmpdir]
            )

            # Change to that directory and run agent list
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                result = runner.invoke(app, ["agent", "list"])
                assert result.exit_code == 0
                # Should show agent table with roles
                assert "Role" in result.stdout or "researcher" in result.stdout.lower()
            finally:
                os.chdir(original_cwd)


class TestTasks:
    """Tests for catt tasks commands."""

    def test_tasks_without_todos_dir(self):
        """Test tasks command when no todos directory exists."""
        result = runner.invoke(app, ["tasks"])
        # Should not crash, just show empty or handle gracefully
        assert result.exit_code == 0

    def test_tasks_kanban_mode(self):
        """Test tasks command with kanban flag."""
        result = runner.invoke(app, ["tasks", "--kanban"])
        assert result.exit_code == 0
        # Should show kanban columns
        assert "TODO" in result.stdout or "IN PROGRESS" in result.stdout or "DONE" in result.stdout


class TestRun:
    """Tests for catt run command."""

    def test_run_without_config_fails(self):
        """Test that run fails gracefully without config."""
        import os
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                result = runner.invoke(app, ["run"])
                assert result.exit_code == 1
                assert "No project configuration" in result.stdout
            finally:
                os.chdir(original_cwd)

    def test_run_dry_run_shows_plan(self):
        """Test that run --dry-run shows execution plan."""
        import os
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create config first
            runner.invoke(
                app,
                ["init", "--no-interactive", "--dir", tmpdir]
            )

            # Change to that directory and run dry-run
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                result = runner.invoke(app, ["run", "--dry-run"])
                assert result.exit_code == 0
                assert "Execution Plan" in result.stdout
                assert "Dry run" in result.stdout
            finally:
                os.chdir(original_cwd)


class TestDataModels:
    """Tests for data models."""

    def test_task_from_dict_handles_none_content(self):
        """Test that Task.from_dict handles None content gracefully."""
        from cat.data.models import Task

        data = {
            "status": "pending",
            "content": None,
            "activeForm": None
        }

        task = Task.from_dict(data, "test-1")
        assert task.content == ""
        assert task.active_form == ""

    def test_task_from_dict_uses_actual_progress(self):
        """Test that Task.from_dict uses actual progress when provided."""
        from cat.data.models import Task

        data = {
            "status": "in_progress",
            "content": "Test task",
            "activeForm": "Testing",
            "progress": 75
        }

        task = Task.from_dict(data, "test-1")
        assert task.progress == 75

    def test_task_from_dict_defaults_progress_by_status(self):
        """Test that Task.from_dict defaults progress based on status."""
        from cat.data.models import Task

        # Pending task
        data_pending = {"status": "pending", "content": "Test"}
        task_pending = Task.from_dict(data_pending, "test-1")
        assert task_pending.progress == 0

        # In progress task
        data_in_progress = {"status": "in_progress", "content": "Test"}
        task_in_progress = Task.from_dict(data_in_progress, "test-2")
        assert task_in_progress.progress == 50

        # Completed task
        data_completed = {"status": "completed", "content": "Test"}
        task_completed = Task.from_dict(data_completed, "test-3")
        assert task_completed.progress == 100


class TestTmuxController:
    """Tests for TmuxController."""

    def test_tmux_controller_initialization(self):
        """Test that TmuxController initializes without tmux installed."""
        from cat.agent.tmux import TmuxController
        import shutil

        # Only test if tmux is not installed
        if not shutil.which("tmux"):
            with pytest.raises(RuntimeError, match="tmux is not installed"):
                TmuxController()

    def test_tmux_session_name_default(self):
        """Test that TmuxController uses default session name."""
        from cat.agent.tmux import TmuxController
        import shutil

        # Only test if tmux is installed
        if shutil.which("tmux"):
            controller = TmuxController()
            assert controller.session == "catt-agents"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
