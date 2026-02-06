# Example Workflows

Complete end-to-end examples of using Claude Agent Teams.

## Example 1: Building a REST API Endpoint

### Goal
Add a new REST API endpoint for user profile management.

### Step 1: Initialize Project

```bash
cd my-api-project
catt init
```

**Interactive prompts:**
```
Project name: user-profile-api
Description: Add user profile CRUD endpoints
Use case: Build a new feature
```

**Select agents:**
- ✅ Researcher (opus) - Evaluate best practices
- ✅ Architect (opus) - Design API structure
- ✅ Developer (sonnet) - Implement endpoints
- ✅ Tester (sonnet) - Write integration tests
- ✅ Reviewer (sonnet) - Final code review

### Step 2: Review Configuration

The init command created `.catt/project.yaml`:

```yaml
name: user-profile-api
description: Add user profile CRUD endpoints
use_case: build_feature
agents:
  researcher:
    role: researcher
    model: opus
    enabled: true
    depends_on: []
  architect:
    role: architect
    model: opus
    enabled: true
    depends_on: [researcher]
  developer:
    role: developer
    model: sonnet
    enabled: true
    depends_on: [architect]
  tester:
    role: tester
    model: sonnet
    enabled: true
    depends_on: [developer]
  reviewer:
    role: reviewer
    model: sonnet
    enabled: true
    depends_on: [tester]
```

### Step 3: Preview Execution Plan

```bash
catt run --dry-run
```

**Output:**
```
Project: user-profile-api
Add user profile CRUD endpoints

Execution Plan:
  1. Researcher (opus)
  2. Architect (opus) (after: researcher)
  3. Developer (sonnet) (after: architect)
  4. Tester (sonnet) (after: developer)
  5. Reviewer (sonnet) (after: tester)
```

### Step 4: Run the Workflow

In one terminal:
```bash
catt run
```

In another terminal (to monitor progress):
```bash
catt dashboard
```

### Step 5: Workflow Execution

**Researcher (5 minutes):**
- Evaluates REST best practices
- Researches authentication patterns
- Documents recommendations
- Signals: `<promise>RESEARCH_COMPLETE</promise>`

**Architect (10 minutes):**
- Reads researcher's findings
- Designs API endpoints:
  - GET /api/v1/users/:id/profile
  - PUT /api/v1/users/:id/profile
  - DELETE /api/v1/users/:id/profile
- Defines data models and validation rules
- Creates architecture document
- Signals: `<promise>ARCHITECTURE_COMPLETE</promise>`

**Developer (20 minutes):**
- Implements routes in `src/routes/profile.ts`
- Adds controllers in `src/controllers/profile.ts`
- Implements validation middleware
- Updates database models
- Signals: `<promise>IMPLEMENTATION_COMPLETE</promise>`

**Tester (15 minutes):**
- Writes integration tests in `tests/profile.test.ts`
- Tests happy paths
- Tests error cases
- Tests authentication
- Signals: `<promise>TESTS_COMPLETE</promise>`

**Reviewer (10 minutes):**
- Reviews all code
- Checks security (SQL injection, XSS)
- Verifies error handling
- Confirms test coverage
- Provides final report

### Step 6: Review Results

```bash
# View all files changed
git status

# Review the diff
git diff

# Check test results
npm test
```

### Step 7: Commit Changes

```bash
git add src/routes/profile.ts src/controllers/profile.ts tests/profile.test.ts
git commit -m "Add user profile CRUD endpoints

- Implemented GET, PUT, DELETE endpoints for user profiles
- Added input validation and authentication middleware
- Created comprehensive integration tests
- Followed REST best practices from research phase

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

### Total Time
Approximately 60 minutes of agent work time (may complete faster with parallel operations).

---

## Example 2: Code Security Review

### Goal
Review existing codebase for security vulnerabilities.

### Step 1: Use Code Review Team

```bash
cd my-app
catt team spawn review
```

**Copy the spawn prompt** and customize:

```
Create a security review team to audit the authentication system.

**Team Structure:**

1. **Security Reviewer**: Focus on authentication vulnerabilities (SQL injection,
   XSS, CSRF, session management). Scan files in src/auth/ and src/middleware/.

2. **Performance Analyst**: Identify N+1 queries, inefficient algorithms, and
   database bottlenecks. Review files in src/models/ and src/services/.

3. **Test Coverage Checker**: Ensure all auth flows have tests. Review test
   files in tests/auth/.

Use Sonnet for all reviewers (parallel execution).

Create tasks:
- Task 1: Security audit (Security Reviewer)
- Task 2: Performance analysis (Performance Analyst)
- Task 3: Test coverage report (Test Coverage Checker)

All tasks run in parallel - no dependencies.

Context:
- Framework: Express with TypeScript
- Database: PostgreSQL
- Auth: JWT tokens in httpOnly cookies
- Focus areas: src/auth/, src/middleware/auth.ts
```

### Step 2: Start Team (Paste into Claude Code)

The three reviewers work in parallel, each scanning their assigned areas.

### Step 3: Results

Each reviewer produces a report:

**Security Reviewer:**
```markdown
## Security Audit Report

### HIGH: SQL Injection in Custom Query
- Location: src/auth/login.ts:42
- Issue: String concatenation in SQL query
- Fix: Use parameterized queries

### MEDIUM: Missing Rate Limiting
- Location: src/routes/auth.ts
- Issue: No rate limiting on login endpoint
- Fix: Add express-rate-limit middleware

### LOW: Weak Password Requirements
- Location: src/middleware/validation.ts:15
- Issue: Only checks length, not complexity
- Fix: Add zxcvbn password strength check
```

**Performance Analyst:**
```markdown
## Performance Analysis Report

### N+1 Query Detected
- Location: src/services/user.ts:67
- Issue: Loading user.posts in loop
- Impact: 100+ queries for 100 users
- Fix: Use eager loading

### Inefficient Algorithm
- Location: src/utils/search.ts:23
- Issue: O(n²) search implementation
- Fix: Use Map for O(1) lookups
```

**Test Coverage Checker:**
```markdown
## Test Coverage Report

Overall Coverage: 68%

### Missing Tests:
- Password reset flow (0% coverage)
- OAuth callback handling (0% coverage)
- Token refresh logic (45% coverage)

### Well-Tested:
- Login flow (98% coverage)
- Registration (95% coverage)
```

---

## Example 3: Research & Decision Making

### Goal
Choose between PostgreSQL and MongoDB for a new microservice.

### Step 1: Use Research Team

```bash
catt team spawn research
```

**Customize the prompt:**

```
Create a research team to evaluate database options for a new notification service.

**Team Structure:**

1. **Investigator** (opus): Research PostgreSQL vs MongoDB for notification
   service. Consider: querying patterns, scaling, consistency requirements.

2. **Devil's Advocate** (opus): Challenge the investigator's findings. Point out
   risks, edge cases, and potential issues with each option.

3. **Synthesizer** (opus): Review both perspectives and make a final recommendation
   with justification.

Context:
- Notification service needs: user preferences, delivery status tracking, history
- Expected scale: 1M notifications/day
- Query patterns: fetch by user, fetch by date range, update status
- Team familiarity: Strong PostgreSQL experience, limited MongoDB experience
```

### Step 2: Run Research

Agents work sequentially:
1. Investigator researches both options
2. Devil's Advocate challenges findings
3. Synthesizer makes final recommendation

### Step 3: Result

**Final Recommendation:**
```markdown
## Database Selection: PostgreSQL

### Justification:
1. **Query Patterns**: Notification queries are relational (user → notifications)
2. **Consistency**: Delivery status tracking requires ACID guarantees
3. **Team Experience**: Reducing operational risk with known technology
4. **Scaling**: Can handle 1M/day with proper indexing and partitioning

### Trade-offs:
- MongoDB would offer easier horizontal scaling
- But JSONB in PostgreSQL provides sufficient flexibility
- Team's PostgreSQL expertise outweighs MongoDB's advantages

### Action Items:
1. Use PostgreSQL with JSONB for flexible notification payloads
2. Partition notifications table by date
3. Add indexes on user_id and created_at
```

---

## Example 4: Large Feature Development

### Goal
Build a complete authentication system from scratch.

### Step 1: Use Software Development Team

```bash
catt team spawn software
```

This includes: PM, Researcher, Architect, Developer, Tester, Reviewer.

### Step 2: Workflow

**Product Manager (15 min):**
- Creates user stories
- Defines acceptance criteria
- Prioritizes features

**Researcher (20 min):**
- Evaluates auth libraries (Passport, Auth0, custom JWT)
- Researches OAuth 2.0 best practices
- Documents security requirements

**Architect (25 min):**
- Designs auth flow diagrams
- Defines API endpoints
- Creates database schema
- Plans middleware structure

**Developer (60 min):**
- Implements:
  - User registration with email verification
  - Login with JWT tokens
  - Password reset flow
  - OAuth integration (Google, GitHub)
  - Session management
  - Rate limiting

**Tester (40 min):**
- Unit tests for all auth functions
- Integration tests for endpoints
- E2E tests for complete flows
- Security test cases

**Reviewer (20 min):**
- Code quality review
- Security audit
- Performance check
- Documentation review

### Total Time
~3 hours of agent work (with parallel operations where possible)

---

## Example 5: Quick Bug Fix (Minimal Team)

### Goal
Fix a specific bug quickly without full team overhead.

### Setup

Custom `.catt/project.yaml`:

```yaml
name: bugfix-session-leak
description: Fix session memory leak
use_case: bugfix
agents:
  developer:
    role: developer
    model: sonnet
    enabled: true
    depends_on: []
    max_iterations: 20
    custom_prompt: |
      Fix the session memory leak in src/middleware/session.ts.
      The issue is that sessions are not being cleaned up after logout.

      Steps:
      1. Identify the root cause
      2. Implement the fix
      3. Add a test to prevent regression

      Keep it simple and focused.
  tester:
    role: tester
    model: sonnet
    enabled: true
    depends_on: [developer]
    max_iterations: 10
```

### Run

```bash
catt run
```

**Results:**
- Developer fixes bug (10 min)
- Tester adds regression test (5 min)
- Total: 15 minutes

---

## Tips for Effective Workflows

### 1. Right-Size Your Team

**Too Big:**
```yaml
# Overkill for a small bug fix
agents: [pm, researcher, architect, dev, tester, security, performance, reviewer]
```

**Just Right:**
```yaml
# Appropriate for a bug fix
agents: [developer, tester]
```

### 2. Use Custom Prompts for Context

```yaml
agents:
  developer:
    custom_prompt: |
      Context:
      - This project uses React with TypeScript
      - Follow the component patterns in src/components/
      - Use styled-components for styling
      - All components must have PropTypes
```

### 3. Adjust Iterations for Task Complexity

```yaml
agents:
  researcher:
    max_iterations: 60  # Complex research needs more time
  developer:
    max_iterations: 40  # Standard implementation
  reviewer:
    max_iterations: 20  # Quick review
```

### 4. Set Up Dependencies Correctly

**Parallel (Independent Tasks):**
```yaml
security_reviewer:
  depends_on: []
performance_reviewer:
  depends_on: []
test_reviewer:
  depends_on: []
```

**Sequential (Dependent Tasks):**
```yaml
architect:
  depends_on: [researcher]
developer:
  depends_on: [architect]
tester:
  depends_on: [developer]
```

### 5. Monitor Progress

```bash
# Terminal 1: Run workflow
catt run

# Terminal 2: Monitor dashboard
catt dashboard --watch

# Terminal 3: View agent logs
catt agent logs developer

# Terminal 4: Check tasks
watch -n 5 "catt tasks --kanban"
```

---

## Common Patterns

### Pattern: Architecture Review Before Implementation

```yaml
architect:
  enabled: true
  depends_on: []
  # Require plan approval

developer:
  enabled: true
  depends_on: [architect]
  # Wait for architecture
```

### Pattern: Parallel Code Reviews

```yaml
security_reviewer:
  depends_on: [developer]  # All wait for dev
performance_reviewer:
  depends_on: [developer]
test_reviewer:
  depends_on: [developer]

final_reviewer:
  depends_on: [security_reviewer, performance_reviewer, test_reviewer]
  # Synthesis review after all parallel reviews
```

### Pattern: Progressive Enhancement

```yaml
# Phase 1: Core functionality
core_developer:
  enabled: true
  depends_on: [architect]

# Phase 2: Enhancements (after core)
enhancement_developer:
  enabled: true
  depends_on: [core_developer, tester]

# Phase 3: Polish (after enhancements)
ui_polish:
  enabled: true
  depends_on: [enhancement_developer]
```

---

## Next Steps

- Read [Best Practices](best-practices.md) for optimization tips
- See [Troubleshooting](troubleshooting.md) for common issues
- Check [FAQ](faq.md) for quick answers
