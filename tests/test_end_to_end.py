"""End-to-end integration tests.

These tests verify the complete workflow from init to run.
"""

import pytest
import tempfile
import os
from pathlib import Path
from typer.testing import CliRunner

from cat.cli import app

runner = CliRunner()


class TestEndToEnd:
    """End-to-end workflow tests."""

    def test_complete_workflow_dry_run(self):
        """Test a complete workflow in dry-run mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)

                # Step 1: Initialize project
                result_init = runner.invoke(app, ["init", "--no-interactive"])
                assert result_init.exit_code == 0
                assert Path(".catt/project.yaml").exists()

                # Step 2: Run dry-run
                result_run = runner.invoke(app, ["run", "--dry-run"])
                assert result_run.exit_code == 0
                assert "Execution Plan" in result_run.stdout

                # Step 3: Check agent list
                result_agents = runner.invoke(app, ["agent", "list"])
                assert result_agents.exit_code == 0
                assert "researcher" in result_agents.stdout.lower() or "Researcher" in result_agents.stdout

                # Step 4: View tasks (should handle empty gracefully)
                result_tasks = runner.invoke(app, ["tasks"])
                assert result_tasks.exit_code == 0

            finally:
                os.chdir(original_cwd)

    def test_custom_config_workflow(self):
        """Test workflow with custom configuration."""
        import yaml

        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)

                # Create custom config
                config_dir = Path(".catt")
                config_dir.mkdir()

                custom_config = {
                    "name": "custom-test",
                    "description": "Custom test project",
                    "use_case": "build_feature",
                    "agents": {
                        "developer": {
                            "role": "developer",
                            "model": "sonnet",
                            "enabled": True,
                            "depends_on": [],
                            "max_iterations": 20,
                            "file_ownership": ["src/"],
                            "custom_prompt": "Focus on clean code",
                        }
                    },
                    "output_dir": ".catt/output",
                    "max_total_iterations": 100,
                }

                config_path = config_dir / "project.yaml"
                with open(config_path, "w") as f:
                    yaml.dump(custom_config, f)

                # Run dry-run with custom config
                result = runner.invoke(app, ["run", "--dry-run"])
                assert result.exit_code == 0
                assert "custom-test" in result.stdout.lower()
                assert "Developer" in result.stdout or "developer" in result.stdout

            finally:
                os.chdir(original_cwd)

    def test_team_templates_accessible(self):
        """Test that all team templates are accessible."""
        team_names = ["dev", "review", "research", "manager", "software"]

        for team in team_names:
            result = runner.invoke(app, ["team", "spawn", team])
            assert result.exit_code == 0, f"Team {team} failed"
            assert "Spawn Prompt" in result.stdout

    def test_stats_command_handles_no_data(self):
        """Test that stats command handles missing data gracefully."""
        result = runner.invoke(app, ["stats"])
        # Should not crash even with no data
        assert result.exit_code == 0

    def test_init_in_existing_project(self):
        """Test initializing in a directory with existing files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)

                # Create some existing files
                Path("README.md").write_text("# Existing Project")
                Path("src").mkdir()
                Path("src/main.py").write_text("print('hello')")

                # Initialize
                result = runner.invoke(app, ["init", "--no-interactive"])
                assert result.exit_code == 0

                # Verify existing files not touched
                assert Path("README.md").exists()
                assert Path("src/main.py").exists()

                # Verify config created
                assert Path(".catt/project.yaml").exists()

            finally:
                os.chdir(original_cwd)


class TestWorkflowEdgeCases:
    """Test edge cases in workflows."""

    def test_run_without_init(self):
        """Test running without initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)

                result = runner.invoke(app, ["run"])
                assert result.exit_code == 1
                assert "No project configuration" in result.stdout

            finally:
                os.chdir(original_cwd)

    def test_dashboard_with_no_todos(self):
        """Test dashboard when no todos exist (should not crash)."""
        # This is a smoke test - dashboard should initialize even with no data
        # We can't easily test the interactive UI, but we can verify it doesn't crash on import
        from cat.dashboard.app import DashboardApp

        app = DashboardApp(watch=False)
        assert app is not None

    def test_multiple_inits(self):
        """Test running init multiple times."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)

                # First init
                result1 = runner.invoke(app, ["init", "--no-interactive"])
                assert result1.exit_code == 0

                # Second init (should succeed or handle gracefully)
                result2 = runner.invoke(app, ["init", "--no-interactive"])
                # Should either succeed or give a clear error
                assert result2.exit_code in [0, 1]

            finally:
                os.chdir(original_cwd)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
