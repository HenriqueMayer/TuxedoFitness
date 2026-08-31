# Research archive

This directory preserves the evidence reports used to build the operational
knowledge base. These files provide provenance and review context; they are not
runtime instructions for the workout generator.

| File | Status | Permitted use |
| --- | --- | --- |
| [`evidence_based_workout_design.md`](evidence_based_workout_design.md) | Principal scientific synthesis | Primary source for drafting and reviewing operational rules |
| [`biomechanics_research_original.md`](biomechanics_research_original.md) | Original report, retained for traceability | Background and source discovery only; no direct normative use |

The original biomechanics report contains useful mechanisms and references,
but also deterministic claims that the evidence synthesis does not support.
Examples include a universal maximum recoverable volume above 20 weekly sets,
BMI- or somatotype-specific training dose, mandatory exercise selection from
body proportions, universal spinal-flexion avoidance, and claims that machines
eliminate lumbar or joint loading. Those claims must not enter generated
programs unless they are independently reviewed and added to the operational
knowledge base with conditions, exceptions, confidence, and provenance.

The generator must load files from [`../knowledge_base/`](../knowledge_base/),
not retrieve passages from this directory as executable rules. When a research
update changes an operational conclusion, update the relevant rule and its
source field explicitly so that the change is reviewable in Git.
