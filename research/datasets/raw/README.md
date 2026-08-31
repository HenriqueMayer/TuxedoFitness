# Local raw data

This directory receives reproducible downloads from
`scripts/research/fetch_priority_datasets.py`. Downloaded data files are
excluded from Git; only small provenance and context files are versioned.

Do not modify the raw files. Transformations must create a separate derived
table with source provenance, source version, and schema validation.
