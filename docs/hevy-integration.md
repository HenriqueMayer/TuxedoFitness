# Hevy integration contract

## Verification record

The official public Swagger bootstrap at
<https://api.hevyapp.com/docs/swagger-ui-init.js> was fetched without a
credential on 2026-08-30. Its SHA-256 value is:

```text
03f51bdc17537d1a530114d2ae47327d3e2863dde0d9224d2b1aa083da1e8438
```

The privately retained source capture had the same hash. The raw provider
bundle is intentionally excluded from the public repository. The
Sprint 9 release check found no contract drift. Revalidate the public bootstrap
before every release that changes the adapter.

## MVP read allowlist

Only these Hevy operations are approved for the MVP adapter:

| Purpose | Method and path |
| --- | --- |
| Validate account | `GET /v1/user/info` |
| Exercise templates | `GET /v1/exercise_templates` |
| Routine folders | `GET /v1/routine_folders` |
| Routines | `GET /v1/routines` |
| Workouts | `GET /v1/workouts` |
| Retrieve one workout | `GET /v1/workouts/{workoutId}` |
| Workout events | `GET /v1/workouts/events` |

All collection and event pages must be fetched from page 1 through
`page_count`, including the final page. Exercise templates use at most 100
items per page; the other paginated allowlisted resources use at most 10.
The routine-folder endpoint currently exposes its collection under the
provider's `routines` response key; the adapter maps that key explicitly to
local routine-folder DTOs.

Body measurements and every Hevy `POST`, `PUT`, or delete operation are
outside the MVP. Workout events apply only to workouts; plans and templates
use explicit complete refreshes.

## Secret boundary

Hevy authentication uses the backend-only `api-key` header. The key is never
stored in Git or sent in an URL. Automated tests use synthetic credentials and
mock transport; they never call the real API.

## Implemented complete import

`integrations.hevy.HevyClient` exposes only the validation and complete-import
GET paths. It starts pagination at page 1, sends the documented maximum page
size, validates `page` and `page_count`, and includes the final page. The
client retries only transient failures, with a 30-second per-request timeout
and at most three attempts.

`FullImportService` validates all DTOs and cross-resource references before
opening the canonical SQLite transaction. The repository upserts templates,
folders, routines, workouts, and their ordered children. Only a confirmed
complete collection refresh can mark absent rows inactive. The initial
`workout-events` cursor is the full-run start time; later incremental event
processing uses the workflow below.

## Incremental workout events

`IncrementalSyncService` requests `/v1/workouts/events` from the confirmed
cursor minus its five-minute overlap. It fetches every page, retains events at
or before the run high-water mark, deduplicates their type, workout ID, and
source timestamp, and applies them in ascending source order. A delete wins
when an update and delete share a timestamp.

Updated events persist their complete workout payload. A syntactically
incomplete update uses `GET /v1/workouts/{workoutId}` for repair. Deleted events
soft-delete only the matching local workout. Canonical writes and cursor
advancement share one SQLite transaction. Failed or partial retrieval leaves
the prior cursor and canonical data unchanged. A per-account local advisory
lock rejects a concurrent writer.

Run a connection check or explicit full import with:

```bash
uv run python manage.py sync_hevy --validate-only --username your-username
uv run python manage.py sync_hevy --mode=full --confirm-full-refresh \
  --username your-username
uv run python manage.py sync_hevy --mode=incremental --username your-username
uv run python manage.py sync_hevy --mode=plans --username your-username
```
