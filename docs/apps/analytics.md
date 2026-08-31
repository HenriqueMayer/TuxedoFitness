# Analytics app

`analytics` is the deterministic metric boundary. It reads confirmed active
rows through `training` models and returns `MetricResult` values with formulas,
units, filters, eligibility, missing-data counts, and limitations. It has no
Hevy client, persistence responsibility, dashboard dependency, or chart
runtime dependency.

Sprint 5 introduces `AnalyticsService` for local periods, activity, duration,
sets, repetitions, compatible volume, modality results, RPE, records, Epley
e1RM, comparisons, trends, target consistency, streaks, and executed muscle
distribution. See [`analytics.md`](../analytics.md) for the normative formulas.

The overview read model also exposes deterministic weekly or monthly activity
buckets for the dashboard presenter. Chart aggregation is presentation-only;
the metric formulas and source values remain owned by this app.
