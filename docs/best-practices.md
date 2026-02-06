# Agent Teams Best Practices

## Task Design

### Optimal Task Sizing

| Quality | Duration | Characteristics |
|---------|----------|-----------------|
| Too Small | < 5 min | Coordination overhead exceeds benefit |
| **Optimal** | 15-45 min | Self-contained, clear deliverable |
| Too Large | > 2 hours | Risk of wasted effort, needs breaking down |

**Rule of Thumb**: If you can describe the task in one sentence with a clear completion criterion, it's the right size.

### Good Task Examples
- "Implement the login form component with email/password fields"
- "Add unit tests for UserService.createUser method"
- "Review authentication module for SQL injection vulnerabilities"

### Bad Task Examples
- "Add a comment" (too small)
- "Build the entire user management system" (too large)
- "Improve the code" (too vague)

### Task Dependencies

Use dependencies to enforce ordering:
```
Task 1: Design API schema
Task 2: Implement endpoints (blocked by Task 1)
Task 3: Write integration tests (blocked by Task 2)
```

**Warning**: Over-specifying dependencies creates bottlenecks. Only add dependencies where order truly matters.

---

## Context Management

### Spawn Prompts

Include in every spawn prompt:
1. **What** to work on (specific files, modules, scope)
2. **How** to approach it (methodology, constraints)
3. **Output** expected (deliverable format)
4. **Context** needed (tech stack, patterns, related code)

**Good Example:**
```
Spawn a backend developer with the prompt: "Implement the /api/users
endpoint following our REST conventions in src/api/. Use the existing
UserService for business logic. Output should include the route handler,
request validation, and error handling. We use Express with TypeScript
and Zod for validation."
```

**Bad Example:**
```
Spawn a developer to work on the API.
```

### CLAUDE.md

Teammates read `CLAUDE.md` automatically. Use it to provide:
- Project conventions
- File ownership rules
- Communication protocols
- Common commands

---

## Coordination

### Preventing File Conflicts

**Best Strategy**: Assign file ownership at spawn time.

```
Workers own these directories exclusively:
- Worker 1: src/features/auth/
- Worker 2: src/features/payments/
- Worker 3: tests/
```

**Fallback**: If workers must share files, use sequential task dependencies to serialize access.

### Monitoring Progress

Check in regularly:
- Press **Ctrl+T** to view task list
- Use **Shift+Up/Down** to check individual teammates
- Ask the lead: "What's the status of all teammates?"

**Warning Signs:**
- Teammate working on same task for > 30 minutes
- No task progress updates
- Teammate asking repeated questions

### Handling Stuck Teammates

1. Check their current state (Shift+Up/Down, select, Enter)
2. Provide additional context or clarification
3. If blocked on another task, manually update task status
4. As last resort, shut down and spawn replacement

---

## Token Efficiency

### When to Use Teams vs. Single Session

| Scenario | Recommendation |
|----------|----------------|
| Sequential tasks | Single session |
| Same-file edits | Single session |
| Independent modules | Agent team |
| Parallel exploration | Agent team |
| Research with debate | Agent team |

### Model Selection by Role

| Role Type | Recommended | Rationale |
|-----------|-------------|-----------|
| Architecture | Opus | Complex decisions, long-term impact |
| Research | Opus | Deep reasoning, hypothesis generation |
| Security Review | Sonnet | Pattern matching, checklist-based |
| Implementation | Sonnet | Following established patterns |
| Testing | Sonnet | Systematic coverage |
| Code Review | Sonnet | Standards checking |

### Reducing Permission Prompts

Pre-approve common operations in settings.json:
```json
{
  "permissions": {
    "allow": [
      "Read",
      "Glob",
      "Grep",
      "Bash(git status)",
      "Bash(git diff *)",
      "Bash(npm test)",
      "Bash(npm run lint)"
    ]
  }
}
```

---

## Error Recovery

### Teammate Crashed

1. Note which task they were working on
2. Spawn a replacement with same specialization
3. Assign the incomplete task to new teammate
4. Provide context about what was already attempted

### Task Status Lag

If a task appears stuck but work is done:
1. Check the actual file state
2. Tell the lead: "Task #3 is complete, please update status"
3. Dependent tasks will automatically unblock

### Lead Shuts Down Early

If the lead finishes before teammates:
```
Wait for all teammates to complete their tasks before concluding
```

### Orphaned Resources

After abnormal termination:
```bash
# List tmux sessions
tmux ls

# Kill orphaned session
tmux kill-session -t <session-name>

# Clean up team resources (in Claude)
"Clean up the team resources"
```

---

## Anti-Patterns to Avoid

### 1. Too Many Teammates
**Problem**: Coordination overhead exceeds parallelism benefit.
**Solution**: Start with 3-4 teammates, scale up only if needed.

### 2. Overlapping File Ownership
**Problem**: Edit conflicts cause lost work.
**Solution**: Explicit file ownership in spawn prompts.

### 3. Vague Spawn Prompts
**Problem**: Teammates lack context, produce wrong output.
**Solution**: Include what, how, output format, and context.

### 4. Missing Dependencies
**Problem**: Teammates start work before prerequisites complete.
**Solution**: Model the workflow, add blocking dependencies.

### 5. Unattended Execution
**Problem**: Wasted tokens on wrong approaches.
**Solution**: Check in every 15-30 minutes, redirect early.

### 6. Premature Optimization
**Problem**: Using teams for tasks a single session handles fine.
**Solution**: Start with single session; use teams for true parallelism.
