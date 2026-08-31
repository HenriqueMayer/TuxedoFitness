# Architecture

## Runtime shape

Tuxedo Fitness is a single-instance, local-first Django application. It uses
server-rendered templates, native authentication, SQLite, local static assets,
strict CSP, and optional HTMX progressive enhancement. Browser code never
contacts Hevy.

```text
pages/accounts/dashboard/training views
                  |
                  v
       analytics services + local repositories
                  |
                  v
       normalized training/integration models

Hevy HTTP -> integrations adapter -> validated DTOs -> training persistence
```

| App | Responsibility |
| --- | --- |
| `core` | Settings, security checks, root routing, liveness/readiness, ASGI/WSGI. |
| `pages` | Public landing page containing synthetic presentation only. |
| `accounts` | Authentication, signup policy, preferences, backup and local deletion controls. |
| `integrations` | Provider client, DTOs, synchronization coordination, state, cursor and run audit. |
| `training` | Normalized persistence, repositories, and read-only training pages. |
| `analytics` | Deterministic formulas, eligibility, comparisons and metric metadata. |
| `dashboard` | Overview composition and presentation-only SVG read models. |

The implementation has deliberate cross-app application-service dependencies:
training views may consume analytics read services, integration orchestration
persists validated training entities, and dashboards read account/integration
freshness. Documentation does not claim a strict linear dependency graph that
the code does not enforce.

## Data and security boundaries

- SQLite, `.env`, backups, exports, diagnostics, and provider snapshots remain
  outside the tracked public tree. POSIX environment files must be mode `0600`.
- Secrets enter through a selected environment file or process environment and
  never enter models, responses, URLs, logs, fixtures, or exports.
- Canonical timestamps are aware; canonical mass/distance storage remains in
  provider units and presentation conversion happens at the template boundary.
- Synchronization validates complete provider responses before canonical
  mutation and advances cursors only in the successful write transaction.
- `research/` is provenance for a future phase and is not imported at runtime.

## Browser contract

The base body boosts ordinary GET navigation and requests complete documents;
HTMX swaps the body only after a successful response. POSTs and downloads opt
out. Dashboard filters explicitly send HTMX headers and receive
`#overview-results` only. JavaScript listeners are document-delegated so they
remain valid after a body swap.

The SVG presentation model is created from analytics read models and contains
geometry, localized labels, summaries, and table rows only. It performs no
domain calculation, persistence, or external I/O.
