# Prompt → JSON → Hevy

The template `tuxedo-training/2.0` combines system-instruction text, user comments/profile, provenance, original routine pages, original selected workout objects, allowed exercise IDs/modalities, analysis instructions and the shared import contract. The entire copied document is a user message in an external chat; Fitness does not configure that tool's system role and never sends the document itself.

Default: last 28 local dates, including today. Last seven days means today and six preceding dates. Last month subtracts one calendar month (clamping month-end). Custom dates are inclusive; last N uses newest start times and presents selected objects chronologically. Missing history/routines is explicit. Missing valid catalogue or original payloads blocks generation. The 6 MiB limit fails explicitly without truncation; token size is an estimate (~characters/3).

Preview displays effective dates, sessions/routines and size. Saving verifies a signed user/text-hash preview with a 15-minute lifetime. A generation stores its final text, input snapshot, template version and source manifest. Subsequent syncs cannot alter it. Copy/download/duplicate/delete are owner-scoped. Suggested model: Claude Opus 5, reviewed 2026-09-05, [official source](https://www.anthropic.com/news/claude-opus-5); use extended reasoning where available. The template remains provider-independent.

## Envelope v1

```json
{"schema_version":1,"api_key":"{{HEVY_API_KEY}}","operations":[{"action":"create","routine":{"title":"Example","folder_id":null,"notes":"Adapt to the user","exercises":[{"exercise_template_id":"ID_FROM_CATALOGUE","superset_id":null,"rest_seconds":90,"notes":"Intended RPE belongs in notes","sets":[{"type":"normal","rep_range":{"start":8,"end":12}}]}]}}]}
```

The ID is a placeholder for a real catalogue ID. Generated examples use an actual allowed ID and are tested with the same validator as imports. Update requires routine_id from the connected account; create forbids it. A routine body is the complete replacement prescription, not a patch. Unlisted routines stay unchanged.

Parse pure JSON or one fenced `json` block with explanation. Reject duplicate keys, nonfinite numbers, unknown fields, real keys, foreign IDs, repeated updates, invalid modalities, folders, supersets and missing prescriptions. Errors identify zero-based field paths. Real key input clears the document rather than echoing it. Limit: 2 MB, 1–20 operations, 1–50 exercises/routine, 1–20 sets/exercise and 64 KB per provider body.

Supported types: warmup, normal, failure, dropset. Fields: weight_kg, reps, rep_range, distance_meters, duration_seconds, custom_metric subject to modality. Omit unused rep_range. RPE is not writable prescription data; put intended effort in notes. Response IDs/timestamps/indexes are not writable fields. Each call sends only `{"routine": ...}`; the resolved credential goes only into `api-key` on the allowlisted Hevy host.

Preview fetches current remote versions for updates and stores hashes. Confirmation revalidates all operations and versions before dispatch. External changes require another preview. The API offers no atomic batch contract: operations run sequentially and stop at the first failure or unknown result; there is no remote rollback or automatic write retry. Results distinguish succeeded, failed, unknown and not_executed. Successful writes followed by failed local refresh are explicitly marked pending; never repeat a successful operation. An interrupted submitting operation is recovered as unknown after stale-lock recovery.
