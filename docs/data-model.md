# Data model · 0.2.0

A fresh database is required; historical migrations are retained as schema construction history, not a supported 0.1.x data-upgrade path.

- **HevyAccount**: one local user/one external account; unique external identity, ciphertext, validation timestamps. A replacement credential must resolve to the same external account.
- **IntegrationState / SyncCursor / SyncLock / SyncRun**: freshness, automatic retry reservation, incremental high-water mark, mutual exclusion and sanitized execution evidence.
- **ProviderSnapshot**: latest complete pages per account/resource, source hash and synchronization timestamp. Routine pages retain page/page_count/routines and all original fields.
- **ExerciseTemplate / ExerciseSecondaryMuscle**: provider ID, original title, modality, equipment, muscles and display-only reviewed PT-BR title/version. Custom and untranslated exercises retain the original name.
- **RoutineFolder / Routine / RoutineExercise / RoutineSet**: current planning data, ordered exercises/sets, notes, rest, supersets and compatible prescriptions.
- **Workout / WorkoutExercise / WorkoutSet**: completed sessions, original payloads, ordered observations, nullable measurements/RPE. Provider removals are tombstoned and excluded from active queries.
- **OwnerPreference**: units, IANA timezone, DMY/MDY, weekly target and private diagnostic retention.
- **DashboardPreference**: ordered visible topic IDs, saved filters and owner-scoped favorite exercises.
- **TrainingProfile**: optional objective, experience, equipment, available days, duration and limitations.
- **PromptGeneration**: UUID, user, final text, template version, frozen input options and manifest. The application never edits a generation; duplication uses current data.
- **RoutineProposal**: UUID, account, normalized envelope, remote source hashes, before/after comparison, 15-minute expiry, consumption state and per-operation results.

Every synchronized entity retains raw_payload and source metadata. Provider IDs are scoped to their account. Decimal measurements preserve nulls and prohibit negative values where defined. Exercise modalities determine metric eligibility; assistance and bodyweight never enter an external-load volume sum.

Deleting the local connection through Settings requires a verified backup first. Disconnecting from the Hevy connection page deletes only the stored credential; it preserves history. Saved prompt generations are separately user-owned and can be deleted individually.
