# Progression and adaptation

**Runtime status:** conditional, normative when loaded

**Load when:** at least one completed-session record or exercise-specific
history is available

**Purpose:** adapt reps, load, rest, ROM, variation, and weekly volume from
observed performance, recovery, adherence, and symptom response.

Progression is earned by the current prescription becoming manageable. It is
not an obligation to add weight or sets every session.

## Minimum history

For every performed exercise, retain when available:

```text
date + variation + setup
load + reps per set + target and reported RIR
rest duration + ROM
technical confidence / stability
session RPE
symptom location and behavior
next-day or next-session response
planned versus completed work
```

Missing history does not count as successful completion. When history is too
sparse to support adaptation, keep the current conservative prescription and
ask for the next observation.

## Operational rules

| ID | Rule | Confidence | Conditions | Exceptions / limits | Source |
| --- | --- | --- | --- | --- | --- |
| `PR-001` | Use rep-range plus RIR double progression: hold load while reps rise within range; after all prescribed sets reach the upper region at target RIR with stable technique and acceptable symptoms, add the smallest practical load and allow reps to return toward the lower bound. | Moderate; evidence-compatible implementation | Comparable completed history exists | Clinical or symptom constraints can require maintaining or regressing despite target performance. | EBD, “Progression” |
| `PR-002` | Progress only one primary dose variable at a time when practical so the response remains interpretable. | Low-moderate; product heuristic | Load, reps, sets, ROM, or frequency could change | A small load increase naturally changes achievable reps and is part of `PR-001`, not two independent progressions. | Derived from EBD adaptive-feedback principle |
| `PR-003` | If reps fall unexpectedly across sets while technique and symptoms remain acceptable, restore adequate rest before reducing the prescribed load. | Moderate | Rest was shorter than needed or performance loss suggests incomplete recovery | Reduce load immediately when technique or symptoms make the current load inappropriate. | EBD, “Rest intervals” and adaptive feedback loop |
| `PR-004` | If reps are below target but stable and safe, maintain the load or increase rest instead of automatically adding effort, sets, or failure work. | Moderate | Isolated underperformance without warning symptoms | Repeated decline triggers recovery and program review. | EBD, “Adaptive feedback loop” |
| `PR-005` | When symptoms increase, regress ROM, load, effort, set count, or variation before any progression and apply the clinical-safety state machine. | Moderate for modification; conservative safeguard | Symptom history changes | New warning symptoms stop automation; do not use RIR alone to clear symptom-limited work. | EBD, clinical sections and feedback loop |
| `PR-006` | When several exercises decline in the same period, review adherence, sleep/recovery context, session spacing, completed volume, and effort before changing a single lift. | Low-moderate; product heuristic | Multi-exercise or multi-session decline | Do not diagnose the cause from training logs. | EBD, “Progression” and adaptive feedback loop |
| `PR-007` | Add weekly sets only after confirming completed work, appropriate effort, adequate rest, recoverability, and lack of progress over a meaningful repeated exposure. | High for diminishing returns; Moderate for sequence | Hypertrophy or volume-supported goal has stalled | Never add volume merely because more days are available or because an arbitrary set threshold was not reached. | EBD, “Weekly volume” and “Progression”; DOI `10.1007/s40279-025-02344-w` |
| `PR-008` | Use exercise-specific response as the strongest personalization signal among otherwise acceptable candidates. | Moderate-high | Repeated comparable exposures exist | Safety states and clinician restrictions still override good performance. | EBD, “Anthropometric decision matrix” |
| `PR-009` | Calibrate RIR conservatively for novices: keep more repetitions in reserve during skill acquisition and revise the estimate from repeated logs rather than forcing failure tests. | Moderate | Novice or unreliable RIR reporting | Selective supervised assessment is outside this generator's default scope. | EBD, “Proximity to failure” |
| `PR-010` | Do not infer a universal deload date or MRV from a fixed weekly-set number. Regress dose when repeated recovery/performance evidence supports it. | High evidence against a universal threshold; Low-moderate for regression logic | Fatigue, adherence, or performance concerns exist | Clinician-directed recovery restrictions are hard constraints. | EBD, volume diminishing returns; rejected original-report MRV claim |

## Decision procedure

```text
if warning symptom or safety state worsened:
    stop progression and run clinical_safety.md

elif symptoms increased or technique became unstable:
    regress ROM/load/effort/sets or use an allowed variation

elif all sets reached the upper rep region
and reported RIR met target
and technique was stable
and symptoms/recovery were acceptable:
    increase by the smallest practical load step

elif target reps were missed but technique/symptoms were acceptable:
    maintain load and evaluate rest

elif several exercises declined repeatedly:
    review recovery, adherence, spacing, and total completed volume

elif progress stalled across repeated valid exposures:
    verify effort and execution, then consider a small volume change
```

## Adaptation output

Every automatic change must record:

- old and new prescription;
- evidence used from recent sessions;
- applied rule ID;
- whether the change affects load, reps, RIR, rest, ROM, exercise, sets, or
  frequency;
- active safety and time constraints;
- what feedback is required before the next progression.

Do not make a silent multi-variable rewrite. If the evidence is ambiguous,
maintaining the current prescription is a valid outcome.
