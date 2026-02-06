# Code Review Team - Spawn Prompt

Copy and customize the sections marked with `{{PLACEHOLDER}}`:

---

## Basic Spawn Prompt

```
Create an agent team to review {{TARGET}}.

Spawn three reviewers:

1. **Security Reviewer**: Focus on authentication vulnerabilities, input
   validation, secrets handling, and injection risks. Rate findings by
   severity (Critical/High/Medium/Low).

2. **Performance Analyst**: Analyze algorithmic complexity, database query
   efficiency, memory usage, and caching opportunities. Quantify impact
   where possible.

3. **Test Coverage Checker**: Evaluate test completeness, edge case
   coverage, and test quality. Identify untested code paths with specific
   test recommendations.

Use Sonnet for all reviewers.

Have each reviewer work independently and report findings. Synthesize a
final review with categorized issues and an overall recommendation.

{{CONTEXT}}
```

---

## Customization Points

### TARGET
What to review. Examples:
- `PR #142`
- `src/auth/` module
- `the checkout flow (src/features/checkout/)`
- `changes in this commit`

### CONTEXT
Background information:
```
Context:
- This is a Node.js/TypeScript backend using Express
- Database is PostgreSQL with Prisma ORM
- Auth uses JWT tokens stored in httpOnly cookies
- Tests use Jest with 80% coverage requirement
```

---

## Variations

### PR Review (Most Common)

```
Create an agent team to review PR #{{PR_NUMBER}}.

Spawn three reviewers:
1. **Security Reviewer**: Check for auth flaws, injection, secrets exposure
2. **Performance Analyst**: Check for N+1 queries, complexity issues
3. **Test Coverage Checker**: Verify new code is tested

Use Sonnet for all reviewers.
Focus only on changed files.
Synthesize findings into approve/request-changes decision.
```

### Security-Focused Audit

```
Create an agent team for a security audit of {{MODULE}}.

Spawn three reviewers:
1. **Security Reviewer**: Deep vulnerability analysis (OWASP Top 10)
2. **Security Reviewer #2**: Focus on auth/authz and session management
3. **Security Reviewer #3**: Focus on data validation and injection

Use Opus for all reviewers (security requires deeper analysis).
Produce a security assessment report with risk ratings.
```

### Pre-Refactor Assessment

```
Create an agent team to assess {{MODULE}} before refactoring.

Spawn three reviewers:
1. **Test Coverage Checker**: Identify coverage gaps that need tests first
2. **Architecture Reviewer**: Identify coupling and design issues
3. **Performance Analyst**: Baseline current performance characteristics

Use Sonnet for all reviewers.
Produce an assessment of refactoring readiness and risk areas.
```

---

## Example Complete Prompt

```
Create an agent team to review PR #142 (Add user authentication).

Spawn three reviewers:

1. **Security Reviewer**: Focus on authentication vulnerabilities, input
   validation, secrets handling, and injection risks. Rate findings by
   severity (Critical/High/Medium/Low).

2. **Performance Analyst**: Analyze algorithmic complexity, database query
   efficiency, memory usage, and caching opportunities. Quantify impact
   where possible.

3. **Test Coverage Checker**: Evaluate test completeness, edge case
   coverage, and test quality. Identify untested code paths with specific
   test recommendations.

Use Sonnet for all reviewers.

Context:
- Node.js/TypeScript backend with Express
- PostgreSQL with Prisma ORM
- JWT auth with httpOnly cookies
- Jest tests, 80% coverage requirement

Have each reviewer work independently and report findings. Synthesize a
final review with categorized issues and an overall recommendation.
```
