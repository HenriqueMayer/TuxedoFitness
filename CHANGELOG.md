# Changelog

All notable changes to Tuxedo Fitness are documented in this file. The format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and versions
follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Made local account creation visible and available by default from the public
  landing page and login screen; `ALLOW_SIGNUPS=False` still closes registration.
- Added a process-memory, session-scoped Hevy connection flow with explicit
  disconnect and logout cleanup.
- Added exercise and routine CSV/JSON exports, deterministic history charts,
  and local prompt generation for external training analysis.
- Added strict routine JSON validation, a human-readable preview, single-use
  confirmation intents, and non-retried `POST /v1/routines` creation.

### Security

- Kept web credentials out of cookies, sessions, models, exports, prompts, and
  logs, and classified ambiguous writes without automatically retrying them.

### Fixed

- Mapped the Hevy routine-folder endpoint's `routines` response key so complete
  and plan synchronization no longer rejects valid pagination metadata.
- Restored the documented Django 6.0 and Tailwind CSS 3.4 dependency bounds
  after incompatible automated dependency updates.

### Planned

- Complete the advanced overview, exercise-history, modality, and comparison
  views described for v0.2.0 in the PRD.

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
