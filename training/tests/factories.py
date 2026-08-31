from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.utils import timezone

from integrations.models import HevyAccount, IntegrationState
from training.models import (
    ExerciseTemplate,
    Routine,
    RoutineExercise,
    RoutineFolder,
    RoutineSet,
    SetType,
    Workout,
    WorkoutExercise,
    WorkoutSet,
)


def synchronized_fields(suffix='a'):
    return {
        'synced_at': timezone.now(),
        'provider_schema_version': 'synthetic-v1',
        'source_payload_hash': suffix * 64,
    }


def create_account(username=None):
    username = username or f'owner-{uuid4().hex[:8]}'
    user = get_user_model().objects.create_user(username=username)
    account = HevyAccount.objects.create(
        user=user,
        external_user_id=f'user-{uuid4().hex}',
        display_name='Synthetic Owner',
        verified_at=timezone.now(),
    )
    IntegrationState.objects.create(
        hevy_account=account,
        status=IntegrationState.Status.CONNECTED,
        is_stale=False,
    )
    return account


def create_template(account, external_id=None, **overrides):
    values = {
        'hevy_account': account,
        'external_id': external_id or f'exercise-{uuid4().hex}',
        'title': 'Synthetic Press',
        'exercise_type': ExerciseTemplate.ExerciseType.WEIGHT_REPS,
        'equipment_category': 'barbell',
        'primary_muscle': 'chest',
        **synchronized_fields(),
    }
    values.update(overrides)
    return ExerciseTemplate.all_objects.create(**values)


def create_routine(account, template=None, **overrides):
    template = template or create_template(account)
    folder = RoutineFolder.all_objects.create(
        hevy_account=account,
        external_id=int(uuid4().hex[:8], 16),
        position=0,
        title='Synthetic Plan',
        **synchronized_fields('b'),
    )
    values = {
        'hevy_account': account,
        'external_id': f'routine-{uuid4().hex}',
        'folder': folder,
        'title': 'Synthetic Routine',
        **synchronized_fields('c'),
    }
    values.update(overrides)
    routine = Routine.all_objects.create(**values)
    exercise = RoutineExercise.objects.create(
        routine=routine,
        position=0,
        exercise_template=template,
        title_snapshot=template.title,
        rest_seconds=90,
    )
    RoutineSet.objects.create(
        routine_exercise=exercise,
        position=0,
        set_type=SetType.NORMAL,
        weight_kg=Decimal('40.000'),
        reps=Decimal('8.000'),
        rep_range_start=8,
        rep_range_end=10,
    )
    return routine


def create_workout(account, template=None, routine=None, **overrides):
    template = template or create_template(account)
    now = timezone.now()
    values = {
        'hevy_account': account,
        'external_id': f'workout-{uuid4().hex}',
        'routine': routine,
        'title': 'Synthetic Workout',
        'start_time': now - timedelta(hours=1),
        'end_time': now,
        **synchronized_fields('d'),
    }
    values.update(overrides)
    workout = Workout.all_objects.create(**values)
    exercise = WorkoutExercise.objects.create(
        workout=workout,
        position=0,
        exercise_template=template,
        title_snapshot=template.title,
    )
    WorkoutSet.objects.create(
        workout_exercise=exercise,
        position=0,
        set_type=SetType.NORMAL,
        weight_kg=Decimal('42.500'),
        reps=Decimal('8.000'),
        rpe=Decimal('8.5'),
    )
    return workout
