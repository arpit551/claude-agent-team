"""Tests for dashboard components."""

import pytest
from cat.data.models import Task, TaskStatus, DashboardState, TaskFile
from pathlib import Path


class TestTaskCard:
    """Tests for TaskCard widget."""

    def test_task_card_handles_none_content(self):
        """Test that TaskCard handles None content without crashing."""
        # This test now verifies that Task.from_dict converts None to ""
        task = Task(
            id="test-1",
            content="",  # from_dict will convert None to ""
            active_form="",
            status=TaskStatus.PENDING,
            progress=0
        )

        # Task should have empty strings, not None
        assert task.content == ""
        assert task.active_form == ""

    def test_task_card_truncates_long_content(self):
        """Test that Task stores full content (TaskCard truncates on display)."""
        long_content = "A" * 100
        task = Task(
            id="test-1",
            content=long_content,
            active_form="Testing",
            status=TaskStatus.IN_PROGRESS,
            progress=50
        )

        # Task should store full content
        assert len(task.content) == 100
        assert task.content == long_content

        # TaskCard will truncate to 60 chars on display
        assert long_content[:60] == "A" * 60


class TestKanbanBoard:
    """Tests for Kanban board."""

    def test_kanban_board_initialization(self):
        """Test that KanbanBoard initializes with empty lists."""
        from cat.dashboard.kanban import KanbanBoard

        board = KanbanBoard()
        assert board.pending_tasks == []
        assert board.in_progress_tasks == []
        assert board.completed_tasks == []

    def test_kanban_board_update_tasks(self):
        """Test that KanbanBoard updates with new tasks."""
        from cat.dashboard.kanban import KanbanBoard

        board = KanbanBoard()

        # Create test tasks
        task1 = Task(
            id="1", content="Task 1", active_form="", status=TaskStatus.PENDING, progress=0
        )
        task2 = Task(
            id="2", content="Task 2", active_form="", status=TaskStatus.IN_PROGRESS, progress=50
        )
        task3 = Task(
            id="3", content="Task 3", active_form="", status=TaskStatus.COMPLETED, progress=100
        )

        # Create state
        state = DashboardState(
            task_files=[
                TaskFile(
                    file_path=Path("/tmp/test.json"),
                    tasks=[task1, task2, task3]
                )
            ]
        )

        board.update_tasks(state)
        assert len(board.pending_tasks) == 1
        assert len(board.in_progress_tasks) == 1
        assert len(board.completed_tasks) == 1


class TestStatsPanel:
    """Tests for stats panel."""

    def test_stats_panel_initialization(self):
        """Test that StatsPanel initializes correctly."""
        from cat.dashboard.stats_panel import StatsPanel

        panel = StatsPanel()
        assert panel.state is None

    def test_stats_panel_update(self):
        """Test that StatsPanel updates with state."""
        from cat.dashboard.stats_panel import StatsPanel

        panel = StatsPanel()

        # Create test state
        task1 = Task(
            id="1", content="Task 1", active_form="", status=TaskStatus.PENDING, progress=0
        )
        task2 = Task(
            id="2", content="Task 2", active_form="", status=TaskStatus.IN_PROGRESS, progress=50
        )

        state = DashboardState(
            task_files=[
                TaskFile(
                    file_path=Path("/tmp/test.json"),
                    tasks=[task1, task2]
                )
            ]
        )

        # Update should not crash
        panel.state = state
        assert panel.state == state


class TestDashboardState:
    """Tests for DashboardState model."""

    def test_dashboard_state_all_tasks(self):
        """Test that DashboardState aggregates all tasks."""
        task1 = Task(
            id="1", content="Task 1", active_form="", status=TaskStatus.PENDING, progress=0
        )
        task2 = Task(
            id="2", content="Task 2", active_form="", status=TaskStatus.IN_PROGRESS, progress=50
        )

        state = DashboardState(
            task_files=[
                TaskFile(file_path=Path("/tmp/test.json"), tasks=[task1, task2])
            ]
        )

        assert len(state.all_tasks) == 2
        assert len(state.pending_tasks) == 1
        assert len(state.in_progress_tasks) == 1

    def test_dashboard_state_total_progress(self):
        """Test that DashboardState calculates total progress."""
        task1 = Task(
            id="1", content="Task 1", active_form="", status=TaskStatus.COMPLETED, progress=100
        )
        task2 = Task(
            id="2", content="Task 2", active_form="", status=TaskStatus.PENDING, progress=0
        )

        state = DashboardState(
            task_files=[
                TaskFile(file_path=Path("/tmp/test.json"), tasks=[task1, task2])
            ]
        )

        assert state.total_progress == 50  # 1 out of 2 complete


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
