from datetime import datetime
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.utils import timezone

from training.models import (
    ExerciseSecondaryMuscle,
    ExerciseTemplate,
    RoutineExercise,
    RoutineSet,
    SetType,
    Workout,
    WorkoutExercise,
    WorkoutSet,
)
from training.tests.factories import (
    create_account,
    create_routine,
    create_template,
    create_workout,
    synchronized_fields,
)


class TrainingConstraintTests(TestCase):
    def test_external_id_is_unique_within_an_account(self):
        account = create_account()
        create_template(account, external_id='same-template')

        with self.assertRaises(IntegrityError), transaction.atomic():
            create_template(account, external_id='same-template')

    def test_same_external_id_is_allowed_for_another_account(self):
        first = create_account()
        second = create_account()

        create_template(first, external_id='shared-provider-id')
        create_template(second, external_id='shared-provider-id')

        self.assertEqual(
            ExerciseTemplate.all_objects.filter(
                external_id='shared-provider-id'
            ).count(),
            2,
        )

    def test_null_metrics_remain_null(self):
        account = create_account()
        workout = create_workout(account)
        recorded_set = workout.exercises.get().sets.get()
        recorded_set.weight_kg = None
        recorded_set.reps = None
        recorded_set.rpe = None
        recorded_set.save()

        recorded_set.refresh_from_db()

        self.assertIsNone(recorded_set.weight_kg)
        self.assertIsNone(recorded_set.reps)
        self.assertIsNone(recorded_set.rpe)

    def test_decimal_and_rep_range_validation(self):
        account = create_account()
        routine = create_routine(account)
        routine_set = RoutineSet(
            routine_exercise=routine.exercises.get(),
            position=1,
            set_type=SetType.NORMAL,
            weight_kg=Decimal('-0.001'),
            rep_range_start=12,
            rep_range_end=8,
        )

        with self.assertRaises(ValidationError):
            routine_set.full_clean()

    def test_workout_rejects_naive_timestamps(self):
        account = create_account()
        workout = Workout(
            hevy_account=account,
            external_id='naive-workout',
            title='Naive workout',
            start_time=datetime(2026, 1, 1, 12, 0),
            end_time=datetime(2026, 1, 1, 13, 0),
            **synchronized_fields(),
        )

        with self.assertRaises(ValidationError):
            workout.full_clean()

    def test_rpe_accepts_only_documented_values(self):
        workout = create_workout(create_account())
        workout_set = workout.exercises.get().sets.get()
        workout_set.rpe = Decimal('6.5')

        with self.assertRaises(ValidationError):
            workout_set.full_clean()

    def test_foreign_keys_must_stay_within_the_account(self):
        first = create_account()
        second = create_account()
        routine = create_routine(first)
        foreign_template = create_template(second)
        exercise = RoutineExercise(
            routine=routine,
            position=1,
            exercise_template=foreign_template,
            title_snapshot=foreign_template.title,
        )

        with self.assertRaises(ValidationError):
            exercise.full_clean()


class OrderingAndDeletionTests(TestCase):
    def test_routine_and_workout_children_follow_source_position(self):
        account = create_account()
        template = create_template(account)
        routine = create_routine(account, template)
        routine_exercise = routine.exercises.get()
        RoutineSet.objects.create(
            routine_exercise=routine_exercise,
            position=2,
            set_type=SetType.WARMUP,
        )
        RoutineSet.objects.create(
            routine_exercise=routine_exercise,
            position=1,
            set_type=SetType.WARMUP,
        )
        workout = create_workout(account, template, routine)
        workout_exercise = workout.exercises.get()
        WorkoutSet.objects.create(
            workout_exercise=workout_exercise,
            position=2,
            set_type=SetType.DROPSET,
        )
        WorkoutSet.objects.create(
            workout_exercise=workout_exercise,
            position=1,
            set_type=SetType.FAILURE,
        )

        self.assertEqual(
            list(routine_exercise.sets.values_list('position', flat=True)),
            [0, 1, 2],
        )
        self.assertEqual(
            list(workout_exercise.sets.values_list('position', flat=True)),
            [0, 1, 2],
        )

    def test_relationship_deletion_policies_preserve_history(self):
        account = create_account()
        template = create_template(account)
        routine = create_routine(account, template)
        workout = create_workout(account, template, routine)

        with self.assertRaises(ProtectedError):
            template.delete()

        folder = routine.folder
        folder.delete()
        routine.refresh_from_db()
        self.assertIsNone(routine.folder)

        routine.delete()
        workout.refresh_from_db()
        self.assertIsNone(workout.routine)

        workout.delete()
        self.assertFalse(WorkoutExercise.objects.exists())
        self.assertFalse(WorkoutSet.objects.exists())

    def test_secondary_muscle_is_unique_per_template(self):
        template = create_template(create_account())
        ExerciseSecondaryMuscle.objects.create(
            exercise_template=template,
            muscle_code='triceps',
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            ExerciseSecondaryMuscle.objects.create(
                exercise_template=template,
                muscle_code='triceps',
            )

    def test_active_manager_excludes_soft_deleted_rows(self):
        account = create_account()
        removed = create_workout(
            account,
            is_active=False,
            removed_at=timezone.now(),
        )

        self.assertFalse(Workout.objects.filter(pk=removed.pk).exists())
        self.assertTrue(Workout.all_objects.filter(pk=removed.pk).exists())
