# Exercise selection

**Runtime status:** normative

**Load:** always, after the clinical-safety gate

**Purpose:** build and rank exercise candidates that satisfy the program's
movement and muscle objectives without pretending that one exercise is
universally best.

Exercise selection is a constrained ranking problem. The selected exercise is
the highest-ranked acceptable candidate for this user and this session, not a
claim of universal biomechanical superiority.

## Candidate record

Each exercise candidate should provide:

```text
id
movement_objectives
direct_muscles
strongly_involved_indirect_muscles
required_equipment
setup_time
skill_complexity
stability_demand
load_progression_options
adjustable_rom
supported_or_seated
grip_stance_and_loading_variants
superset_compatibility
clinical_constraints
user_feedback_history
```

Missing metadata lowers selection confidence; it must not be guessed from an
exercise name when the guess could affect safety or equipment compatibility.

## Operational rules

| ID | Rule | Confidence | Conditions | Exceptions / limits | Source |
| --- | --- | --- | --- | --- | --- |
| `ES-001` | Generate multiple candidates for a movement or muscle objective, then filter hard constraints before scoring preferences. | Moderate; algorithmic design | Every exercise slot | If only one safe, available candidate remains, expose the narrow choice rather than inventing alternatives. | EBD, “Proposed exercise-selection scoring” |
| `ES-002` | Treat machines, free weights, bands, and bodyweight as potentially effective modalities. Rank them by fit, not by a universal equipment hierarchy. | High | General resistance training | Goal specificity, setup, stability, accessibility, or symptoms may make one modality preferable for a user. | EBD, scope conclusions; ACSM 2026 |
| `ES-003` | Filter candidates that conflict with equipment, explicit clinician restrictions, current safety state, or a repeatedly unfavorable symptom response. | High for constraints; Moderate for feedback logic | A corresponding hard constraint or established response exists | Previous injury alone is not a permanent ban; a changed clinical state requires reassessment. | EBD, “Common musculoskeletal limitations” |
| `ES-004` | Give observed exercise-specific tolerance, technique confidence, adherence, and progression more weight than height, BMI, or segment-proportion predictions. | Moderate-high | Exercise history exists | Acute warning symptoms still bypass scoring and return to the safety gate. | EBD, “Anthropometric decision matrix” and “Adaptive feedback loop” |
| `ES-005` | Use anthropometry only to propose setup or variation trials; never make it the sole selector or exclusion criterion. | Moderate evidence against deterministic selection | Relevant fit, ROM, or geometry issue | Load `biomechanics.md` before applying an anthropometric modifier. | EBD, “Biomechanics and anthropometric individualization” |
| `ES-006` | For low-frequency or short programs, prioritize candidates that cover broad training objectives and are quick to set up before redundant isolation variations. | Moderate | Limited time or 1–2 training days | A clinical restriction, explicit preference, or local-muscular goal can justify a stable isolation exercise. | EBD, “Minimal-dose training” |
| `ES-007` | Match exercise complexity to current competence. Favor stable, adjustable options during early learning, high fatigue, or symptom-limited training. | Moderate; conservative implementation | Novice, low confidence, unstable technique, or constrained ROM | Stable does not mean mandatory machine use, and free weights are not inherently unsafe. | EBD, ACSM emphasis on individualization |
| `ES-008` | Offer supported, seated, low-impact, or easily scaled candidates when they improve accessibility for a higher-body-mass or deconditioned user. | Moderate | Accessibility, balance, equipment-fit, or joint-tolerance issue is present | BMI or body mass alone must not force machines, lower training quality, or unique rep ranges. | EBD, “Overweight and obesity as an anthropometric variable” |
| `ES-009` | When a movement provokes manageable symptoms, first test changes to load, ROM, grip/stance, support, or variation while monitoring response instead of permanently banning the pattern. | Moderate-high for continued exercise; Low-moderate for a specific substitution | Safety gate allows exercise with constraints | Worsening, new, or concerning symptoms return to `clinical_safety.md`; clinician restrictions are hard limits. | EBD, “Common musculoskeletal limitations” |
| `ES-010` | Use a controlled, tolerated ROM that satisfies the objective; record the ROM so response can be compared over time. | Moderate; implementation rule | Every resistance candidate | Do not enforce universal full ROM, lengthened partials, or fixed joint-angle windows without a reviewed condition-specific rule. | EBD, anthropometric and clinical sections |
| `ES-011` | Select trunk exercises from tolerated functional directions and actual program gaps; do not diagnose a “weak core” from pain or posture. | Moderate for general exercise; Low for exact architecture | Direct trunk work is included | No universal requirement exists for every trunk category each week. | EBD, “What core training should mean” |
| `ES-012` | Select cardio modality by preference, conditioning, impact tolerance, accessibility, and equipment. | High for flexible activity; Moderate for modality ranking | Cardio is included | Do not default everyone to HIIT or imply that one modality is optimal for all adults. | EBD, “Cardiorespiratory training”; WHO 2020 |
| `ES-013` | A substitution must preserve the slot's primary objective and update muscle-volume, rest, setup-time, and safety metadata. | Moderate; algorithmic design | Any automatic or user-requested substitution | If no equivalent candidate exists, recalculate the program rather than silently swapping by exercise name. | Derived from EBD scoring and volume framework |

## Coverage objectives

Build the weekly plan from objectives, not a mandatory list of branded lifts.
Common objectives include:

- knee-dominant lower-body work;
- hip-dominant or hinge work;
- upper-body push and pull across useful directions;
- optional unilateral lower-body, calf, arm, shoulder, grip, or priority work;
- direct trunk work where useful;
- an aerobic modality when the program includes cardio.

Not every objective must appear in every session. The weekly result should train
the intended major muscle groups within the dose from `workout_programming.md`.

## Candidate scoring

After hard filtering, rank candidates conceptually as:

```text
score =
    goal_match
  + equipment_match
  + user_preference
  + movement_competence
  + progression_potential
  + observed_tolerance
  + adherence_history
  + conditional_anthropometric_fit
  - current_symptom_penalty
  - setup_and_transition_cost
  - unnecessary_fatigue_cost
```

The weights are product hypotheses and require validation. `observed_tolerance`
and longitudinal response should have a stronger effect than
`conditional_anthropometric_fit`. A score must never convert a blocked exercise
into an allowed one.

## Trial and feedback

For a new or modified candidate, store:

```text
variation + setup + load + reps + RIR + ROM
+ technical confidence + stability
+ discomfort location/behavior
+ next-day or next-session symptom response
```

Use this record to compare acceptable variations. The initial candidate can be
an informed guess; repeated individual response is the stronger selector.
