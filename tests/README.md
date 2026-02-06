# Tests

Integration and unit tests for the Claude Agent Teams CLI.

## Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=cat --cov-report=html

# Run specific test file
pytest tests/test_cli.py

# Run with verbose output
pytest -v

# Run specific test
pytest tests/test_cli.py::TestInit::test_init_no_interactive_creates_config
```

## Test Structure

- `test_cli.py` - Integration tests for CLI commands
- `test_dashboard.py` - Tests for dashboard components
- `conftest.py` - Pytest fixtures and configuration

## Test Coverage

The tests cover:
- CLI command execution
- Configuration creation and loading
- Task data models and parsing
- Dashboard widget initialization
- Tmux controller basics
- Error handling and edge cases

## Adding New Tests

When adding new features, please add corresponding tests:

1. For CLI commands, add tests to `test_cli.py`
2. For dashboard components, add tests to `test_dashboard.py`
3. For data models, add tests to appropriate test file
4. Use fixtures from `conftest.py` for common test data

## Continuous Integration

These tests should be run in CI/CD pipelines before merging PRs.
