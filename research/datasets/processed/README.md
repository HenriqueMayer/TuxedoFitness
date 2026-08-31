# Processed data

This directory is generated with:

```bash
uv run scripts/research/prepare_readable_data.py
```

## Curated CSV files

All three CSV files include participants aged 18 or older. The project does not
currently include evidence or rules for pediatric exercise prescription. Data
for other ages remain available in the complete Parquet files.

- `curated/population_reference_2021_2023.csv`: current population reference
  with anthropometry, reported physical activity, and reported health
  conditions.
- `curated/body_composition_2017_2018.csv`: historical DXA body composition,
  including fat mass, lean mass, and bone mineral content and density.
- `curated/grip_strength_2013_2014.csv`: historical dynamometer-measured grip
  strength linked to body measures and demographics.

Column names are descriptive, categorical codes are decoded, and special
numeric responses such as refusal or unknown have separate response-status
columns. See `data_dictionary.csv` for definitions, units, source variables,
and caveats.

## Complete Parquet files

`full/` preserves every table and column published by the CDC, using the
original column names and compressed Parquet files. SAS numeric missing-value
markers are normalized to null. Use these files when an analysis requires a
variable that was not selected for a curated CSV.

A blank value in a CSV does not automatically mean "no". It may mean missing,
not applicable for the participant's age, or intentionally skipped by the
questionnaire flow. The complete tables and official codebooks remain the
audit sources.
