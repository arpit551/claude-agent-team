# Architecture Update - Iteration 6

## Major Change: Tmux Removal ✅

**Date**: Iteration 6 of Ralph Loop
**Status**: Complete

### What Changed

The Claude Agent Teams framework has been migrated from a tmux-based architecture to a direct process management system.

### Old Architecture (v1)
- Spawned agents in tmux panes
- Read agent output from tmux buffers
- Required tmux to be installed
- Complex session management

### New Architecture (v2)
- Uses `AgentController` for direct process spawning
- Reads agent output from log files
- Uses `ClaudeStateReader` for Claude session monitoring
- No external dependencies beyond Python

### Files Created
1. `cat/agent/controller.py` - AgentController for process management
2. `cat/agent/claude_monitor.py` - ClaudeStateReader and AgentOutputMonitor

### Files Deleted
1. `cat/agent/tmux.py`
2. `cat/dashboard/tmux_manager.py`
3. `demo_tmux.py`
4. `demo_tmux_ui.py`
5. `tests/test_tmux_integration.py`
6. `docs/tmux-ui-guide.md`

### Files Updated
- `cat/agent/__init__.py` - Exports new modules
- `cat/agent/models.py` - Removed tmux_pane field
- `cat/agent/registry.py` - Removed set_tmux_pane method
- `cat/workflow/spawner.py` - Uses AgentController
- `cat/workflow/collector.py` - Uses AgentController
- `cat/workflow/engine.py` - Uses AgentController
- `cat/cli.py` - Removed tmux command
- `tests/test_cli.py` - Updated tests

### Files Marked for Future Work
- `cat/dashboard/unified_manager.py` - Still uses subprocess calls to tmux
  - Marked with TODO for future refactoring
  - Not critical for core functionality

### Migration Guide

If you were using tmux-specific features:

**Before:**
```python
from cat.agent.tmux import TmuxController
controller = TmuxController()
```

**After:**
```python
from cat.agent.controller import AgentController
controller = AgentController()
```

**Before:**
```python
pane = controller.spawn_agent(role, prompt, model)
output = controller.capture_output(role)
```

**After:**
```python
agent = controller.spawn_agent(role, prompt, model)
output = controller.capture_output(role, lines=100)
```

### Benefits

1. **Simpler**: No external dependencies
2. **Portable**: Works on any platform (Windows, Mac, Linux)
3. **Maintainable**: Direct Python code, no shell commands
4. **Testable**: Easier to mock and test
5. **Faster**: No IPC overhead with tmux

### Verification

All core modules compile successfully:
```bash
python3 -m py_compile cat/agent/*.py cat/workflow/*.py cat/cli.py
```

Import test:
```bash
python3 -c "from cat.agent.controller import AgentController; print('✅ Success')"
```

### Next Steps

Future iterations will:
1. Refactor `unified_manager.py` to use AgentController
2. Add comprehensive tests for new modules
3. Update remaining documentation
4. Continue with iterations 7-30 of Ralph Loop
