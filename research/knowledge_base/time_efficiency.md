# Time-efficient training

**Runtime status:** conditional, normative when loaded

**Load when:** the user has at most 40 minutes per session, or the uncompressed
draft exceeds the available time

**Purpose:** fit productive training into the real session budget without
turning every short workout into an all-out circuit.

Time efficiency means preserving the highest-value training work while reducing
redundancy, avoidable transitions, and idle time. It does not override safety,
technique, symptom, RIR, or recovery constraints.

## Time model

Estimate duration before presenting the workout:

```text
session_duration =
    movement_specific_warm_up
  + work_set_execution
  + programmed_rest
  + equipment_and_station_transitions
  + logging_and_unplanned_buffer
```

Do not claim a session fits because only work-set execution time was counted.
For shared-gym supersets, include the practical cost of occupying or moving
between stations.

## Operational rules

| ID | Rule | Confidence | Conditions | Exceptions / limits | Source |
| --- | --- | --- | --- | --- | --- |
| `TE-001` | Compress in this order: remove redundant variations, reduce low-priority isolation work, simplify setup/transitions, use compatible supersets, then reduce work sets toward a useful minimum. | Moderate; programming inference | Draft exceeds the time budget | Goal priorities and clinical constraints can change what is low priority; do not remove all work for a major target silently. | EBD, “Minimal-dose training” and “Forty-minute framework” |
| `TE-002` | Preserve a brief movement-specific warm-up for the first demanding movement and any additional preparation required by load, skill, symptoms, or clinician instruction. | Moderate; conservative implementation | Every short session | Do not force a fixed warm-up duration when more preparation is needed. | EBD, “Forty-minute framework” |
| `TE-003` | Prefer non-competing supersets such as upper push + pull or lower + upper when they reduce time without degrading technique or target performance. | Moderate-high for time saving; Moderate for preferred pairing | Compatible exercises, equipment, and user tolerance | Avoid pairing two highly technical or same-muscle demanding exercises when fatigue would violate RIR, rest, or safety constraints. | EBD, “Supersets” |
| `TE-004` | In a superset, preserve adequate recovery before the same muscle or demanding movement is loaded again; increase round rest when performance deteriorates. | Moderate | Supersets are used | A superset is not permission for zero rest or for turning strength work into conditioning unintentionally. | EBD, “Supersets” and “Rest intervals” |
| `TE-005` | Use drop sets only as an optional replacement for selected straight-set accessory work, primarily on stable machine or isolation exercises. | Moderate for comparable hypertrophy/time saving; conservative for exercise class | Time is dominant, the user accepts higher exertion, and technique is stable | Do not use as a universally superior method, default novice method, or default on technical heavy barbell lifts. | EBD, “Drop sets”; Sødal et al. 2023 |
| `TE-006` | Do not add rest-pause, forced reps, or failure circuits as automatic compression methods without a separately reviewed rule. | Moderate evidence boundary | Any short session | A future reviewed technique may be added with explicit conditions and provenance. | EBD does not make these required; failure is unnecessary |
| `TE-007` | Keep most hypertrophy work near 1–3 RIR even when time is short; time pressure does not require failure. | Moderate-high | Hypertrophy-oriented short session | Optional stable isolation/drop-set work may approach 0–2 RIR when allowed by `WP-009` and `TE-005`. | EBD, RIR and time-efficiency sections |
| `TE-008` | Prefer fewer productive sets to an overfilled plan that cannot preserve technique, rest, transitions, or logging. | High that modest training beats none; Moderate for exact minimum | Time budget cannot hold the uncompressed dose | Recalculate weekly dose and disclose the tradeoff; do not claim equivalence to a higher completed volume. | EBD, “Minimal-dose training” |
| `TE-009` | Schedule cardio separately, after priority resistance work, or in another available window when placing it inside the session would displace the user's primary goal. | Moderate; scheduling inference | Program includes cardio and the session is time-limited | General-health adherence may justify combined sessions; explosive-power priorities favor separation when feasible. | EBD, “Combining resistance and cardio” |
| `TE-010` | Validate the final estimate against the user's hard time limit and retain a small logging/transition buffer. | High as product behavior | Every time-constrained draft | If the estimate still exceeds the limit, rerun compression or reduce scope; never hide the overrun. | EBD, “Forty-minute framework” |

## Approximate 40-minute architecture

This is an implementation template synthesized from the evidence, not a single
RCT-validated protocol:

| Approx. time | Work | Typical prescription |
| ---: | --- | --- |
| 0–5 min | Brief general movement and movement-specific warm-up | Progressively prepare the first demanding exercise. |
| 5–15 min | Pair A | Knee-dominant work + upper-body pull, about 2–3 work sets each. |
| 15–25 min | Pair B | Press + hip hinge, about 2–3 work sets each. |
| 25–33 min | Pair C | Secondary pull/press + unilateral leg or leg-curl objective, about 2 sets each. |
| 33–38 min | Trunk or explicit priority | About 2 focused sets when useful. |
| 38–40 min | Logging and transition buffer | Record load, reps, RIR, technique, and symptoms. |

Exercise selection remains conditional on equipment, goal, clinical status,
preference, and response. A novice commonly receives fewer sets than the upper
end of this template.

## Shorter sessions

For roughly 30 minutes, treat this as a product heuristic:

1. keep a brief necessary warm-up;
2. use two compatible primary pairs covering the highest-priority objectives;
3. add one short accessory or trunk pair only if the estimate still fits;
4. distribute omitted nonessential work elsewhere in the week only when real
   availability exists;
5. preserve the buffer and disclose reduced weekly dose or coverage.

Do not scale every rest interval and exercise duration down by the same
percentage. Heavy strength, complex skills, and symptom-limited work may require
more rest and therefore fewer exercises.

## Validation failures

Reject or revise the compressed session when:

- estimated time exceeds the available minutes;
- a superset violates equipment reality, rest needs, technique, or symptoms;
- a time-saving technique requires unplanned failure;
- transition time or logging buffer is missing;
- the short-session rewrite silently changes the primary goal;
- essential clinical modifications or warm-up requirements were removed;
- weekly volume was increased to “make up” for time without evidence that the
  user can complete and recover from it.
