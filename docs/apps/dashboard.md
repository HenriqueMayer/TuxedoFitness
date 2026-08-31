# Dashboard app

`dashboard` owns the authenticated root overview, period/comparison form, KPI
cards, freshness summary, and shared application shell. It consumes
`AnalyticsService` read models and never calculates domain formulas or calls
Hevy. Empty and insufficient-data states remain explicit.

The Sprint 6 overview supports inclusive local periods, opt-in comparison with
the preceding equal period, and confirmed local workout metrics. History and
exercise read surfaces live in `training` and use the same authenticated shell.

`DashboardPresenter` creates typed localized SVG geometry, summaries,
equivalent tables, and explicit empty states without recalculating analytics.
HTMX 2.0.10 enhances the GET period form, which keeps the same complete
server-rendered response when JavaScript is disabled.

The chart/table series is capped at 2,000 points and history remains paginated,
preserving bounded responses on long accounts.
