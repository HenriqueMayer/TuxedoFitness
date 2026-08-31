# Reference-corpus performance

The reproducible benchmark builds a disposable SQLite database with 10,000
workouts, 10,000 workout exercises, 200,000 workout sets, and 100 exercise
templates. It performs one warm request followed by 20 measured requests per
surface and deletes the temporary database afterward.

```bash
uv run python scripts/benchmark_reference_corpus.py
```

## Result — 2026-08-30

Development machine: Linux x86_64, Intel Core i7-1365U (12 logical CPUs),
Python 3.12.13, Django 6.0.8, and SQLite 3.50.4.

| Surface | p95 | Target | HTML size | Result |
| --- | ---: | ---: | ---: | --- |
| Overview | 0.192 s | ≤ 1.5 s | 22.6 KiB | Pass |
| History with `tipo=normal` | 0.286 s | ≤ 1.0 s | 23.7 KiB | Pass |
| Exercise search with `q=Exercise` | 0.007 s | ≤ 1.0 s | 24.8 KiB | Pass |

All responses remain below the 1.5 MiB uncompressed HTML limit. The history
uses a 25-row look-ahead window instead of an exact total-count query; this
keeps navigation bounded without scanning the full set corpus merely to render
a page count. The exercise catalogue uses 50-row pages.

These values are local development evidence, not a production service-level
agreement. Run the command again after query, schema, Django, or SQLite changes.
