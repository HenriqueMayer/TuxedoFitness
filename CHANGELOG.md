# Changelog

All notable changes to Tuxedo Fitness are documented in this file. The format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and versions
follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

No additional changes.

## [0.2.0] - 2026-09-05

### Breaking

- Fresh local database required; no supported migration of 0.1.x users or test data. The default private directory is `var/private/v020`.
- Hevy credentials move from session-only storage to per-user encrypted persistence with a separate installation key ring.
- Stable English routes and native EN/PT-BR gettext replace the old guided screens.

### Added

- Tuxedo family shell and parity contract pinned to Finance `90cfe53`, local assets and both themes.
- Access-triggered/manual sync with daily catalogue cache, original provider snapshots and read aliases.
- Full-history browsing, bilingual catalogue, routine folders, six configurable analysis topics, favorites and exports.
- Optional training profile, versioned immutable prompt generations, original API context and offline copy/download.
- Batch routine envelopes, whole-batch validation, remote comparisons, expiring single-use confirmations and per-operation outcomes.
- Key rotation, synthetic contract tests, branch coverage, isolated E2E/capture tooling and bilingual static preview.

### Reliability

- Provider writes never retry ambiguous outcomes; partial successes and pending local refresh remain visible.
- Same-path updates preserve scroll/focus; SVG charts include keyboard interaction and equivalent tables.
- Documentation distinguishes synthetic tests from real Hevy operations.


## [0.1.0] - 2026-08-31

### Added

- Local-first Django application with native authentication, normalized SQLite
  training history, read-only Hevy synchronization, deterministic analytics,
  CSV export, preferences, verified backups, and database health checks.
- Responsive public and authenticated surfaces with local assets, strict CSP,
  light/dark themes, accessible server-rendered SVG and equivalent tables.
- Reproducible Python/frontend lockfiles, CI, dependency audits, secret/history
  scanning, coverage gates, and desktop/tablet/mobile Playwright checks.

### Changed

- Made signup closed by default while preserving explicit opt-in registration.
- Moved HTMX to the application shell and narrowed dashboard updates to the
  results island, preserving content, focus, scroll, URL, and no-JavaScript use.
- Replaced Plotly with a typed server-rendered SVG presentation model.

### Security

- Enforced owner-only permissions for the local environment file on POSIX.
- Removed private snapshots and unlicensed raw vendor captures from the public
  release tree and prepared a new sanitized repository history.

[Unreleased]: https://github.com/HenriqueMayer/TuxedoFitness/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/HenriqueMayer/TuxedoFitness/releases/tag/v0.1.0
