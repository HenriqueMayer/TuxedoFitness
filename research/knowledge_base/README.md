# Operational workout knowledge base

This directory is the normative knowledge layer for generating workouts for
general-population adults. It translates the research archive into bounded,
reviewable rules. It is not a diagnostic system, a rehabilitation protocol, or
a substitute for a qualified health professional.

## Scope

The rules cover adults seeking general health, hypertrophy, maximal strength,
or local muscular endurance through recreational training. They do not cover
minors, pregnancy or postpartum care, acute injury, postoperative care,
competitive sport optimization, or individualized treatment of complex
medical conditions.

## Loading contract

Load these files for every generation:

1. [`clinical_safety.md`](clinical_safety.md) as the pre-generation gate and
   final safety validator;
2. [`workout_programming.md`](workout_programming.md) for the weekly dose and
   session structure;
3. [`exercise_selection.md`](exercise_selection.md) for candidate generation
   and substitutions.

Load these files only when their trigger is present:

| File | Trigger |
| --- | --- |
| [`biomechanics.md`](biomechanics.md) | Equipment-fit issue, relevant ROM or segment information, instability, discomfort, repeated technique difficulty, or poor response to a variation |
| [`progression.md`](progression.md) | At least one completed-session record or exercise-specific history exists |
| [`time_efficiency.md`](time_efficiency.md) | Available session time is at most 40 minutes, or the draft exceeds the user's time budget |

Do not use the reports in [`../reports/`](../reports/) as direct generation
context. They are evidence and provenance for maintainers, not competing rule
sets for the model.

## Decision precedence

When rules conflict, apply this order:

```text
Safety gate
  -> explicit clinician restrictions
  -> goal and availability
  -> recoverable weekly dose
  -> exercise candidate selection
  -> biomechanical and clinical filtering
  -> effort and rest prescription
  -> history-based progression
  -> time compression
  -> final safety/time/volume validation
  -> feedback and adaptation
```

A lower layer may narrow or regress a prescription, but it must not bypass a
higher-layer constraint. Time pressure, preferences, or a performance goal
never override the safety gate.

## Rule contract

Operational tables use the following fields:

| Field | Meaning |
| --- | --- |
| `ID` | Stable identifier used in code, tests, logs, and reviews |
| `Rule` | The behavior the generator or validator must perform |
| `Confidence` | `High`, `Moderate`, or `Low`; low-confidence rules are explicit product heuristics |
| `Conditions` | Inputs or state required before the rule applies |
| `Exceptions / limits` | Situations where the rule is narrowed, overridden, or must not be used |
| `Source` | Research section and, where practical, primary DOI or guideline |

Confidence describes the evidence behind the proposition, not certainty that
it is correct for a particular user. Numeric ranges remain starting points.
Exercise-specific response over time should outrank weak anthropometric
predictions, while clinical constraints always outrank both.

## Required generator behavior

The generator must:

- return the applied rule IDs and active constraints with every draft;
- distinguish evidence-supported guidance from implementation heuristics;
- represent uncertainty as ranges or candidate trials, not false precision;
- keep source provenance out of user-facing medical claims unless the product
  has a separate reviewed communication layer;
- reject or revise a draft that fails safety, equipment, weekly-volume, or
  session-time validation;
- store feedback needed by [`progression.md`](progression.md) instead of trying
  to infer all personalization from body measurements before the first session.

## Evidence sources

`EBD` in rule tables means
[`../reports/evidence_based_workout_design.md`](../reports/evidence_based_workout_design.md),
the principal synthesis. The archived biomechanics report is cited only when a
rule explicitly records a rejected claim or provenance concern; it is never an
independent authority for runtime behavior.
