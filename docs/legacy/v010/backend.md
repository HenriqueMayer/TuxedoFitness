# Backend

## Baseline

The backend targets Python 3.12 or later and Django `>=6.0,<6.1`. Dependencies
are declared in `pyproject.toml` and locked with `uv.lock`.

`core/settings.py` loads the root `.env` through `python-dotenv`; real process
variables take priority. `SECRET_KEY` is required. `DEBUG`, `ALLOWED_HOSTS`,
`HTTPS`, `CSRF_TRUSTED_ORIGINS`, `TUXEDO_DATA_DIR`, `TUXEDO_FITNESS_DB`, and
`TUXEDO_ENV_FILE`, `ALLOW_SIGNUPS`, and `SYNC_LOCK_STALE_SECONDS` control
the local runtime without storing secrets in models.

## Security

- Every personal route uses `LoginRequiredMixin`.
- `/conta/cadastro/` creates a native Django user by default. Setting
  `ALLOW_SIGNUPS=False` closes registration with 403 without disabling login.
- Logout accepts POST only and includes CSRF protection.
- CSP permits executable and presentation assets from `'self'` only, rejects
  inline event handlers, frames, and plugins, and limits forms to the same
  origin.
- Secure cookies, HTTPS redirect, and HSTS activate with `HTTPS=True`.
- Referrer, MIME-sniffing, opener, and frame protections are explicit.
- The private data directory is mode `0700` on POSIX; environment files and
  backups are mode `0600`.
- `/health/` is database-independent liveness. `/ready/` verifies that SQLite
  can answer a query.

## Persistence and presentation

SQLite defaults to `var/private/tuxedo-fitness.sqlite3`. Django uses aware
timestamps, Brazilian Portuguese interface text, and
`America/Sao_Paulo` presentation time.

SQLite runs in WAL mode with `synchronous=NORMAL`, a 20-second busy timeout,
and immediate write transactions. This is still a single-instance,
single-writer deployment; it is not shared-network or multi-replica storage.

Sprint 2 adds account-scoped integration state and normalized exercise,
routine, and workout tables. Decimal fields preserve canonical units without
binary floating-point storage. Database constraints protect external identity,
child order, rep ranges, RPE, and time ranges. Model validation rejects naive
source timestamps and cross-account references.

Active synchronized rows are the default query surface. Audit and sync code can
use explicit unfiltered managers. `TrainingRepository` provides local reads and
soft deletion without importing an HTTP client. Its full-import persistence
operation replaces ordered child rows inside the caller's transaction and
upserts parent rows by account-scoped external identity.

The Hevy adapter is the only HTTP boundary. Management commands read
`HEVY_API_KEY` from the environment; authenticated web flows use a
process-local credential bound to the current Django session. The adapter
accepts only the official HTTPS host, approved GET paths, and the explicitly
confirmed routine-creation POST. It uses standard-library transport with a
30-second timeout. DTO validation
normalizes UTC timestamps, IDs, decimals, nullable metrics, planned rest, and
recorded RPE before the repository is called.

Sprint 4 adds event DTOs and an incremental coordinator. It uses the stored
cursor minus a five-minute overlap, a run high-water mark, deterministic event
ordering, and a single transaction for workout writes and cursor confirmation.
Only an incomplete updated-workout event may trigger the allowed repair GET.

Sprint 5 adds the local-only analytics boundary. `AnalyticsService` converts
inclusive local calendar dates using the owner's presentation timezone, reads
active normalized workouts, keeps `Decimal` arithmetic for loads and formulas,
and returns metadata-rich `MetricResult` objects. Null values stay null and
incompatible exercise modalities never enter external-load volume or e1RM.

Sprint 7 keeps web synchronization behind the existing integration services and
uses POST-only authenticated actions. Routine and export reads are account
scoped. `accounts.services.create_verified_backup` writes an integrity-checked
SQLite backup outside the checkout; settings deletes account-scoped rows only
after that backup succeeds and the owner confirms `EXCLUIR`.

The presentation-only `DashboardPresenter` consumes weekly or monthly activity
buckets and returns typed SVG geometry, localized labels, summaries, and table
rows. No chart code calls Hevy, recalculates domain formulas, or writes SQLite.

`HistoryPreparationService` builds non-persistent chart read models from
normalized workouts. `RoutinePayloadValidator` checks provider-shaped JSON
against local templates and folders. `RoutineWriteIntent` makes confirmations
single-use without storing the credential; ambiguous remote results remain
auditable and require a plan refresh before any new attempt.

Sprint 9 adds verified backup and SQLite-check management commands. The backup
uses SQLite's online backup API, then requires both `integrity_check=ok` and an
empty foreign-key check. The restore rehearsal copies only a synthetic backup
to an isolated temporary directory.

Presentation preferences convert canonical kilograms and metres only when
rendering HTML. CSV exports and stored values remain kilograms, metres, and
seconds. The daily `prune_runtime_data` command applies the 0–30 day private
snapshot preference and retains sync runs for 180 days while always keeping
the newest 20 per account.

## Conventions

- Code and technical documentation use English.
- Fixed interface text uses Brazilian Portuguese.
- Domain rules do not live in views or templates.
- External calls remain behind `integrations`.
- Persistence operations remain behind `training` models and repositories.
- New abstractions require a current use.
