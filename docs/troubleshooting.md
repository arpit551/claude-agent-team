# Troubleshooting Guide

## Installation Issues

### tmux not found

**Error:**
```
RuntimeError: tmux is not installed
```

**Solution:**
```bash
# macOS
brew install tmux

# Ubuntu/Debian
sudo apt install tmux

# Fedora/RHEL
sudo dnf install tmux

# Verify installation
which tmux
tmux -V
```

### Claude Code CLI not found

**Error:**
```
claude: command not found
```

**Solution:**
1. Install Claude Code from https://claude.ai/code
2. Verify installation: `which claude`
3. If installed but not in PATH, add to your shell config:
   ```bash
   export PATH="$PATH:/path/to/claude"
   ```

### Python version issues

**Error:**
```
Python 3.10+ required
```

**Solution:**
```bash
# Check your Python version
python3 --version

# Install Python 3.10+ using pyenv
pyenv install 3.11.0
pyenv local 3.11.0

# Or use system package manager
brew install python@3.11  # macOS
```

### CATT command not found after pip install

**Error:**
```
catt: command not found
```

**Solution:**
```bash
# Make sure you installed in editable mode
pip install -e .

# Or reinstall
pip uninstall catt
pip install -e .

# Check if it's in your PATH
which catt

# If using virtual environment, activate it
source .venv/bin/activate
```

---

## Common Issues

### Teammates Not Appearing

**Symptom**: Asked for a team but no teammates visible.

**Solutions**:
1. Press **Shift+Down** to cycle through teammates (in-process mode)
2. Check if task warranted a team (Claude may have decided single session)
3. Verify agent teams are enabled:
   ```bash
   # Check settings
   cat ~/.claude/settings.json | grep AGENT_TEAMS
   ```
4. For split-pane mode, verify tmux is installed: `which tmux`
5. For iTerm2, check `it2` CLI and Python API enabled

---

### Agent Teams Not Enabled

**Symptom**: Claude doesn't understand team commands.

**Solution**: Enable in settings.json:
```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

Then restart Claude Code.

---

### Permission Prompts Flooding

**Symptom**: Constant permission requests interrupting work.

**Solution**: Pre-approve operations in settings.json:
```json
{
  "permissions": {
    "allow": [
      "Read",
      "Glob",
      "Grep",
      "Bash(git status)",
      "Bash(git diff *)",
      "Bash(git log *)",
      "Bash(npm test)",
      "Bash(npm run *)"
    ]
  }
}
```

---

### Task Stuck in Progress

**Symptom**: Task shows "in progress" but teammate appears idle.

**Solutions**:
1. Check teammate directly (Shift+Up/Down, select, Enter)
2. Tell lead: "Check on Task #N status"
3. If complete, tell lead: "Mark Task #N as completed"
4. If truly stuck, ask: "What's blocking Task #N?"

---

### Edit Conflicts

**Symptom**: Teammate overwrote another's changes.

**Prevention**:
- Assign file ownership in spawn prompts
- Use task dependencies for shared files
- Never have two teammates own the same directory

**Recovery**:
```bash
# See what changed
git diff HEAD~1

# Restore if needed
git checkout HEAD~1 -- path/to/file

# Or use git stash
git stash
git stash pop
```

---

### Lead Implementing Instead of Delegating

**Symptom**: Lead starts coding instead of coordinating.

**Solutions**:
1. Enable delegate mode: Press **Shift+Tab**
2. Tell lead: "Do not implement directly. Delegate all work to teammates."
3. Add to initial prompt: "Enable delegate mode - coordinate only"

---

### Teammate Crashed Mid-Task

**Symptom**: Teammate no longer responding, task incomplete.

**Recovery**:
1. Note the task and progress made
2. Tell lead: "Spawn a replacement for [role]"
3. Provide context: "They were working on Task #N, completed X but not Y"
4. Assign incomplete task to replacement

---

### Session Resume Fails

**Symptom**: After `/resume`, lead messages non-existent teammates.

**Limitation**: Agent teams don't fully support session resumption.

**Solution**: Tell lead: "Previous teammates are gone. Spawn new teammates to continue."

---

### Orphaned tmux Sessions

**Symptom**: tmux sessions persist after team ends.

**Solution**:
```bash
# List sessions
tmux ls

# Kill specific session
tmux kill-session -t <session-name>

# Nuclear option: kill all
tmux kill-server
```

---

### Teammates Not Communicating

**Symptom**: Teammates work in isolation, don't share findings.

**Solution**: Add to spawn prompts:
```
Share findings with other teammates directly.
Coordinate on shared concerns via messages.
```

Or explicitly instruct: "Have teammates debate before synthesizing."

---

## Diagnostic Commands

### Check Configuration
```bash
# View settings
cat ~/.claude/settings.json

# Check if agent teams enabled
grep -r "AGENT_TEAMS" ~/.claude/

# View team configs (if any exist)
ls ~/.claude/teams/
cat ~/.claude/teams/*/config.json

# View task lists
ls ~/.claude/tasks/
```

### Check Environment
```bash
# Verify tmux
which tmux
tmux -V

# Check for orphaned sessions
tmux ls

# Check Claude Code process
ps aux | grep claude
```

### During Session
```
# In Claude Code:
Ctrl+T        # Toggle task list
Shift+Up/Down # Navigate teammates
Shift+Tab     # Toggle delegate mode

# Ask lead for status:
"What's the status of all teammates?"
"Show me the task list"
"Which tasks are blocked?"
```

---

## Known Limitations

1. **No session resumption**: `/resume` doesn't restore teammates
2. **Task status lag**: Teammates may not mark tasks complete
3. **Slow shutdown**: Teammates finish current work before stopping
4. **One team per session**: Clean up before starting new team
5. **No nested teams**: Teammates can't spawn their own teams
6. **Fixed lead**: Can't transfer leadership
7. **Split panes limited**: Only works with tmux or iTerm2

---

## Getting Help

If issues persist:

1. Check [official documentation](https://code.claude.com/docs/en/agent-teams)
2. Note error message and steps to reproduce
3. Try fresh session: exit and restart Claude Code
4. Report issues at [github.com/anthropics/claude-code/issues](https://github.com/anthropics/claude-code/issues)
