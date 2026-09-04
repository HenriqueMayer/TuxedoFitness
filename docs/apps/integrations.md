# Integrations app

`integrations` owns Hevy account identity and synchronization state:

- `HevyAccount` stores non-secret account metadata;
- `IntegrationState` stores connection and freshness timestamps;
- `SyncRun` stores state, counts, timing, versions, and sanitized failures;
- `SyncCursor` stores confirmed per-stream progress and overlap.
- `SyncLock` provides one local writer per account.
- `RoutineWriteIntent` stores a non-secret, single-use routine preview and its
  confirmed, failed, expired, or unknown result.

Sprint 3 adds the backend-only read adapter in `integrations.hevy`, validated
DTOs in `integrations.dtos`, and the complete-import coordinator in
`integrations.services`. The client accepts only HTTPS requests to the official
Hevy host and its fixed read allowlist. Management commands load
`HEVY_API_KEY` from the environment. Web requests receive a credential from the
process-local `SessionCredentialStore`; it is never written to the Django
session or a model. Reads use a 30-second timeout and at most three attempts,
and the adapter never logs payloads or headers.

`sync_hevy --validate-only` validates the configured account. A full refresh
requires both `--mode=full` and `--confirm-full-refresh`; it fetches every
page before one SQLite transaction persists normalized rows, marks confirmed
missing rows inactive, and creates the initial workout-events cursor. The
authenticated `/sincronizacao/` page exposes the same safe actions without
rendering the API key.

The same page now exposes five guided actions. Local exercise and routine
exports are produced on demand as CSV or JSON. The prompt builder combines
structured owner input, active routines, the allowed exercise catalog, and a
bounded local workout period into downloadable Markdown without external I/O.

Routine creation is the sole write allowlist entry. The validator accepts only
`{"routine": {...}}`, checks local references and modality-compatible metrics,
and creates a 30-minute preview intent. Confirmation sends exactly one
`POST /v1/routines`; timeout, 5xx, or an invalid success confirmation becomes
`WRITE_UNKNOWN` and is never retried automatically. A confirmed response is
followed by a complete plan refresh.

Sprint 4 implements the workout-events stream. It retrieves every event page
with a five-minute cursor overlap, records a run high-water mark, deduplicates
by event type, workout ID, and source timestamp, and processes events in a
stable order where an equal-timestamp delete wins. Incomplete update payloads
are repaired with the single-workout GET. Only completed workouts change;
templates, folders, and routines remain untouched. The cursor advances in the
same transaction as canonical writes, after all pages validate.

Use `--mode=incremental` for workout events and `--mode=plans` for a complete
template, folder, and routine refresh. `--retry-run <uuid>` links an
incremental retry to a failed or partial run.

Incremental synchronization requires the cursor created by a complete import;
otherwise it returns `SYNC_NOT_INITIALIZED` without acquiring a lock. A lock
older than `SYNC_LOCK_STALE_SECONDS` is recoverable, and its old running
`SyncRun` is marked failed with `SYNC_INTERRUPTED` before the new writer starts.

Command failures use stable exit classes for configuration/authentication,
transient provider errors, validation/partial results, writer conflicts, and
database errors. Output contains run metadata and sanitized counts, never the
credential or response body.

Web actions are POST-only and use the shared local services. Full refreshes
require an explicit confirmation page; retries accept only failed or partial
runs. Run detail pages show sanitized errors, counts, timing, and prior-run
links, while normal forms remain usable without JavaScript.
