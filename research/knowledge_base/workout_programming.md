# Workout programming

**Runtime status:** normative

**Load:** always, after the initial clinical-safety gate

**Purpose:** convert goal, experience, availability, equipment, and recovery
capacity into a weekly resistance- and aerobic-training structure.

This file defines starting ranges, not one universally optimal workout. The
generator should optimize consistency, adequate effort, recoverable volume,
exercise tolerance, and progression.

## Required inputs

- primary goal: `general_health`, `hypertrophy`, `maximal_strength`, or
  `local_muscular_endurance`;
- training experience and recent training exposure;
- available days per week and minutes per session;
- available equipment and exercise preferences;
- clinical-safety result and hard constraints;
- completed training history when available.

If an essential input is missing, choose the least complex conservative default
that remains useful and mark the assumption. Never invent clinical clearance,
equipment, or training history.

## Operational rules

| ID | Rule | Confidence | Conditions | Exceptions / limits | Source |
| --- | --- | --- | --- | --- | --- |
| `WP-001` | Apply the order `safety -> goal -> availability -> recoverable volume -> exercise selection -> effort -> progression -> feedback`. | High | Every program | No later rule may override the safety gate or clinician restriction. | EBD, “Algorithm-ready framework” |
| `WP-002` | Expose every major muscle group to resistance training on about 2 or more days per week as the general default. | High | Eligible adult; general health or a balanced program | One reliable full-body day is still preferable to no training; do not fabricate extra availability. | EBD, “Frequency”; ACSM 2026, DOI `10.1249/MSS.0000000000003897` |
| `WP-003` | Start novices with mostly moderate, technically manageable loads, 1–3 work sets per exercise, and about 3–4 RIR while learning. | High for simple starting dose; Moderate for exact range | Novice or returning after a long layoff | Clinical constraints may require a smaller dose; experienced users need not restart here without a reason. | EBD, “Goal-specific prescription” |
| `WP-004` | For hypertrophy, use a broad loading spectrum; use about 6–15 reps and 1–3 RIR as an efficient default, not as a unique physiological optimum. | High for broad loading; Moderate for exact implementation range | Hypertrophy is a primary or secondary goal | Lighter sets commonly require more reps and closer proximity to failure; symptomatic exercise is controlled by more than RIR. | EBD, “Goal-specific prescription” and “Proximity to failure”; DOI `10.1519/JSC.0000000000002200` |
| `WP-005` | Build hypertrophy volume gradually toward about 10 challenging direct-equivalent sets per muscle per week when experience, adherence, recovery, and time support it. | High for volume principle; Moderate for the target as an individual prescription | Hypertrophy priority | Ten is neither a minimum nor a threshold; do not automatically exceed it or label more than 20 sets as a universal MRV. | EBD, “Weekly volume”; ACSM 2026; DOI `10.1007/s40279-025-02344-w` |
| `WP-006` | Estimate muscle volume as `direct sets + 0.5 x strongly involved indirect sets` for planning and duplicate-work detection. | Moderate | Weekly volume accounting | This is a software approximation, not a biological law; exercise-specific involvement may be uncertain. | EBD, “Weekly volume”; DOI `10.1007/s40279-025-02344-w` |
| `WP-007` | For maximal strength, include substantial work at or above about 80% 1RM on the priority movements, commonly about 3–6 reps for 2–3 work sets with about 2–4 RIR and longer rest. | High for heavy-load specificity; Moderate for exact rep/RIR boundaries | Technically competent, clinically eligible user with maximal-strength goal | Not every exercise must be heavy; novice skill work and symptomatic training may use lighter loads. | EBD, “Goal-specific prescription”; ACSM 2026; DOI `10.1136/bjsports-2023-106807` |
| `WP-008` | For local muscular endurance, emphasize lighter task-specific sets commonly at 15 or more reps, usually 2–3 sets relatively close to task-specific fatigue. | Moderate | Local muscular endurance goal | Retain broader resistance work when compatible with the user's goal; do not infer cardiovascular fitness from local repetition endurance. | EBD, “Goal-specific prescription” |
| `WP-009` | Do not require momentary muscular failure. Reserve optional 0–2 RIR work mainly for stable machine or isolation exercises when the user wants it and recovery is acceptable. | Moderate-high evidence that failure is not required | Routine resistance training | Avoid failure by default during novice compound-skill work, heavy strength work, and symptom-limited exercise. | EBD, “Proximity to failure”; DOI `10.1016/j.jshs.2021.01.007`, `10.1007/s40279-022-01784-y` |
| `WP-010` | Default rest to about 2–3 minutes after demanding compound sets, 1–2 minutes after accessory work, and 2–4 or more minutes for heavy strength work when needed. Increase rest when performance or technique deteriorates unexpectedly. | Moderate | Resistance-training sessions | Supersets change how rest is scheduled but do not remove the need for adequate recovery before a muscle is loaded again. | EBD, “Rest intervals”; PMID `39205815` |
| `WP-011` | Select the split from reliable days available; preserve weekly dose rather than treating a split name as anabolic. | Moderate-high | Every program | Higher frequency may help strength practice and distribute volume, but does not automatically justify more weekly volume. | EBD, “Frequency” and “Split selection”; PMID `38595233` |
| `WP-012` | Compress a low-availability program by removing redundant isolation work before removing broad movement coverage. | Moderate | 1–2 days per week or short sessions | A user's clinical limitation or stated priority can change which movements are essential. | EBD, “Minimal-dose training” |
| `WP-013` | Include aerobic activity as a distinct health target: work gradually toward 150–300 min/week moderate, 75–150 min/week vigorous, or an equivalent combination. | High | General-health programming | This is a weekly public-health target, not a requirement that every generated lifting session contain cardio; some activity is better than none. | EBD, “Cardiorespiratory training”; WHO 2020, DOI `10.1136/bjsports-2020-102955` |
| `WP-014` | Allow concurrent aerobic and resistance training for recreational goals. Prioritize the session's main goal; separate by about 3 hours when explosive power is a priority and separation is feasible. | Moderate-high | Program includes both modalities | Do not claim cardio destroys hypertrophy. Competitive endurance/power optimization is outside scope. | EBD, “Combining resistance and cardio” |
| `WP-015` | Treat direct trunk work as a small complement across tolerated functions such as resisting extension, rotation, or lateral flexion and controlled spinal motion where appropriate. | Moderate for exercise broadly; Low for an exact weekly architecture | Trunk work supports the goal or fills a program gap | No evidence requires all categories every week or supports universal spinal-flexion avoidance. | EBD, “What core training should mean” |

## Split defaults

| Reliable days/week | Default structure | Constraint |
| ---: | --- | --- |
| 1 | Full body | Use a meaningful minimum dose and disclose that frequency is below the general target. |
| 2 | Full body A/B | Aim for about two weekly exposures per major muscle group. |
| 3 | Full body A/B/C, or rotating full/upper/lower | Choose from preference and per-session time. |
| 4 | Upper/lower repeated, or lower-volume full-body sessions | Distribute moderate-to-high weekly volume without forcing long sessions. |
| 5 | Upper/lower plus a short full-body or priority session | Do not add volume solely because a fifth day exists. |
| 6 | Distributed push/pull/lower, upper/lower variants, or short full-body rotations | Use only when preference, adherence, and recoverable dose support it. |

Split choice is organizational. When weekly volume is matched, current evidence
does not establish a general strength or hypertrophy advantage for split over
full-body routines.

## Program construction

```text
1. Receive an allowed safety state and hard constraints.
2. Choose goal-specific load, repetition, RIR, and rest ranges.
3. Choose the split from reliable availability.
4. Allocate a conservative recoverable weekly dose.
5. Ask exercise_selection.md to fill movement/muscle objectives.
6. Apply conditional biomechanics, progression, and time-efficiency rules.
7. Recalculate direct-equivalent weekly sets and estimated duration.
8. Run clinical-safety and program-integrity validation.
```

## Required output and validation

Every generated program must expose enough structure to validate:

- day, exercise, movement objective, sets, rep range, target RIR, and rest;
- direct and strongly involved indirect muscle groups;
- weekly direct-equivalent sets by muscle group;
- estimated session duration including transitions and a logging buffer;
- active clinical, equipment, preference, and time constraints;
- applied rule IDs and any low-confidence assumptions.

Reject or revise a draft when it exceeds reliable availability, uses unavailable
equipment, violates a hard safety constraint, silently exceeds the time budget,
requires failure as a general rule, or derives training dose from height, BMI,
somatotype, or limb proportions.
