# Code Review Team

## Purpose

Parallel code review with specialized reviewers examining different quality dimensions simultaneously. Each reviewer operates independently, producing findings that the lead synthesizes into a comprehensive review.

## Team Composition

| Role | Focus | Model | Plan Approval |
|------|-------|-------|---------------|
| Security Reviewer | Vulnerabilities, auth, secrets, injection | sonnet | No |
| Performance Analyst | Complexity, queries, memory, caching | sonnet | No |
| Test Coverage Checker | Coverage gaps, edge cases, test quality | sonnet | No |

## Workflow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Security     │     │   Performance   │     │  Test Coverage  │
│    Reviewer     │     │    Analyst      │     │    Checker      │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────┐
                    │   Lead Synthesizes  │
                    │   Final Review      │
                    └─────────────────────┘
```

**Key**: No task dependencies. All reviewers work in parallel on the same code.

## Best Use Cases

- Pull request reviews
- Pre-merge quality gates
- Security audits
- Code quality assessments
- Module reviews before refactoring

## Anti-patterns (When NOT to Use)

- Simple typo fixes
- Documentation-only changes
- Single-file changes under 50 lines
- Urgent hotfixes (use single session)

## Expected Output

Consolidated review document with:
- Categorized findings by severity (Critical/High/Medium/Low)
- Specific file and line references
- Remediation suggestions with code
- Overall approval/rejection recommendation

## Customization Options

### Add More Reviewers
- **Accessibility Reviewer**: WCAG compliance, screen reader support
- **Documentation Reviewer**: API docs, README, inline comments
- **Architecture Reviewer**: Design patterns, coupling, SOLID principles

### Scope Limiting
Add to spawn prompt:
```
Focus only on files changed in this PR: {{FILE_LIST}}
```

### Severity Thresholds
Add to spawn prompt:
```
Block on Critical/High findings only. Medium/Low are advisory.
```
