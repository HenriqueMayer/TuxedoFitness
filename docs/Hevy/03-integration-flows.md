# Integration flows

## 1. Connect an account

1. The user obtains the key in Hevy Web under `Settings > Developer`.
2. The backend validates it through `GET /v1/user/info`.
3. Keep the key in the backend environment. Do not store it in the application
   database. Retain returned `data.id` as the external account identifier.
4. Only show `name` and `url` after validation. Never return the key to a web
   client.

## 2. Full initial import

Fetch data in this order:

1. User: `GET /v1/user/info`.
2. Catalogue: fetch **every** page of `GET /v1/exercise_templates`
   (`pageSize=100`) and index by `id`.
3. Organisation: fetch every page of `GET /v1/routine_folders`.
4. Planned training: fetch every page of `GET /v1/routines` and join each
   `folder_id` to its folder.
5. Session history: fetch every page of `GET /v1/workouts` and store its full
   nested exercises and sets.
6. Measurements: fetch every page of `GET /v1/body_measurements` when body
   progress is enabled.

The `Routine` and `Workout` list schemas already contain complete exercises and
sets, so an ID request is not required after every list item. Use the single-ID
endpoints to refresh one item or repair an incomplete cache.

## 3. Incremental workout synchronisation

`GET /v1/workouts/events?since=<ISO-8601>` returns update/delete events from
newest to oldest.

```text
saved cursor ──> fetch every event page since the cursor
                        │
             ┌──────────┴──────────┐
             ▼                     ▼
      type = updated          type = deleted
      upsert full workout     soft-delete/remove by id
             └──────────┬──────────┘
                        ▼
       advance cursor only after a successful transaction
```

Apply each batch deterministically. Re-query a small overlapping time window
and upsert idempotently by `workout.id` to avoid missing an update at the time
boundary. The API documents no opaque cursor, so persist the last confirmed
instant and deduplicate locally.

This event feed covers workouts only. No equivalent feed is documented for
routines, templates, folders, or measurements; refresh those collections on a
schedule or through a user-triggered refresh.

## 4. Create a complete planned workout (routine)

1. Fetch exercise templates and select each `exercise_template_id`.
2. Optionally create a folder and assign its numeric ID to `folder_id`; use
   `null` for the default **My Routines** folder.
3. Set routine `title`, optional `notes`, and ordered exercises.
4. For every set, choose `type`: `warmup`, `normal`, `failure`, or `dropset`.
   Add the applicable prescription: weight, reps or rep range, distance,
   duration, and custom metric.
5. Set per-exercise `rest_seconds`, notes, and `superset_id` when needed.
6. Send `POST /v1/routines`; retain the returned ID. Use `PUT` with that ID to
   edit the routine later.

```json
{
  "routine": {
    "title": "Upper A",
    "folder_id": null,
    "notes": "Weekly load progression.",
    "exercises": [
      {
        "exercise_template_id": "D04AC939",
        "superset_id": null,
        "rest_seconds": 120,
        "notes": "Control the eccentric.",
        "sets": [
          {"type": "warmup", "weight_kg": 40, "reps": 12, "distance_meters": null, "duration_seconds": null, "custom_metric": null, "rep_range": null},
          {"type": "normal", "weight_kg": 70, "reps": 10, "distance_meters": null, "duration_seconds": null, "custom_metric": null, "rep_range": {"start": 8, "end": 12}},
          {"type": "dropset", "weight_kg": 50, "reps": 12, "distance_meters": null, "duration_seconds": null, "custom_metric": null, "rep_range": null}
        ]
      }
    ]
  }
}
```

## 5. Record a complete completed session (workout)

Use `POST /v1/workouts` only for an executed session. The request includes
`title`, optional `description`, `start_time`, `end_time`, `is_private`, and
the ordered exercises/sets. Correct an existing session with
`PUT /v1/workouts/{workoutId}` using the same body shape.

For each completed set, send its `type` (including warmup/failure/dropset),
the applicable numeric metrics, and `rpe` where known. The documented workout
write contract has no `rest_seconds` or `rep_range`; those belong to routine
prescription, not the completed-session payload.

```json
{
  "workout": {
    "title": "Upper A",
    "description": "Strong execution.",
    "start_time": "2026-08-26T12:00:00Z",
    "end_time": "2026-08-26T13:00:00Z",
    "is_private": false,
    "exercises": [
      {
        "exercise_template_id": "D04AC939",
        "superset_id": null,
        "notes": "All reps controlled.",
        "sets": [
          {"type": "warmup", "weight_kg": 40, "reps": 12, "distance_meters": null, "duration_seconds": null, "custom_metric": null, "rpe": null},
          {"type": "normal", "weight_kg": 70, "reps": 10, "distance_meters": null, "duration_seconds": null, "custom_metric": null, "rpe": 8},
          {"type": "failure", "weight_kg": 70, "reps": 9, "distance_meters": null, "duration_seconds": null, "custom_metric": null, "rpe": 10}
        ]
      }
    ]
  }
}
```

Do not invent `index` in a create/update payload. The API returns it as the
persisted order.

## 6. Display exercise analysis

1. Choose the template from the catalogue (`exercise_template_id`).
2. Request a period using ISO 8601 `start_date` and `end_date`.
3. Aggregate returned rows by `workout_id` and timestamp. Separate warmups
   from working sets when the metric requires it.
4. Preserve nulls: never sum absent weight or reps for duration/distance-based
   exercises.

For body progress, use the paginated measurement collection and treat `date`
as a date-only data point rather than a workout timestamp.
