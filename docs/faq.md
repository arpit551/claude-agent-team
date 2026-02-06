# Frequently Asked Questions (FAQ)

## Installation & Setup

### Q: Where do I install the settings.json file?

The settings file should be created at `~/.claude/settings.json` (your home directory). The full path looks like:
- macOS/Linux: `/Users/yourname/.claude/settings.json`
- Windows: `C:\Users\yourname\.claude\settings.json`

You can also create project-specific settings at `.claude/settings.json` in your project root.

### Q: Do I need to install tmux?

Yes, tmux is required for spawning multiple agents. Install it with:
```bash
# macOS
brew install tmux

# Ubuntu/Debian
sudo apt install tmux

# Fedora
sudo dnf install tmux
```

### Q: I get "tmux is not installed" error

Make sure tmux is installed and available in your PATH. Test with:
```bash
which tmux
```

If tmux is installed but not found, add it to your PATH or specify the full path in your shell configuration.

## Configuration

### Q: How do I enable agent teams?

Add this to your `~/.claude/settings.json`:
```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

Restart Claude Code after making this change.

### Q: Can I customize which agents are used?

Yes! Edit `.catt/project.yaml` after running `catt init`. You can:
- Enable/disable specific agents
- Change models (opus vs sonnet)
- Modify dependencies between agents
- Set max iterations per agent
- Add custom prompts

Example:
```yaml
agents:
  developer:
    role: developer
    model: sonnet
    enabled: true
    depends_on: [architect]
    max_iterations: 40
```

### Q: What's the difference between opus and sonnet?

- **Opus**: Best for complex reasoning tasks (research, architecture, planning). More expensive but more capable.
- **Sonnet**: Fast and efficient for implementation tasks. Great for coding, testing, and reviews.

Use opus for thinking, sonnet for doing.

## Usage

### Q: How do I start a new project?

```bash
cd your-project
catt init
```

Follow the interactive wizard to configure your team.

### Q: Can I resume a stopped workflow?

Yes, use the `--resume` flag:
```bash
catt run --resume
```

This will continue from where the workflow was interrupted.

### Q: How do I see what will happen before running?

Use the dry-run flag:
```bash
catt run --dry-run
```

This shows the execution plan and team creation prompt without actually running agents.

### Q: How do I monitor agent progress?

Launch the dashboard in a separate terminal:
```bash
catt dashboard
```

Or use the kanban view:
```bash
catt tasks --kanban
```

### Q: Can agents work in parallel?

Yes! Agents with no dependencies run in parallel. For example, in a code review team, security, performance, and test coverage reviewers all run simultaneously.

Configure dependencies in your project.yaml to control execution order.

## Troubleshooting

### Q: Dashboard shows no tasks

This is normal if:
- You haven't created any tasks yet
- You're in a new project
- Task files are in a non-standard location

To see tasks, you need to either:
1. Have Claude Code create tasks in `~/.claude/todos/`
2. Use `catt run` to start a workflow that creates tasks

### Q: "No project configuration found" error

You need to run `catt init` first:
```bash
cd your-project
catt init
```

This creates `.catt/project.yaml` with your project configuration.

### Q: Agents are not spawning

Check:
1. Is tmux installed? (`which tmux`)
2. Is the experimental flag enabled in settings.json?
3. Is Claude Code CLI installed? (`which claude`)
4. Do you have valid API credentials?

### Q: Dashboard is blank or shows "Progress"

This can happen if:
- The terminal is too small (resize to at least 80x24)
- Tasks haven't loaded yet (press 'r' to refresh)
- No task files exist yet

## Performance

### Q: How many agents can I run at once?

This depends on your machine and API rate limits. We recommend:
- Start with 3-5 agents for most projects
- Use parallel teams (code review) for independent tasks
- Use sequential teams (development) for dependent tasks

### Q: How do I reduce API costs?

1. Use sonnet for implementation tasks (cheaper than opus)
2. Reduce max_iterations per agent
3. Disable agents you don't need
4. Use smaller teams for simple tasks

## Integration

### Q: Can I use this with my existing project?

Yes! Just run `catt init` in your project directory. The framework works with any codebase.

### Q: Does this work with GitHub Actions?

Not yet, but you can:
1. Run `catt run` locally
2. Review the output
3. Commit changes normally

CI/CD integration is planned for a future release.

### Q: Can I create custom roles?

Yes! Create a new file in `roles/` directory:
```markdown
# roles/my-custom-role.md

You are a custom agent role.

## Responsibilities
- Task 1
- Task 2

## File Ownership
- Own files in src/custom/
```

Then reference it in your project.yaml.

## Best Practices

### Q: When should I use agent teams vs. working directly?

Use agent teams when:
- Building new features from scratch
- Need multiple perspectives (architecture, security, performance)
- Want to parallelize work
- Working on complex, multi-step tasks

Work directly when:
- Making small bug fixes
- Quick one-line changes
- Debugging specific issues
- Learning the codebase

### Q: How do I structure tasks for agents?

Good task structure:
- Clear, actionable goals
- Well-defined scope
- Proper dependencies
- Reasonable time estimates (15-45 minutes per task)

Bad task structure:
- Vague goals ("make it better")
- Too large (multi-hour tasks)
- Missing context
- No clear completion criteria

### Q: Should I review agent output?

**Always** review agent-generated code before committing! Agents are powerful but not perfect. Check for:
- Security issues
- Performance problems
- Edge cases
- Test coverage
- Documentation

## Advanced

### Q: Can I use different models for different agents?

Yes! Each agent in project.yaml can specify its own model:
```yaml
agents:
  architect:
    model: opus  # Complex reasoning
  developer:
    model: sonnet  # Fast implementation
```

### Q: How do I add custom context to agents?

Use the `custom_prompt` field in project.yaml:
```yaml
agents:
  developer:
    role: developer
    custom_prompt: |
      Additional context:
      - Use TypeScript strict mode
      - Follow the existing patterns in src/
```

### Q: Can agents communicate with each other?

Yes! When using Claude Code's agent teams feature, agents can:
- Share a task list
- Message each other
- See each other's output
- Coordinate work through the lead agent

This is handled automatically by the tmux-based spawning system.

## Getting Help

### Q: Where do I report bugs?

Open an issue on GitHub with:
- What you expected to happen
- What actually happened
- Steps to reproduce
- Your config file (remove sensitive info)
- Error messages

### Q: How do I request features?

Open a GitHub issue with the "enhancement" label and describe:
- The use case
- Why it's valuable
- Proposed implementation (optional)

### Q: Where can I find examples?

Check:
- `teams/` directory for team templates
- `roles/` directory for role templates
- Documentation in `docs/`
- README.md for quick start guide
