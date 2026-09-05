# Release notes

## 0.1.0 — 2026-08-31

Tuxedo Fitness 0.1.0 is the first public local-first release. It provides
read-only Hevy synchronization, normalized SQLite history, deterministic
analytics, authenticated server-rendered pages, accessible SVG and tables,
CSV export, local preferences, and verified backup/recovery controls.

The application now uses global progressive HTMX navigation while preserving
ordinary links and forms. Dashboard filtering replaces only its results
island, so the existing page remains visible until a complete server response
arrives. Plotly and its 4.8 MB browser asset were removed.

## Known limits and operator responsibilities

- Signup is closed by default. Create the first owner with `create_owner` and
  enable `ALLOW_SIGNUPS` only intentionally.
- The Hevy contract is external and can change. Workout events are incremental
  only for workouts; plans, folders, and templates need an explicit refresh.
- SQLite supports one application writer. Multiple replicas and network-shared
  SQLite are unsupported.
- The operator owns HTTPS termination, host restrictions, owner-only secret
  permissions, scheduling, off-checkout backups, and restore rehearsals.
- This release does not present every analytics service in the UI. The exact
  v0.2.0 product gaps are recorded in the PRD and implementation status.
- Tuxedo Fitness is not affiliated with Hevy and is not a medical product.
