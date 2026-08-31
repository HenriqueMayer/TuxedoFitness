# Changelog

All notable changes to Tuxedo Fitness are documented in this file. The format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and versions
follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

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
