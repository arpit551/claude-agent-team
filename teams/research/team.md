# Research Team

## Purpose

Explore complex problems from multiple perspectives using adversarial collaboration. Investigators gather evidence, devil's advocates challenge findings, and synthesizers produce balanced recommendations.

## Team Composition

| Role | Focus | Model | Plan Approval |
|------|-------|-------|---------------|
| Investigator | Deep exploration, evidence gathering | opus | No |
| Devil's Advocate | Challenge findings, find counterexamples | opus | No |
| Synthesizer | Combine perspectives, produce recommendations | opus | No |

**Note**: All roles use Opus because research requires deep reasoning and nuanced analysis.

## Workflow

```
     ┌──────────────────┐
     │   Investigator   │
     │  Gathers Evidence│
     └────────┬─────────┘
              │ Shares findings
              ▼
     ┌──────────────────┐
     │ Devil's Advocate │◄────┐
     │ Challenges Findings    │
     └────────┬─────────┘     │
              │ Debate        │ Multiple
              ▼               │ rounds
     ┌──────────────────┐     │
     │   Investigator   │─────┘
     │  Defends/Refines │
     └────────┬─────────┘
              │ Debate concludes
              ▼
     ┌──────────────────┐
     │   Synthesizer    │
     │ Produces Report  │
     └──────────────────┘
```

## Interaction Pattern

**Adversarial Collaboration**:
1. Investigator shares findings with evidence
2. Devil's Advocate challenges with counterarguments
3. Investigator defends or refines based on challenges
4. Repeat until natural conclusion
5. Synthesizer integrates all perspectives

## Best Use Cases

- Technology selection decisions
- Architecture trade-off analysis
- Root cause investigation for complex bugs
- Feasibility studies
- Migration planning
- "Should we?" questions

## Anti-patterns (When NOT to Use)

- Known solutions (just implement)
- Simple debugging (use single session)
- Time-sensitive decisions (too slow)
- Questions with obvious answers

## Scaling Options

### Minimal (2 roles)
- Investigator + Synthesizer (skip devil's advocate)
- Good for: Information gathering without deep debate

### Standard (3 roles)
- All three roles as described
- Good for: Most research tasks

### Extended (4+ roles)
- Multiple investigators for different angles
- Good for: Multi-faceted research questions

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│Investigator │  │Investigator │  │Investigator │
│   (Tech)    │  │   (Cost)    │  │   (Team)    │
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │                │                │
       └────────────────┼────────────────┘
                        ▼
              ┌─────────────────┐
              │ Devil's Advocate│
              └────────┬────────┘
                       ▼
              ┌─────────────────┐
              │   Synthesizer   │
              └─────────────────┘
```

## Expected Output

Final synthesis document with:
- Summary of key findings (agreed upon)
- Resolved disagreements (how settled)
- Remaining uncertainties
- Recommendation with confidence level
- Concrete next steps
