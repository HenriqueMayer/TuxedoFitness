# Future training research

This directory separates **reference data**, used for calibration and analysis,
from **prescription rules**. These datasets must not be used to diagnose or
treat injuries, or to decide whether an exercise is safe for a specific person.

This material belongs to the future conversational-agent roadmap. The Tuxedo
Fitness analytics MVP must not load it at runtime.

## Knowledge layers

Workout-generation knowledge is intentionally separated from population data:

- [`knowledge_base/`](knowledge_base/) contains the reviewed operational rules
  that the generator and validator may execute;
- [`reports/`](reports/) contains the underlying reports for evidence review
  and provenance, not direct runtime instructions;
- [`datasets/raw/`](datasets/raw/) and
  [`datasets/processed/`](datasets/processed/) contain reference datasets for
  analysis and calibration, not prescription rules.

The generator should always load clinical safety, workout programming, and
exercise selection. Biomechanics, progression, and time-efficiency guidance are
loaded only when their documented triggers apply. See the
[`knowledge_base` loading contract](knowledge_base/README.md) for the exact
precedence and rule schema.

## Getting started

Download the small, reproducible, primary-source dataset collection:

```bash
uv run python scripts/research/fetch_priority_datasets.py
```

This creates `research/datasets/raw/nhanes_2021_2023/`,
`research/datasets/raw/nhanes_2017_2018/`, and
`research/datasets/raw/nhanes_2013_2014/`. The source files use SAS Transport
(`.xpt`) and are excluded from Git. Each directory contains a `README.md`
describing its source, survey cycle, and join key.

Then generate the working formats:

```bash
uv run scripts/research/prepare_readable_data.py
```

The results are written to `research/datasets/processed/`: curated CSV files
for direct use and complete Parquet files containing every original column.

The machine-readable source catalog is available in
[`dataset_catalog.json`](dataset_catalog.json). Read the documentation linked
for each source before using it: variable definitions, eligibility rules,
sample weights, and limitations are part of the data.

## Recommended order of use

1. **NHANES 2021--2023:** the primary current population reference for height,
   weight, BMI, waist and hip circumferences, arm and leg lengths, reported
   physical activity, and reported medical conditions.
2. **NHANES 2017--2018:** preserves body composition measured with DXA. Use it
   as a historical complement, not as a description of the current population.
3. **NHANES 2013--2014:** adds dynamometer-measured grip strength linked to body
   measures and demographics. Do not pool it with another survey cycle without
   following the NHANES survey-design and weighting guidance.
4. **ANSUR II:** use only to explore relationships among body dimensions that
   NHANES does not measure. Its U.S. military sample does not represent the
   civilian population.
5. **MHEALTH, PhysioNet, and instrumented studies:** use for sensor ingestion,
   movement-recognition prototypes, and pipeline tests. Their small samples are
   not standards for technique, injury risk, or training load.

## Product and safety boundaries

- Anthropometry can suggest adaptations to evaluate; it cannot determine one
  universally correct posture or replace an in-person assessment.
- Self-reported health data and research datasets must not directly generate
  clinical recommendations. Pain, musculoskeletal conditions, recent surgery,
  and cardiovascular symptoms require conservative screening and professional
  referral when appropriate.
- Use NHANES sample weights (`WTMEC2YR` for analyses that include examination
  data) for population estimates. Follow the documentation for each survey
  cycle and component; `SEQN` is a join key only within the same cycle.
- Record the source version, URL, download date, and transformations for each
  experiment. Never combine participants, protocols, or equipment conditions
  without an explicit provenance field.

## Formats

- `datasets/processed/curated/*.csv`: participants aged 18 or older, a focused set of
  columns, descriptive names, and decoded categorical values. This is the layer
  for human inspection and prototypes. The adult-only scope avoids implying a
  pediatric use case without pediatric prescription evidence.
- `datasets/processed/full/**/*.parquet`: every original column, compressed and with
  types preserved. This is the layer for analyses that need to revisit the
  complete source.
- `datasets/raw/**/*.xpt`: immutable files published by the CDC. This is the audit layer.

`datasets/processed/data_dictionary.csv` documents each curated column, its
unit, source variable, and caveats. A blank value never automatically means
"no": it may be missing, outside the participant's age eligibility, or skipped
by the survey's questionnaire flow.

Large open datasets and sources with specific access terms are not downloaded
automatically. Their purpose, size, access conditions, and limitations are
recorded in the catalog so ingestion can be an explicit decision.
