# Implementation status

This document records implementation truth. The PRD defines product intent,
but a requirement is considered implemented only when code and executable
evidence exist.

## Unreleased implemented

- Authenticated web users can test a Hevy key held only in process memory for
  the current session, explicitly disconnect it, and retain local data after it
  is forgotten.
- The synchronization page is now a five-action Hevy workspace for complete
  history preparation, exercise/routine CSV and JSON exports, routine creation,
  and offline prompt generation.
- Routine creation accepts strict provider-shaped JSON, validates local
  exercise/folder references and modality fields, presents a preview, consumes
  a 30-minute single-use intent, sends one non-retried provider POST, and
  refreshes local plans after confirmed success.
- The overview presents activity, set-type, RPE, and selected-exercise evolution
  as server-rendered SVG with text and table equivalents.

## v0.1.0 implemented

- Local Django 6 application, native authentication, environment-disableable signup,
  per-user presentation preferences, and protected personal routes.
- Normalized SQLite models for provider identity, exercises, routines,
  workouts, sets, synchronization state, cursors, and audited runs.
- Read-only Hevy client with an explicit GET allowlist, complete pagination,
  DTO validation, retries, atomic imports, incremental workout events, overlap,
  deduplication, locking, cursor safety, and sanitized failures.
- Deterministic local analytics for activity, duration, sets, repetitions,
  compatible load volume, modality, RPE, records, e1RM, comparisons, trends,
  target consistency, and muscle distribution.
- Overview, history, workout, exercise, routine, synchronization, settings, and
  CSV export surfaces. Some advanced analytics exist as services before they
  have dedicated product presentation.
- Global progressive HTMX navigation with ordinary HTTP fallbacks, exact
  results-island responses, stable focus/scroll/history, local assets, strict
  CSP, accessible server-rendered SVG, and equivalent tables.
- Verified SQLite backup/check/rehearsal operations, retention cleanup,
  liveness/readiness, secure deployment settings, CI, dependency audits,
  repository/history scanning, and browser checks.

## Planned for v0.2.0

- Present weekly-target consistency, average duration, and frequent exercises
  on the overview.
- Expand exercise lists with equipment, secondary muscles, custom status,
  recent activity, and compact metric summaries.
- Expand exercise detail with local set history, RPE completeness, date filters,
  period comparison, and modality-specific record presentation.
- Present distance, duration, and other non-load set modalities consistently in
  workout detail.
- Improve structured synchronization provenance and reduce cross-app coupling
  behind explicit application-service boundaries.

## Future and intentionally absent

Editing existing Hevy routines, writing workouts/folders/exercises, webhooks,
body measurements, embedded LLM calls, conversational agents, medical advice,
multi-tenancy, queues, and distributed infrastructure remain absent.

## Release evidence

The release gate and current commands are authoritative in
[`testing.md`](testing.md). All tests use synthetic data and mocked provider
transport. The repository must not be made public until its sanitized history
passes `scripts/security/scan_secrets.py --history` from a fresh remote mirror.
