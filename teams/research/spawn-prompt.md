# Research Team - Spawn Prompt

Copy and customize the sections marked with `{{PLACEHOLDER}}`:

---

## Basic Spawn Prompt

```
Create an agent team to research {{TOPIC}}.

**Team Structure:**

1. **Investigator**: Deeply explore {{ASPECTS}}. Gather evidence from the
   codebase, documentation, and best practices. Document findings with
   specific examples and confidence levels.

2. **Devil's Advocate**: Challenge every finding from the Investigator.
   Find counterexamples, identify risks, and argue the opposite position.
   Your job is to stress-test conclusions, not to agree.

3. **Synthesizer**: After the Investigator and Devil's Advocate have
   debated, combine their perspectives into a balanced recommendation.
   Include summary, risks, next steps, and confidence level.

Use Opus for all teammates (research requires deep reasoning).

Have teammates communicate directly with each other. The Investigator and
Devil's Advocate should debate findings before the Synthesizer produces
the final report.

{{CONTEXT}}
```

---

## Customization Points

### TOPIC
The research question:
- `migrating from REST to GraphQL`
- `choosing a state management library (Redux vs Zustand vs Jotai)`
- `investigating the memory leak in production`
- `feasibility of real-time collaboration features`

### ASPECTS
Specific angles to explore:
- `technical feasibility and implementation complexity`
- `performance implications and scalability`
- `team learning curve and maintenance burden`
- `cost implications and resource requirements`

### CONTEXT
Decision criteria and constraints:
```
Context:
- Current stack: React, Express, PostgreSQL
- Team size: 5 developers, mixed experience levels
- Timeline: Need decision within 1 week, implementation within 1 month
- Constraints: Must maintain backward compatibility with existing API
```

---

## Variations

### Technology Selection

```
Create an agent team to evaluate {{OPTIONS}} for {{PURPOSE}}.

**Team Structure:**

1. **Investigator A**: Research {{OPTION_A}} - implementation patterns,
   performance characteristics, ecosystem maturity, learning curve.

2. **Investigator B**: Research {{OPTION_B}} - same criteria as above.

3. **Devil's Advocate**: Challenge findings from both investigators.
   Find weaknesses in each option. Identify hidden costs and risks.

4. **Synthesizer**: Compare options objectively. Produce recommendation
   with clear rationale and migration path.

Use Opus for all teammates.

Decision criteria (in priority order):
1. {{CRITERION_1}}
2. {{CRITERION_2}}
3. {{CRITERION_3}}

{{CONTEXT}}
```

### Root Cause Investigation

```
Create an agent team to investigate {{PROBLEM}}.

**Team Structure:**

1. **Investigator**: Form hypotheses about the root cause. Gather evidence
   from logs, code, and metrics. Test hypotheses systematically.

2. **Devil's Advocate**: Challenge each hypothesis. Propose alternative
   explanations. Identify what evidence would disprove each theory.

3. **Synthesizer**: Once debate concludes, document the most likely root
   cause with evidence, alternative explanations considered, and
   recommended fix with verification plan.

Use Opus for all teammates.

Symptoms:
{{SYMPTOM_LIST}}

Relevant code paths:
{{CODE_PATHS}}
```

### Feasibility Study

```
Create an agent team to assess feasibility of {{FEATURE}}.

**Team Structure:**

1. **Technical Investigator**: Analyze implementation complexity, required
   changes, technical risks, and dependencies.

2. **Business Investigator**: Analyze user value, market comparison,
   maintenance burden, and opportunity cost.

3. **Devil's Advocate**: Challenge both perspectives. Find reasons why
   this might fail. Identify hidden costs and risks.

4. **Synthesizer**: Produce go/no-go recommendation with confidence level,
   key risks, and recommended approach if proceeding.

Use Opus for all teammates.

{{CONTEXT}}
```

---

## Example Complete Prompt

```
Create an agent team to research migrating from Redux to Zustand.

**Team Structure:**

1. **Investigator**: Deeply explore the migration path. Analyze:
   - Technical complexity of migration
   - Performance differences (bundle size, runtime)
   - API compatibility and learning curve
   - Ecosystem (middleware, devtools, community)

   Gather evidence from our codebase (src/store/), Zustand docs, and
   community experiences. Document findings with confidence levels.

2. **Devil's Advocate**: Challenge every finding. Specifically:
   - Find cases where Redux patterns don't translate to Zustand
   - Identify features we use that Zustand lacks
   - Argue for staying with Redux - what are we losing?
   - Find migration horror stories and failure cases

3. **Synthesizer**: After the debate, produce a recommendation:
   - Summary of migration complexity
   - Risk assessment with mitigations
   - Recommended approach (big bang vs incremental)
   - Concrete next steps with effort estimates
   - Confidence level in recommendation

Use Opus for all teammates.

Context:
- Current Redux usage: 15 slices, 50+ actions, heavy use of redux-saga
- Team: 5 devs, 3 very familiar with Redux, 2 newer
- Motivation: Reduce boilerplate, improve DX, smaller bundle
- Constraint: Cannot break existing features, need gradual migration path
```
