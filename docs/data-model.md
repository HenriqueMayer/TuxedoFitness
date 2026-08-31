# Data model

Sprint 2 defines the normalized SQLite schema. Migrations are the schema source
of truth; no database file or Hevy payload is tracked.

## Ownership and integration state

| Model | Main fields | Rules |
| --- | --- | --- |
| `OwnerPreference` | timezone, weekly target, display units, snapshot retention | One-to-one with the native Django user. |
| `HevyAccount` | external user ID, display name, profile URL, verification time | One-to-one with the owner; the API key is never stored. |
| `IntegrationState` | connection status, validation and refresh times, stale flag | One-to-one with the Hevy account. |
| `SyncRun` | UUID, mode, trigger, state, timing, counts, cursors, sanitized error, versions, prior run | Records synchronization observability without payloads or credentials. |
| `SyncCursor` | stream name, confirmed time, overlap seconds | Unique per account and stream. |

`SyncRun` permits `pending`, `running`, `succeeded`, `partial`, and `failed`.
Its finish time cannot precede its start time. All source and cursor timestamps
must be timezone-aware.

## Training entities

```text
HevyAccount
├── ExerciseTemplate ──< ExerciseSecondaryMuscle
├── RoutineFolder ──< Routine ──< RoutineExercise ──< RoutineSet
└── Workout ──< WorkoutExercise ──< WorkoutSet
                 │
Routine ─────────┘ (optional source plan)
```

| Model | Hevy-sourced fields |
| --- | --- |
| `ExerciseTemplate` | string ID, title, exercise type, equipment, primary muscle, custom flag |
| `ExerciseSecondaryMuscle` | muscle code from the secondary-muscle array |
| `RoutineFolder` | numeric ID, source position, title |
| `Routine` | string ID, optional folder, title |
| `RoutineExercise` | source position, template, title snapshot, notes, rest seconds, optional superset group |
| `RoutineSet` | source position, set type, weight, reps, rep range, distance, duration, custom metric |
| `Workout` | string ID, optional source routine, title, description, start and end |
| `WorkoutExercise` | source position, template, title snapshot, notes, optional superset group |
| `WorkoutSet` | source position, set type, weight, reps, distance, duration, RPE, custom metric |

Routine sets are prescriptions and workout sets are recorded results. The two
structures intentionally use separate tables.

## Synchronized metadata

`ExerciseTemplate`, `RoutineFolder`, `Routine`, and `Workout` contain:

- account-scoped external identity;
- nullable external creation and update times;
- local creation, update, and synchronization times;
- `is_active` and nullable `removed_at` soft-deletion state;
- provider schema version and SHA-256 payload hash.

Their default `objects` manager returns active, non-removed rows.
`all_objects` exists for synchronization and audit operations.

## Precision and nulls

| Value | Storage |
| --- | --- |
| Weight | Decimal kilograms, 3 decimal places |
| Repetitions | Non-negative decimal, 3 decimal places |
| Distance | Decimal meters, 3 decimal places |
| Duration | Decimal seconds, 3 decimal places |
| Custom metric | Non-negative decimal, 3 decimal places |
| RPE | Decimal, 1 decimal place; documented values 6, 7, 7.5, 8, 8.5, 9, 9.5, or 10 |
| Position and rest | Non-negative integer |
| Time | Aware datetime, stored canonically by Django in UTC |

Metric fields are nullable because missing is not zero. Routine rep-range start
cannot exceed its end, and workout end cannot precede workout start.

## Identity, ordering, and indexes

- External IDs are unique per account and entity.
- Secondary muscles are unique per template and muscle code.
- Child positions are unique within their parent and define default order.
- Workout indexes cover account/start/active, routine/start, template history,
  set type, and the correlated exercise/set-type history filter.
- Active-state indexes cover templates, folders, and routines.
- Sync runs are indexed by account, state, and start time.

## Deletion behavior

- Template references from routine or workout history are protective.
- Deleting a folder sets `Routine.folder` to null.
- Deleting a routine sets `Workout.routine` to null.
- Nested exercises and sets cascade with their local parent.
- Provider removals are soft deletions; audit access remains possible.
- Confirmed local-owner deletion first requires a verified off-checkout SQLite
  backup; protective history references prevent an unsafe shortcut.

## Repository boundary

`TrainingRepository` reads active normalized workouts and exercise history,
supports audit-inclusive workout queries, and applies aware, idempotent soft
deletions. It performs no HTTP request. Sprint 3 adds the full-import persistence
operation: validated DTOs upsert account-scoped parents, replace ordered child
rows transactionally, reactivate returned rows, and leave absence handling to a
confirmed refresh coordinator.

Sprint 4 adds `SyncRun.high_water_at` and `SyncLock`. The high-water timestamp
records the incremental retrieval boundary; `cursor_after` remains null unless
the canonical workout transaction succeeds. `SyncLock` is a local per-account
advisory writer lock and holds no secret or provider payload.

`OwnerPreference.snapshot_retention_days` defaults to 7 and accepts 0 through
30. Mass and distance choices are presentation-only: canonical database values
remain kilograms and metres.

## Migrations

- `accounts/0001_initial.py`: owner preferences.
- `accounts/0002_alter_ownerpreference_snapshot_retention_days.py`: seven-day
  default and the 0–30 day bounds.
- `integrations/0001_initial.py`: account, state, run, and cursor tables.
- `integrations/0002_synclock_syncrun_high_water_at.py`: advisory lock and
  incremental high-water mark.
- `training/0001_initial.py`: normalized training tables, constraints, and
  indexes.
- `training/0002_alter_exercisetemplate_exercise_type.py`: complete documented
  exercise-type choices.
- `training/0003_workoutset_workout_set_exercise_type_idx.py`: composite
  exercise/set-type lookup for bounded history filtering.
