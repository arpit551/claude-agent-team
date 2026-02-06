"""Pytest configuration and fixtures."""

import pytest
import tempfile
from pathlib import Path


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_config():
    """Sample project configuration for testing."""
    return {
        "name": "test-project",
        "description": "Test project description",
        "use_case": "build_feature",
        "agents": {
            "researcher": {
                "role": "researcher",
                "model": "opus",
                "enabled": True,
                "depends_on": [],
                "max_iterations": 40,
            }
        },
        "output_dir": ".catt/output",
        "max_total_iterations": 200,
    }


@pytest.fixture
def sample_tasks():
    """Sample tasks for testing."""
    from cat.data.models import Task, TaskStatus

    return [
        Task(
            id="1",
            content="Design architecture",
            active_form="Designing architecture",
            status=TaskStatus.PENDING,
            progress=0
        ),
        Task(
            id="2",
            content="Implement feature",
            active_form="Implementing feature",
            status=TaskStatus.IN_PROGRESS,
            progress=50
        ),
        Task(
            id="3",
            content="Write tests",
            active_form="Writing tests",
            status=TaskStatus.COMPLETED,
            progress=100
        ),
    ]
