# Data model and training semantics

## Core entities

```text
ExerciseTemplate ── used by ──> Routine ── may produce ──> Workout
        │                           │                          │
        └─ exercise history         └─ stored in a folder        └─ update/delete events
```

| Entity | Meaning | Key fields |
| --- | --- | --- |
| `ExerciseTemplate` | Exercise catalogue available to the account, built-in or custom. | `id`, `title`, `type`, muscles, equipment, `is_custom` |
| `Routine` | Reusable planned workout; it is not a completed session. | `id`, `title`, `folder_id`, `notes`, `exercises` |
| `Workout` | Completed training session at a specific time. | `id`, `routine_id`, `start_time`, `end_time`, `exercises` |
| `RoutineFolder` | Routine grouping and display order. | `id`, `index`, `title` |
| `BodyMeasurement` | Body-composition and circumference snapshot for a date. | `date`, `weight_kg`, `fat_percent`, measurements |

Routine sets describe the **prescription** and may contain `rep_range`.
Workout sets describe the **recorded result** and may contain `rpe`. Do not
interchange the two meanings in performance analysis.

## Exercise and set fields

Routines and workouts contain ordered exercises and ordered sets. The API
returns `index` for their persisted order. Each exercise references the
catalogue through `exercise_template_id`.

| Field | Routine | Workout | Meaning |
| --- | --- | --- | --- |
| `exercise_template_id` | yes | yes | Reference to the chosen exercise template. |
| `superset_id` | request | request | Shared value groups exercises into a superset; use `null` otherwise. |
| `notes` | yes | yes | Exercise-specific notes. |
| `rest_seconds` | yes | no | Planned rest interval between sets. The workout write contract does not expose it. |
| `type` | yes | yes | `warmup`, `normal`, `failure`, or `dropset`. |
| `weight_kg`, `reps` | yes | yes | Strength prescription or logged result. |
| `distance_meters`, `duration_seconds` | yes | yes | Distance/time prescription or logged result. |
| `custom_metric` | yes | yes | Currently used for stair-machine steps/floors. |
| `rep_range` | yes | no | Planned rep target: `{ "start": 8, "end": 12 }`. |
| `rpe` | no | yes | Logged perceived exertion: 6, 7, 7.5, 8, 8.5, 9, 9.5, or 10. |

The response field is named `supersets_id` (plural), while the create/update
request uses `superset_id` (singular). Keep this mapping explicit in the
adapter.

## Custom exercise types

Allowed `exercise_type` values: `weight_reps`, `reps_only`,
`bodyweight_reps`, `bodyweight_assisted_reps`, `duration`, `weight_duration`,
`distance_duration`, `short_distance_weight`.

Allowed `equipment_category` values: `none`, `barbell`, `dumbbell`,
`kettlebell`, `machine`, `plate`, `resistance_band`, `suspension`, `other`.

Allowed muscle groups: `abdominals`, `shoulders`, `biceps`, `triceps`,
`forearms`, `quadriceps`, `hamstrings`, `calves`, `glutes`, `abductors`,
`adductors`, `lats`, `upper_back`, `traps`, `lower_back`, `chest`, `cardio`,
`neck`, `full_body`, `other`.

## Monitoring and performance data

- Use `GET /v1/exercise_history/{exerciseTemplateId}` for progress of one
  exercise. It returns individual set entries with workout IDs and timestamps;
  this snapshot does not document pagination for it.
- `GET /v1/workouts` already includes exercises and sets for a complete session.
- Preserve `updated_at` and process workout update/delete events for a faithful
  local cache. A deletion event only contains `id` and `deleted_at`.
- Volume, personal records, intensity, and estimated 1RM are application
  calculations; the API exposes raw sets but not these aggregates.
