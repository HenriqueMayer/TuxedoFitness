# Hevy integration · adapter review 2026-09-05

Primary source: [official Hevy API documentation](https://api.hevyapp.com/docs/). Local source notes are in [Hevy](Hevy/README.md). Hevy Pro is required. The public contract does not expose an exercise-language query parameter.

Reads are restricted to the official HTTPS host and allowlisted paths. Redirects are not followed, preventing forwarding of `api-key`. The bounded HTTP client retries transient reads, respects bounded Retry-After, validates JSON/page metadata and preserves original pages. Known read aliases are `equipment` / `equipment_category` and `superset_id` / `supersets_id`; contradictory values fail validation. Writes emit `superset_id` only.

Full connection imports exercise templates, routine folders, routines and workouts. Collection pagination starts at 1 and ends at page_count; routine folders use the response key `routines`. Incomplete/changing pagination must not publish a collection or advance the event cursor. Original routine pages are persisted atomically with normalized routines. Latest original workout objects follow the normalized workout update.

After-load `POST /sync/auto/` reserves the next automatic attempt and performs due work in a separate request. Workouts/routines: 15 minutes; catalogue: 24 hours. The manual header form uses the same service, including without JS. No distributed job system is needed. Records render immediately from SQLite; a provider failure preserves the last valid local state. Filters do not force fresh network collection while the reservation/data remains current.

Incremental workout events overlap the previous high-water time and deduplicate upserts/deletes. Routines/folders use complete collections because workout events do not cover them. An account lock prevents sync/write overlap. Calls are outside canonical persistence transactions; validation precedes publication. Stale locks are recovered after the installation-configured lifetime, and interrupted writes become unknown.

One HevyAccount belongs to each user. Credentials are encrypted using an installation MultiFernet key ring. Saving a replacement validates the remote identity; a different account is rejected before data can mix. Disconnect clears ciphertext and stops access-triggered synchronization, preserving local records. CLI `sync_hevy --username ...` uses the same stored credential.

Provider writes are only reachable through a reviewed, owner-scoped proposal. POST creates; PUT updates by ID. The Fitness envelope is never sent remotely. Header `api-key` is injected in the backend, and the body is only `{"routine": ...}`. Response-only fields and RPE are excluded. No writes are retried automatically, including timeouts and invalid successful confirmations. Read the [complete proposal contract](planning.md).

## Portuguese catalogue

Reviewed terminology lives in `training/translations.py`. Exact known standard exercise titles are matched during import, and the resulting display translation is stored against that account's provider exercise ID with a review version. Original payloads/IDs remain unchanged. Custom exercises and unmatched names keep their original titles. Search includes both names. This initial vocabulary is intentionally finite; new exercises remain usable until a reviewed mapping is added. This is local terminology, not an official Hevy translation service.
