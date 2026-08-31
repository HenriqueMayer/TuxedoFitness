# Analytics formulas

Sprint 5 provides the deterministic, local-only metric boundary in
`analytics/services.py`. It reads active normalized workouts and never calls
Hevy or raw snapshot files. The dashboard can consume these results without
reimplementing formulas.

## Shared contract

`MetricResult` exposes `metric_id`, `name`, `question`, `value`, `unit`,
`definition`, `filters`, `formula_version`, `included_set_types`,
`source_entity_count`, `missing_value_count`, `validity`, `limitation`, and
`data_freshness`. Values are `Decimal` where arithmetic precision matters;
missing inputs remain `None` and produce an `insufficient_data` result when a
metric has no eligible observations.

Periods are inclusive local calendar dates. A missing period defaults to the
last 28 days including today, using the owner's presentation timezone. The
database remains UTC-aware and is only converted at the analytics boundary.

## Implemented formulas

| Area | Formula and eligibility |
| --- | --- |
| Activity | Distinct active workouts, local training dates, weekday counts, and `workouts / days × 7` frequency. |
| Duration | `Σ(end_time - start_time)` and arithmetic mean; malformed or missing durations are excluded. |
| Sets | Total rows, counts by `warmup`/`normal`/`failure`/`dropset`, and working sets only when the type is non-warmup and the template has a compatible recorded metric. |
| Repetitions | Sum non-null `reps` on rep-based templates; null is never treated as zero. |
| External-load volume | `Σ(weight_kg × reps)` only for positive `weight_reps` working sets. Other modalities are not aggregated into volume. |
| Modality results | Per-template repetitions, assistance/load, duration, distance, and custom totals remain separate. |
| RPE | Mean, median, distribution, and missing count/percentage over working sets with recorded RPE. |
| Records | Maximum load, repetitions at exact load, largest compatible set volume, and maximum estimated 1RM per template. |
| Estimated 1RM | Epley `weight × (1 + reps / 30)` for normal/failure `weight_reps` sets with positive weight and integer reps from 1 through 10. It is always labeled an estimate. |
| Comparison | Equal-period `current - previous`; percentage is omitted when the previous value is zero or null. |
| Trend | Ordinary least-squares slope scaled to the requested number of days; fewer than two points are insufficient. |
| Muscle distribution | Each working set is counted once for the executed primary muscle. Secondary muscles are a separate association count with no fractional weighting. |
| Weekly target and streak | Complete local Monday–Sunday weeks only; current partial week is in progress. Activity streaks count consecutive active calendar weeks. |

`AnalyticsService.build_overview()` groups these read models for the next
dashboard sprint. Planned routine muscles are intentionally not mixed with
executed workout distribution.

The overview also includes `activity_buckets`, a deterministic count keyed by
the local Monday of each week (periods up to 365 days) or the first day of each
month (longer periods). It is a presentation input only; absent buckets remain
zero activity while missing metric inputs elsewhere remain `None`.

## Synthetic fixtures

`analytics/tests.py` covers hand-calculated activity, duration, set counts,
null handling, volume, RPE, Epley eligibility, modality separation, muscles,
period comparison, and local timezone boundaries. These fixtures are local
database tests; they do not perform network I/O.
