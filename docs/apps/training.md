# Training app

`training` owns normalized exercise, routine, workout, and set persistence.
Routine prescriptions and recorded workouts use separate ordered child tables.
Account-scoped external IDs, decimal units, aware timestamps, soft deletion,
and history-preserving foreign keys are enforced by models and migrations.

`TrainingRepository` reads local active workouts and set history, applies soft
deletion, and persists a complete validated import without an HTTP dependency.
Its full-import operation runs inside the coordinator transaction, upserts
parents by external identity, and replaces source-ordered child structures.

The authenticated `/historico/`, `/exercicios/`, and `/rotinas/` routes read
local rows without external calls. History keeps removed workouts visible for
audit, while analytics and routine lists use active rows. Sprint 7 adds
folder-grouped routine lists, ordered planned-set detail, and a persistent
distinction between planning and executed workouts. No routine page has create,
edit, or delete controls.

`/exportacoes/treinos.csv` uses the same period, routine, exercise, and set-type
filters as history. It emits one row per recorded set, keeps kg/metres/seconds
as canonical units, and leaves null fields empty.
