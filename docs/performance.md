# Reference-corpus performance

The reproducible benchmark builds a disposable SQLite database with 10,000 workouts, 10,000 workout exercises, 200,000 workout sets and 100 exercise templates. It performs one warm request followed by 20 measured requests per surface and deletes the temporary database afterward. Source code, credentials and real owner data are excluded from the corpus.

```bash
uv run python scripts/benchmark_reference_corpus.py
```

## Result — 2026-09-05, version 0.2.0

Local Linux x86_64 environment: Python 3.12.13, Django 6.0.8 and SQLite 3.50.4. [Machine-readable results](benchmarks/0.2.0.json).

| Surface | p95 | Target | HTML size | Result |
| --- | ---: | ---: | ---: | --- |
| Overview | 0.642 s | ≤ 1.5 s | 26.6 KiB | Pass |
| History with `set_type=normal` | 0.795 s | ≤ 1.0 s | 19.7 KiB | Pass |
| Exercise search with `q=Exercise` | 0.028 s | ≤ 1.0 s | 21.5 KiB | Pass |
| Analysis: frequency | 0.256 s | ≤ 1.5 s | 37.0 KiB | Pass |
| Analysis: progression | 0.096 s | ≤ 1.5 s | 42.2 KiB | Pass |
| Analysis: effort | 0.252 s | ≤ 1.5 s | 93.6 KiB | Pass |
| Analysis: volume | 0.174 s | ≤ 1.5 s | 95.5 KiB | Pass |
| Analysis: distribution | 0.182 s | ≤ 1.5 s | 34.3 KiB | Pass |
| Analysis: duration | 0.171 s | ≤ 1.5 s | 91.7 KiB | Pass |

Analysis requests cover all exercises unless the panel requires an exercise selection: progression uses the first synthetic exercise. All responses stay below the 1.5 MiB uncompressed HTML limit. History uses a 25-row look-ahead window instead of an exact total-count query; the catalogue uses 50-row pages.

Measurements use Django's local test client and include local request/render/database work. They exclude browser paint and Hevy/network latency. Provider latency was not measured because the verification made no live provider calls. These are reproducible local development observations, not a production service-level agreement. Run again after query, schema, Django or SQLite changes.


## Revision verification — 2026-09-07

The same 10,000-workout / 200,000-set corpus now includes comparison requests.
The distribution code caches translated category labels per request.
[Machine-readable results](benchmarks/2026-09-07.json).

| Surface | p95 | Response |
|---|---:|---:|
| dashboard | 0.252 s | 34.3 KiB |
| history_filter | 0.279 s | 36.9 KiB |
| exercise_filter | 0.016 s | 33.2 KiB |
| reports/frequency | 0.080 s | 47.8 KiB |
| reports/progression | 0.028 s | 59.8 KiB |
| reports/effort | 0.094 s | 103.4 KiB |
| reports/volume | 0.085 s | 102.5 KiB |
| reports/distribution | 0.083 s | 48.7 KiB |
| reports/duration | 0.086 s | 99.4 KiB |
| comparison/progression | 0.032 s | 63.5 KiB |
| comparison/volume | 0.116 s | 105.3 KiB |
| comparison/distribution | 0.115 s | 51.4 KiB |

All existing time and response-size gates passed. These are local measurements,
not provider latency or a production SLA.
