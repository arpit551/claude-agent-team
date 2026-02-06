# Software Development Team - Spawn Prompt

Copy and customize the sections marked with `{{PLACEHOLDER}}`:

---

## Basic Spawn Prompt

```
Create a software development team to build {{FEATURE}}.

**Team Structure:**

1. **Product Manager**: Define requirements, user stories, and acceptance
   criteria. Document in {{REQUIREMENTS_PATH}}. Focus on user value and
   clear success metrics.

2. **Researcher**: Evaluate technical options for {{RESEARCH_TOPICS}}.
   Document findings in {{RESEARCH_PATH}}. Include pros/cons and
   recommendations.

3. **Architect** (require plan approval): Design the system architecture
   based on PM requirements and Researcher findings. Define interfaces,
   data flow, and integration points. Document in {{DESIGN_PATH}}.

4. **Developer**: Implement the feature following the Architect's design.
   Own files in {{SOURCE_PATH}}. Do not modify tests or documentation.

5. **Tester**: Create comprehensive tests after implementation.
   Own files in {{TEST_PATH}}. Cover unit, integration, and edge cases.

6. **Reviewer**: Final review for code quality, security, and design
   conformance. Read-only access. Approve or request changes.

Use Opus for PM, Researcher, and Architect. Use Sonnet for Developer,
Tester, and Reviewer.

Create tasks with dependencies:
- Task 1: Gather requirements (PM)
- Task 2: Research technical options (Researcher) - parallel with Task 1
- Task 3: Design architecture (Architect, blocked by Tasks 1 and 2)
- Task 4: Implement feature (Developer, blocked by Task 3)
- Task 5: Write tests (Tester, blocked by Task 4)
- Task 6: Final review (Reviewer, blocked by Tasks 4 and 5)

Enable delegate mode - coordinate only, do not implement directly.

{{CONTEXT}}
```

---

## Customization Points

### FEATURE
What's being built:
- `user authentication with OAuth2`
- `real-time notification system`
- `payment processing integration`
- `analytics dashboard`

### RESEARCH_TOPICS
What needs investigation:
- `OAuth providers (Google, GitHub, Auth0)`
- `WebSocket vs SSE for real-time updates`
- `Payment gateways (Stripe, Square, PayPal)`
- `Charting libraries (Chart.js, D3, Recharts)`

### PATH Variables
```
REQUIREMENTS_PATH: docs/requirements/
RESEARCH_PATH: docs/research/
DESIGN_PATH: docs/design/
SOURCE_PATH: src/features/{{feature}}/
TEST_PATH: tests/features/{{feature}}/
```

### CONTEXT
Background information:
```
Context:
- Existing stack: React, Node.js, PostgreSQL
- Auth: Currently using JWT tokens
- Patterns: Repository pattern, service layer
- Must integrate with existing user system
- Timeline: Feature freeze in 2 weeks
```

---

## Variations

### Without Research Phase

```
Create a software development team to build {{FEATURE}}.

**Team Structure:**

1. **Product Manager**: Define requirements and acceptance criteria.
2. **Architect** (require plan approval): Design the architecture.
3. **Developer**: Implement following the design.
4. **Tester**: Create comprehensive tests.
5. **Reviewer**: Final quality review.

Use Opus for PM and Architect, Sonnet for others.

Tasks:
- Task 1: Requirements (PM)
- Task 2: Design (Architect, blocked by Task 1)
- Task 3: Implement (Developer, blocked by Task 2)
- Task 4: Test (Tester, blocked by Task 3)
- Task 5: Review (Reviewer, blocked by Tasks 3 and 4)

{{CONTEXT}}
```

### With Parallel Frontend/Backend

```
Create a software development team to build {{FEATURE}}.

**Team Structure:**

1. **Product Manager**: Requirements and user stories.
2. **Researcher**: Technical feasibility study.
3. **Architect** (require plan approval): System design with clear
   frontend/backend boundaries.
4. **Frontend Developer**: UI components and client logic.
   Own: src/components/, src/pages/, src/hooks/
5. **Backend Developer**: API and business logic.
   Own: src/api/, src/services/, src/models/
6. **Tester**: Tests for both frontend and backend.
   Own: tests/
7. **Reviewer**: Final review.

Tasks:
- Task 1: Requirements (PM)
- Task 2: Research (Researcher) - parallel with Task 1
- Task 3: Design (Architect, blocked by Tasks 1, 2)
- Task 4: Frontend implementation (Frontend Dev, blocked by Task 3)
- Task 5: Backend implementation (Backend Dev, blocked by Task 3)
- Task 6: Write tests (Tester, blocked by Tasks 4, 5)
- Task 7: Final review (Reviewer, blocked by Tasks 4, 5, 6)

{{CONTEXT}}
```

---

## Example Complete Prompt

```
Create a software development team to build user authentication with
OAuth2 support for Google and GitHub.

**Team Structure:**

1. **Product Manager**: Define requirements, user stories, and acceptance
   criteria. Document in docs/requirements/auth/. Focus on user flows
   (sign up, sign in, link accounts) and security requirements.

2. **Researcher**: Evaluate OAuth providers (Google, GitHub) and
   authentication libraries. Document in docs/research/auth/. Include
   comparison of passport.js vs next-auth vs custom implementation.

3. **Architect** (require plan approval): Design the auth system based
   on requirements and research. Define interfaces for AuthService,
   TokenManager, and ProviderAdapter. Document in docs/design/auth/.

4. **Developer**: Implement the auth module following the design.
   Own files in src/features/auth/. Do not modify tests.

5. **Tester**: Create comprehensive tests after implementation.
   Own files in tests/features/auth/. Cover OAuth flows, token refresh,
   error handling, and security edge cases.

6. **Reviewer**: Final review for security vulnerabilities, code quality,
   and design conformance. Read-only. Focus especially on token handling
   and callback validation.

Use Opus for PM, Researcher, and Architect. Use Sonnet for Developer,
Tester, and Reviewer.

Create tasks with dependencies:
- Task 1: Gather auth requirements and user stories (PM)
- Task 2: Research OAuth providers and libraries (Researcher)
- Task 3: Design auth architecture (Architect, blocked by Tasks 1, 2)
- Task 4: Implement OAuth integration (Developer, blocked by Task 3)
- Task 5: Write auth tests (Tester, blocked by Task 4)
- Task 6: Security review (Reviewer, blocked by Tasks 4, 5)

Enable delegate mode - coordinate only, do not implement directly.

Context:
- Stack: Next.js, PostgreSQL with Prisma
- Existing user table with email/password auth
- Need to support account linking (OAuth + existing email)
- Must maintain session compatibility with current JWT approach
- Security: Follow OWASP guidelines for OAuth
```
