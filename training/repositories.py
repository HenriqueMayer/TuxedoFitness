from datetime import datetime

from django.db import transaction
from django.db.models import QuerySet

from core.validators import validate_aware_datetime
from integrations.models import HevyAccount
from training.models import (
    ExerciseSecondaryMuscle,
    ExerciseTemplate,
    Routine,
    RoutineExercise,
    RoutineFolder,
    RoutineSet,
    Workout,
    WorkoutExercise,
    WorkoutSet,
)
from training.translations import CATALOG_VERSION, translated_title


class TrainingRepository:
    @transaction.atomic
    def persist_full_import(
        self,
        hevy_account: HevyAccount,
        *,
        templates,
        folders,
        routines,
        workouts,
        synced_at: datetime,
        provider_schema_version: str,
    ) -> dict[str, int]:
        validate_aware_datetime(synced_at)
        result = {
            'exercise_templates': len(templates),
            'routine_folders': len(folders),
            'routines': len(routines),
            'workouts': len(workouts),
            'created': 0,
            'updated': 0,
            'ignored': 0,
            'invalid': 0,
        }
        template_map = {}
        for dto in templates:
            template, created = ExerciseTemplate.all_objects.update_or_create(
                hevy_account=hevy_account,
                external_id=dto.external_id,
                defaults={
                    'title': dto.title,
                    'exercise_type': dto.exercise_type,
                    'title_pt_br': translated_title(dto.title, dto.is_custom, dto.external_id),
                    'translation_version': CATALOG_VERSION,
                    'equipment_category': dto.equipment_category,
                    'primary_muscle': dto.primary_muscle,
                    'is_custom': dto.is_custom,
                    'external_created_at': dto.created_at,
                    'external_updated_at': dto.updated_at,
                    'synced_at': synced_at,
                    'is_active': True,
                    'removed_at': None,
                    'provider_schema_version': provider_schema_version,
                    'source_payload_hash': dto.source_hash,
                    'raw_payload': dto.raw_payload,
                },
            )
            result['created' if created else 'updated'] += 1
            ExerciseSecondaryMuscle.objects.filter(exercise_template=template).delete()
            ExerciseSecondaryMuscle.objects.bulk_create([
                ExerciseSecondaryMuscle(exercise_template=template, muscle_code=muscle)
                for muscle in dto.secondary_muscles
            ])
            template_map[dto.external_id] = template
        folder_map = {}
        for dto in folders:
            folder, created = RoutineFolder.all_objects.update_or_create(
                hevy_account=hevy_account,
                external_id=dto.external_id,
                defaults={
                    'position': dto.position,
                    'title': dto.title,
                    'external_created_at': dto.created_at,
                    'external_updated_at': dto.updated_at,
                    'synced_at': synced_at,
                    'is_active': True,
                    'removed_at': None,
                    'provider_schema_version': provider_schema_version,
                    'source_payload_hash': dto.source_hash,
                    'raw_payload': dto.raw_payload,
                },
            )
            result['created' if created else 'updated'] += 1
            folder_map[dto.external_id] = folder
        routine_map = {}
        for dto in routines:
            routine, created = Routine.all_objects.update_or_create(
                hevy_account=hevy_account,
                external_id=dto.external_id,
                defaults={
                    'folder': folder_map.get(dto.folder_id),
                    'notes': dto.raw_payload.get('notes') or '',
                    'title': dto.title,
                    'external_created_at': dto.created_at,
                    'external_updated_at': dto.updated_at,
                    'synced_at': synced_at,
                    'is_active': True,
                    'removed_at': None,
                    'provider_schema_version': provider_schema_version,
                    'source_payload_hash': dto.source_hash,
                    'raw_payload': dto.raw_payload,
                },
            )
            result['created' if created else 'updated'] += 1
            routine.exercises.all().delete()
            for exercise_dto in dto.exercises:
                exercise = RoutineExercise.objects.create(
                    routine=routine,
                    position=exercise_dto.position,
                    exercise_template=template_map[exercise_dto.template_id],
                    title_snapshot=exercise_dto.title,
                    notes=exercise_dto.notes,
                    rest_seconds=exercise_dto.rest_seconds,
                    superset_group=exercise_dto.superset_group,
                )
                RoutineSet.objects.bulk_create([
                    RoutineSet(
                        routine_exercise=exercise,
                        position=set_dto.position,
                        set_type=set_dto.set_type,
                        weight_kg=set_dto.weight_kg,
                        reps=set_dto.reps,
                        distance_meters=set_dto.distance_meters,
                        duration_seconds=set_dto.duration_seconds,
                        custom_metric=set_dto.custom_metric,
                        rep_range_start=set_dto.rep_range_start,
                        rep_range_end=set_dto.rep_range_end,
                    ) for set_dto in exercise_dto.sets
                ])
            routine_map[dto.external_id] = routine
        for dto in workouts:
            workout, created = Workout.all_objects.update_or_create(
                hevy_account=hevy_account,
                external_id=dto.external_id,
                defaults={
                    'routine': routine_map.get(dto.routine_id),
                    'title': dto.title,
                    'description': dto.description,
                    'start_time': dto.start_time,
                    'end_time': dto.end_time,
                    'external_created_at': dto.created_at,
                    'external_updated_at': dto.updated_at,
                    'synced_at': synced_at,
                    'is_active': True,
                    'removed_at': None,
                    'provider_schema_version': provider_schema_version,
                    'source_payload_hash': dto.source_hash,
                    'raw_payload': dto.raw_payload,
                },
            )
            result['created' if created else 'updated'] += 1
            workout.exercises.all().delete()
            for exercise_dto in dto.exercises:
                exercise = WorkoutExercise.objects.create(
                    workout=workout,
                    position=exercise_dto.position,
                    exercise_template=template_map[exercise_dto.template_id],
                    title_snapshot=exercise_dto.title,
                    notes=exercise_dto.notes,
                    superset_group=exercise_dto.superset_group,
                )
                WorkoutSet.objects.bulk_create([
                    WorkoutSet(
                        workout_exercise=exercise,
                        position=set_dto.position,
                        set_type=set_dto.set_type,
                        weight_kg=set_dto.weight_kg,
                        reps=set_dto.reps,
                        distance_meters=set_dto.distance_meters,
                        duration_seconds=set_dto.duration_seconds,
                        custom_metric=set_dto.custom_metric,
                        rpe=set_dto.rpe,
                    ) for set_dto in exercise_dto.sets
                ])
        return result

    @transaction.atomic
    def persist_incremental_workouts(
        self,
        hevy_account: HevyAccount,
        workouts,
        *,
        synced_at: datetime,
        provider_schema_version: str,
    ) -> dict[str, int]:
        validate_aware_datetime(synced_at)
        templates = {
            item.external_id: item
            for item in ExerciseTemplate.all_objects.filter(hevy_account=hevy_account)
        }
        routines = {
            item.external_id: item
            for item in Routine.all_objects.filter(hevy_account=hevy_account)
        }
        result = {'created': 0, 'updated': 0}
        for dto in workouts:
            if dto.routine_id is not None and dto.routine_id not in routines:
                raise ValueError('Workout refers to an unavailable routine.')
            if any(exercise.template_id not in templates for exercise in dto.exercises):
                raise ValueError('Workout refers to an unavailable exercise template.')
            workout, created = Workout.all_objects.update_or_create(
                hevy_account=hevy_account,
                external_id=dto.external_id,
                defaults={
                    'routine': routines.get(dto.routine_id),
                    'title': dto.title,
                    'description': dto.description,
                    'start_time': dto.start_time,
                    'end_time': dto.end_time,
                    'external_created_at': dto.created_at,
                    'external_updated_at': dto.updated_at,
                    'synced_at': synced_at,
                    'is_active': True,
                    'removed_at': None,
                    'provider_schema_version': provider_schema_version,
                    'source_payload_hash': dto.source_hash,
                    'raw_payload': dto.raw_payload,
                },
            )
            result['created' if created else 'updated'] += 1
            workout.exercises.all().delete()
            for exercise_dto in dto.exercises:
                exercise = WorkoutExercise.objects.create(
                    workout=workout,
                    position=exercise_dto.position,
                    exercise_template=templates[exercise_dto.template_id],
                    title_snapshot=exercise_dto.title,
                    notes=exercise_dto.notes,
                    superset_group=exercise_dto.superset_group,
                )
                WorkoutSet.objects.bulk_create([
                    WorkoutSet(
                        workout_exercise=exercise,
                        position=set_dto.position,
                        set_type=set_dto.set_type,
                        weight_kg=set_dto.weight_kg,
                        reps=set_dto.reps,
                        distance_meters=set_dto.distance_meters,
                        duration_seconds=set_dto.duration_seconds,
                        custom_metric=set_dto.custom_metric,
                        rpe=set_dto.rpe,
                    ) for set_dto in exercise_dto.sets
                ])
        return result

    def query_workouts(
        self,
        hevy_account: HevyAccount,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
        include_removed: bool = False,
    ) -> QuerySet[Workout]:
        manager = Workout.all_objects if include_removed else Workout.objects
        workouts = manager.filter(hevy_account=hevy_account)
        if start is not None:
            workouts = workouts.filter(start_time__gte=start)
        if end is not None:
            workouts = workouts.filter(start_time__lt=end)
        return workouts.select_related('routine').prefetch_related(
            'exercises__exercise_template',
            'exercises__sets',
        )

    def query_exercise_history(
        self,
        hevy_account: HevyAccount,
        exercise_template: ExerciseTemplate,
    ) -> QuerySet[WorkoutSet]:
        return WorkoutSet.objects.filter(
            workout_exercise__workout__in=Workout.objects.filter(
                hevy_account=hevy_account
            ),
            workout_exercise__exercise_template=exercise_template,
        ).select_related('workout_exercise__workout')

    @transaction.atomic
    def mark_workout_removed(
        self,
        hevy_account: HevyAccount,
        external_id: str,
        removed_at: datetime,
    ) -> bool:
        validate_aware_datetime(removed_at)
        updated = Workout.all_objects.filter(
            hevy_account=hevy_account,
            external_id=external_id,
        ).update(is_active=False, removed_at=removed_at)
        return updated == 1

    @transaction.atomic
    def mark_missing_inactive(
        self,
        model: (
            type[ExerciseTemplate]
            | type[RoutineFolder]
            | type[Routine]
            | type[Workout]
        ),
        hevy_account: HevyAccount,
        confirmed_external_ids: set[str | int],
        removed_at: datetime,
    ) -> int:
        validate_aware_datetime(removed_at)
        if model not in {ExerciseTemplate, RoutineFolder, Routine, Workout}:
            raise ValueError('Unsupported synchronized model.')
        return model.all_objects.filter(
            hevy_account=hevy_account,
            is_active=True,
        ).exclude(external_id__in=confirmed_external_ids).update(
            is_active=False,
            removed_at=removed_at,
        )
