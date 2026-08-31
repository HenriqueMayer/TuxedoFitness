# Endpoint reference

Base URL: `https://api.hevyapp.com`
Required header on every endpoint: `api-key: <HEVY_API_KEY>`

## User

| Method and path | Purpose | Response |
| --- | --- | --- |
| `GET /v1/user/info` | Validate the connection and identify the account. | `{ "data": { "id", "name", "url" } }` |

## Exercise templates

| Method and path | Purpose | Parameters/body |
| --- | --- | --- |
| `GET /v1/exercise_templates` | List the account's available exercise catalogue. | `page`, `pageSize` (max. 100) |
| `GET /v1/exercise_templates/{exerciseTemplateId}` | Retrieve one template. | Path ID |
| `POST /v1/exercise_templates` | Create a custom template; returns `{ "id" }`. | `exercise.title`, type, equipment, muscle group, optional secondary muscles |

A returned template contains `id`, `title`, `type`, `primary_muscle_group`,
`secondary_muscle_groups`, `equipment_category`, and `is_custom`. Creation may
return `403` if the custom-exercise limit has been reached.

## Routines and folders

| Method and path | Purpose | Parameters/body |
| --- | --- | --- |
| `GET /v1/routines` | List planned routines. | `page`, `pageSize` (max. 10) |
| `POST /v1/routines` | Create a planned routine. | `{ "routine": { ... } }` |
| `GET /v1/routines/{routineId}` | Retrieve a complete routine. | Path ID |
| `PUT /v1/routines/{routineId}` | Update a routine. | `{ "routine": { ... } }` |
| `GET /v1/routine_folders` | List routine folders. | `page`, `pageSize` (max. 10) |
| `POST /v1/routine_folders` | Create a folder at index 0. | `{ "routine_folder": { "title": "..." } }` |
| `GET /v1/routine_folders/{folderId}` | Retrieve one folder. | Path ID |

A routine contains `id`, `title`, `folder_id`, `updated_at`, `created_at`, and
exercises. Routine exercise payloads support rest, notes, set type, weights,
reps, rep ranges, distance, duration, custom metric, and supersets.

## Workouts (completed sessions)

| Method and path | Purpose | Parameters/body |
| --- | --- | --- |
| `GET /v1/workouts` | List complete sessions. | `page`, `pageSize` (max. 10) |
| `GET /v1/workouts/count` | Retrieve only the session count. | — |
| `GET /v1/workouts/{workoutId}` | Retrieve one complete session. | Path ID |
| `POST /v1/workouts` | Record a session. | `{ "workout": { ... } }` |
| `PUT /v1/workouts/{workoutId}` | Edit a session. | `{ "workout": { ... } }` |
| `GET /v1/workouts/events` | Sync updates and deletions. | `since`, `page`, `pageSize` (max. 10) |

`GET /v1/workouts/count` returns `{ "workout_count": 42 }`. A workout
contains its ID, title, optional routine ID, description, start/end times,
creation/update timestamps, and nested exercises/sets. The write payload
supports set type, weights, reps, distance, duration, custom metric, and RPE.

## History and measurements

| Method and path | Purpose | Parameters/body |
| --- | --- | --- |
| `GET /v1/exercise_history/{exerciseTemplateId}` | Retrieve historical exercise sets. | Optional ISO 8601 `start_date`, `end_date` |
| `GET /v1/body_measurements` | List body measurements. | `page`, `pageSize` (max. 10) |
| `POST /v1/body_measurements` | Create a measurement for a date. | `BodyMeasurement`; duplicate date returns `409` |
| `GET /v1/body_measurements/{date}` | Retrieve a measurement. | `date` as `YYYY-MM-DD` |
| `PUT /v1/body_measurements/{date}` | Replace a measurement. | Omitted fields become `null` |

`BodyMeasurement` requires `date`. Optional fields are `weight_kg`,
`lean_mass_kg`, `fat_percent`, `neck_cm`, `shoulder_cm`, `chest_cm`, both
biceps and forearms, `abdomen`, `waist`, `hips`, both thighs, and both calves.

## Read examples

```bash
# Every template on the first page (documented maximum)
curl --fail-with-body --silent --show-error \
  -H "api-key: $HEVY_API_KEY" \
  "$HEVY_API_BASE_URL/v1/exercise_templates?page=1&pageSize=100"

# Bench-press history in 2026
curl --fail-with-body --silent --show-error \
  -H "api-key: $HEVY_API_KEY" \
  --get "$HEVY_API_BASE_URL/v1/exercise_history/D04AC939" \
  --data-urlencode 'start_date=2026-01-01T00:00:00Z' \
  --data-urlencode 'end_date=2026-12-31T23:59:59Z'
```
