# Standalone scripts

These utilities support repository maintenance and research. They are not
Django application services.

| Path | Purpose | Output boundary |
| --- | --- | --- |
| `hevy/export_snapshot.py` | Create a private, read-only snapshot of current Hevy routines and exercise templates. | `var/private/hevy-snapshots/` |
| `research/fetch_priority_datasets.py` | Download approved public research datasets. | `research/datasets/raw/` |
| `research/prepare_readable_data.py` | Create curated CSV and full Parquet research outputs. | `research/datasets/processed/` |
| `benchmark_reference_corpus.py` | Build the disposable 10k-workout/200k-set corpus and measure warm requests. | Temporary directory removed after the run. |
| `check_version.py` | Validate the SemVer contract across metadata, lockfile, README, changelog, and tags. | No output file. |
| `security/scan_secrets.py` | Scan the tracked tree and optionally all reachable Git objects without printing suspected values. | No output file. |

The Django Hevy adapter and synchronization command are the product source of
truth. The standalone snapshot utility writes private audit material only.
Research scripts remain outside the runtime dependency path.
