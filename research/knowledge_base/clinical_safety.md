# Clinical safety and validation

**Runtime status:** normative safety boundary

**Load:** always, before generation and again for final validation

**Purpose:** decide whether automated programming may proceed, must proceed with
constraints, or must stop pending appropriate professional evaluation.

This knowledge base does not diagnose disease, determine that pain is harmless,
or deliver individualized rehabilitation. It supports conservative exercise
programming for general-population adults after appropriate screening.

## Required screening inputs

At minimum, collect and keep distinct:

- current physical-activity level and recent training exposure;
- intended exercise intensity and whether it is a substantial increase;
- current warning signs or symptoms;
- known cardiovascular, metabolic, renal, neurological, or musculoskeletal
  conditions relevant to exercise;
- recent surgery, acute injury, or explicit clinician restrictions;
- current and previous pain location, behavior, and change over time;
- medications or other factors only when the product has a reviewed, qualified
  interpretation pathway.

Missing safety information must remain `unknown`; it must never be converted to
`no condition` or `cleared`.

## Safety states

The safety gate returns exactly one state plus reasons and hard constraints:

| State | Generator behavior |
| --- | --- |
| `blocked_urgent` | Do not generate or progress a workout. Advise the user to seek appropriate urgent or emergency assessment for the current warning symptom. |
| `blocked_pending_professional_review` | Do not generate the affected training until the user has appropriate professional guidance or the missing restriction is resolved. |
| `allowed_with_constraints` | Generate only inside explicit clinical, symptom, load, ROM, intensity, or exercise constraints and require feedback monitoring. |
| `allowed` | Generate normally within the remaining knowledge-base rules. This is not a guarantee of safety. |

## Operational rules

| ID | Rule | Confidence | Conditions | Exceptions / limits | Source |
| --- | --- | --- | --- | --- | --- |
| `CS-001` | Run the safety gate before goal, split, exercise, progression, or time-efficiency logic and rerun it on the completed draft. | High as a product safeguard | Every generation | No user goal, time limit, or preference bypasses this gate. | EBD, “Common musculoskeletal limitations” and algorithm hierarchy |
| `CS-002` | Return `blocked_urgent` for a current acute warning symptom such as chest pain/pressure, unexplained fainting, severe or unusual breathlessness, a new focal neurological sign, or a major acute injury/sudden severe pain. | High for screening need; conservative product policy | The user reports a current warning symptom | Examples are not exhaustive or diagnostic; the product must not identify a cause or suggest exercising through it. | EBD citing ACSM screening; Riebe et al. 2015, DOI `10.1249/MSS.0000000000000664` |
| `CS-003` | Assess exercise risk from current activity, warning signs/symptoms or known cardiovascular/metabolic/renal disease, and intended intensity. Do not use age, BMI, or risk-factor counts alone as automatic exclusion. | High | Preparticipation screening | The generator is not a clearance engine; ambiguity that could materially change safety returns professional review rather than a guess. | Riebe et al. 2015, DOI `10.1249/MSS.0000000000000664` |
| `CS-004` | Treat explicit clinician restrictions as hard constraints with their stated scope and duration. | High as a product safeguard | A qualified clinician restriction is supplied | Do not broaden or reinterpret a restriction; unclear or conflicting instructions require review. | EBD safety hierarchy |
| `CS-005` | A previous injury or stable chronic musculoskeletal condition opens a modification and monitoring branch; it does not automatically ban resistance training or an entire movement pattern. | Moderate-high | No acute warning sign; condition is stable enough for exercise | Recent surgery, acute injury, progressive neurological signs, clinician restrictions, or material worsening can block or narrow training. | EBD, “Common musculoskeletal limitations” |
| `CS-006` | For chronic low-back pain, favor continued tolerable exercise with adjustable load, ROM, variation, support, set count, effort, and frequency rather than universal avoidance. | Moderate | Stable chronic low-back pain and exercise is allowed | This is not permission to ignore new/worsening symptoms and does not prescribe a diagnosis-specific rehabilitation protocol. | EBD, “Chronic low-back pain”; Hayden et al. 2021 Cochrane review |
| `CS-007` | For patellofemoral pain, allow tolerable knee loading and consider both knee- and hip-targeted strengthening while adjusting depth, load, variation, and progression from response. | Moderate-high | Stable patellofemoral pain and exercise is allowed | Do not use a universal pain score or fixed ROM window; honor clinician restrictions. | EBD, “Patellofemoral pain”; Neal et al. 2024; Nascimento et al. 2018 |
| `CS-008` | For knee osteoarthritis, permit progressive resistance training but do not force high-intensity loading as inherently superior for pain or function. | Moderate-high | Stable knee OA and exercise is allowed | Individual goals and clinician guidance can still include heavy work when appropriate and tolerated. | EBD, “Knee osteoarthritis”; Messier et al. 2021 |
| `CS-009` | For rotator-cuff-related shoulder pain, test tolerable changes in grip, pressing angle, ROM, load, and modality rather than prescribing rest from all upper-body training. | Moderate | Stable shoulder condition and exercise is allowed | New trauma, marked loss of function, progressive symptoms, or clinician restrictions require review. | EBD, “Rotator-cuff-related shoulder pain” |
| `CS-010` | Do not interpret any pain during exercise as automatic tissue damage, and do not define one universal safe pain cutoff. Use behavior during and after the session. | Moderate for chronic musculoskeletal exercise; High that no universal cutoff is established | Manageable chronic musculoskeletal symptoms | Evidence about chronic therapeutic exercise does not generalize to acute injury, chest pain, neurological symptoms, or every pathology. | EBD, “Is pain during training automatically dangerous?”; DOI `10.1136/bjsports-2016-097383` |
| `CS-011` | Continue only when symptoms are absent or familiar and stable; regress load/ROM/effort or change variation when symptoms rise set-to-set; stop progression and request reassessment when worsening persists or repeats. | Low-moderate; conservative implementation | Symptom monitoring is allowed | This trajectory rule cannot declare a symptom safe; warning signs return to `CS-002`. | EBD symptom-response table |
| `CS-012` | Preserve resistance training as an option for adults with overweight or obesity and adapt accessibility or recovery from actual constraints. | High for resistance-training benefit; Moderate for adaptations | Safety gate otherwise allows exercise | Body mass alone neither grants clearance nor mandates machines, unique rep ranges, or lower-quality training. | EBD, “Users with overweight or obesity” |
| `CS-013` | Never output a diagnosis, prognosis, guarantee of safety, claim that pain is harmless, or instruction to disregard a qualified professional. | High as a product safeguard | Every user-facing result | General educational context and transparent uncertainty remain allowed. | Scope of this KB |
| `CS-014` | Return `blocked_pending_professional_review` for a relevant recent surgery, non-emergency acute injury, unstable or materially worsening known condition, or unresolved restriction that the generator cannot safely interpret. | High as a conservative product safeguard; context-specific evidence | The condition affects the requested training and `CS-002` does not require urgent action | Do not broaden the block beyond the affected training; resume only from adequate guidance or resolved state, not an LLM inference. | EBD safety hierarchy and scope |

## Gate decision procedure

```text
if a current warning symptom meets CS-002:
    blocked_urgent

elif recent surgery / acute injury / unstable condition / unresolved restriction
or materially important safety information is unknown:
    blocked_pending_professional_review

elif a stable condition, previous injury, symptom history,
or clinician instruction requires bounded changes:
    allowed_with_constraints

else:
    allowed
```

The generator must return the matched rule IDs and the exact affected scope.
It must not convert `unknown` to `allowed` merely to complete a workout.

## Symptom-response validator

Use symptom behavior, not a single number:

| Observed response | Allowed automated action |
| --- | --- |
| No symptoms, or familiar mild symptoms remain stable | Continue the current plan; progress only if all progression criteria pass. |
| Symptoms rise modestly but settle and baseline is maintained | Maintain or regress conservatively; keep monitoring. Do not label the response safe. |
| Symptoms progressively increase across sets | Stop the affected exercise for the session; reduce ROM/load/effort or select an allowed variation. |
| Material worsening persists after training or repeats across sessions | Stop automated progression, regress the affected dose, and request appropriate reassessment. |
| A new warning symptom appears | Return to the safety gate; use `blocked_urgent` when `CS-002` applies. |

The product may record a 0–10 symptom rating, but the number is contextual data,
not an autonomous clearance threshold.

## Final draft validation

Before presenting a workout, verify that:

- the safety state permits generation;
- every clinician restriction is represented as a hard constraint;
- no exercise or intensity conflicts with an active constraint;
- symptom-modified work includes a feedback plan and no guarantee of safety;
- previous injury, obesity, height, or pain location was not converted into an
  unsupported permanent ban or deterministic exercise choice;
- time-saving techniques did not bypass rest, skill, or symptom constraints;
- the output distinguishes an allowed training option from medical advice.

If any check fails, reject the draft and return the failed rule IDs. Do not let
the language model “explain away” a failed safety validator.
