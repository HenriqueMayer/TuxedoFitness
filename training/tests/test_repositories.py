from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from training.models import ExerciseTemplate, Workout
from training.repositories import TrainingRepository
from training.tests.factories import create_account, create_template, create_workout


class TrainingRepositoryTests(TestCase):
    def setUp(self):
        self.account = create_account()
        self.template = create_template(self.account)
        self.repository = TrainingRepository()

    def test_queries_use_confirmed_local_active_data(self):
        included = create_workout(self.account, self.template)
        create_workout(
            self.account,
            self.template,
            is_active=False,
            removed_at=timezone.now(),
        )

        workouts = list(self.repository.query_workouts(self.account))
        history = list(
            self.repository.query_exercise_history(self.account, self.template)
        )

        self.assertEqual(workouts, [included])
        self.assertEqual(len(history), 1)

    def test_soft_delete_is_idempotent_and_auditable(self):
        workout = create_workout(self.account, self.template)
        removed_at = timezone.now()

        self.assertTrue(
            self.repository.mark_workout_removed(
                self.account,
                workout.external_id,
                removed_at,
            )
        )
        self.assertTrue(
            self.repository.mark_workout_removed(
                self.account,
                workout.external_id,
                removed_at,
            )
        )
        workout.refresh_from_db()

        self.assertFalse(workout.is_active)
        self.assertEqual(workout.removed_at, removed_at)
        self.assertFalse(Workout.objects.filter(pk=workout.pk).exists())

    def test_repository_rejects_naive_removal_time(self):
        workout = create_workout(self.account, self.template)
        naive_time = (timezone.now() - timedelta(days=1)).replace(tzinfo=None)

        with self.assertRaises(ValidationError):
            self.repository.mark_workout_removed(
                self.account,
                workout.external_id,
                naive_time,
            )

    def test_confirmed_refresh_can_mark_missing_templates_inactive(self):
        retained = self.template
        missing = create_template(self.account)
        removed_at = timezone.now()

        count = self.repository.mark_missing_inactive(
            ExerciseTemplate,
            self.account,
            {retained.external_id},
            removed_at,
        )
        missing.refresh_from_db()

        self.assertEqual(count, 1)
        self.assertFalse(missing.is_active)
        self.assertEqual(missing.removed_at, removed_at)
