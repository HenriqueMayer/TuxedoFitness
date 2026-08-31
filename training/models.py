from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.db.models import F, Q

from core.validators import validate_aware_datetime

NON_NEGATIVE = MinValueValidator(Decimal('0'))
SHA256_VALIDATOR = RegexValidator(
    regex=r'\A[0-9a-f]{64}\Z',
    message='Payload hash must be a 64-character SHA-256 hex value.',
)
RPE_CHOICES = [
    (Decimal('6.0'), '6'),
    (Decimal('7.0'), '7'),
    (Decimal('7.5'), '7.5'),
    (Decimal('8.0'), '8'),
    (Decimal('8.5'), '8.5'),
    (Decimal('9.0'), '9'),
    (Decimal('9.5'), '9.5'),
    (Decimal('10.0'), '10'),
]


class ActiveSynchronizedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True, removed_at__isnull=True)


class SynchronizedModel(models.Model):
    external_created_at = models.DateTimeField(
        validators=[validate_aware_datetime],
        null=True,
        blank=True,
    )
    external_updated_at = models.DateTimeField(
        validators=[validate_aware_datetime],
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    synced_at = models.DateTimeField(validators=[validate_aware_datetime])
    is_active = models.BooleanField(default=True)
    removed_at = models.DateTimeField(
        validators=[validate_aware_datetime],
        null=True,
        blank=True,
    )
    provider_schema_version = models.CharField(max_length=32)
    source_payload_hash = models.CharField(
        max_length=64,
        validators=[SHA256_VALIDATOR],
    )

    objects = ActiveSynchronizedManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True
        base_manager_name = 'all_objects'
        default_manager_name = 'objects'


class ExerciseTemplate(SynchronizedModel):
    class ExerciseType(models.TextChoices):
        WEIGHT_REPS = 'weight_reps', 'Weight and reps'
        REPS_ONLY = 'reps_only', 'Reps only'
        BODYWEIGHT_REPS = 'bodyweight_reps', 'Bodyweight reps'
        BODYWEIGHT_ASSISTED_REPS = 'bodyweight_assisted_reps', 'Assisted reps'
        DURATION = 'duration', 'Duration'
        WEIGHT_DURATION = 'weight_duration', 'Weight and duration'
        DISTANCE_DURATION = 'distance_duration', 'Distance and duration'
        SHORT_DISTANCE_WEIGHT = 'short_distance_weight', 'Distance and weight'
        CUSTOM = 'custom', 'Custom'

    class EquipmentCategory(models.TextChoices):
        NONE = 'none', 'None'
        BARBELL = 'barbell', 'Barbell'
        DUMBBELL = 'dumbbell', 'Dumbbell'
        KETTLEBELL = 'kettlebell', 'Kettlebell'
        MACHINE = 'machine', 'Machine'
        PLATE = 'plate', 'Plate'
        RESISTANCE_BAND = 'resistance_band', 'Resistance band'
        SUSPENSION = 'suspension', 'Suspension'
        OTHER = 'other', 'Other'

    class MuscleGroup(models.TextChoices):
        ABDOMINALS = 'abdominals', 'Abdominals'
        SHOULDERS = 'shoulders', 'Shoulders'
        BICEPS = 'biceps', 'Biceps'
        TRICEPS = 'triceps', 'Triceps'
        FOREARMS = 'forearms', 'Forearms'
        QUADRICEPS = 'quadriceps', 'Quadriceps'
        HAMSTRINGS = 'hamstrings', 'Hamstrings'
        CALVES = 'calves', 'Calves'
        GLUTES = 'glutes', 'Glutes'
        ABDUCTORS = 'abductors', 'Abductors'
        ADDUCTORS = 'adductors', 'Adductors'
        LATS = 'lats', 'Lats'
        UPPER_BACK = 'upper_back', 'Upper back'
        TRAPS = 'traps', 'Traps'
        LOWER_BACK = 'lower_back', 'Lower back'
        CHEST = 'chest', 'Chest'
        CARDIO = 'cardio', 'Cardio'
        NECK = 'neck', 'Neck'
        FULL_BODY = 'full_body', 'Full body'
        OTHER = 'other', 'Other'

    hevy_account = models.ForeignKey(
        'integrations.HevyAccount',
        on_delete=models.CASCADE,
        related_name='exercise_templates',
    )
    external_id = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    exercise_type = models.CharField(max_length=32, choices=ExerciseType)
    equipment_category = models.CharField(
        max_length=32,
        choices=EquipmentCategory,
        blank=True,
    )
    primary_muscle = models.CharField(
        max_length=32,
        choices=MuscleGroup,
        blank=True,
    )
    is_custom = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['hevy_account', 'external_id'],
                name='unique_exercise_template_external_id',
            ),
        ]
        indexes = [
            models.Index(
                fields=['hevy_account', 'is_active'],
                name='exercise_template_active_idx',
            ),
        ]
        ordering = ['title', 'external_id']

    def __str__(self):
        return self.title


class ExerciseSecondaryMuscle(models.Model):
    exercise_template = models.ForeignKey(
        ExerciseTemplate,
        on_delete=models.CASCADE,
        related_name='secondary_muscles',
    )
    muscle_code = models.CharField(
        max_length=32,
        choices=ExerciseTemplate.MuscleGroup,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['exercise_template', 'muscle_code'],
                name='unique_template_secondary_muscle',
            ),
        ]
        ordering = ['muscle_code']


class RoutineFolder(SynchronizedModel):
    hevy_account = models.ForeignKey(
        'integrations.HevyAccount',
        on_delete=models.CASCADE,
        related_name='routine_folders',
    )
    external_id = models.PositiveBigIntegerField()
    position = models.PositiveIntegerField()
    title = models.CharField(max_length=255)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['hevy_account', 'external_id'],
                name='unique_routine_folder_external_id',
            ),
        ]
        indexes = [
            models.Index(
                fields=['hevy_account', 'is_active'],
                name='routine_folder_active_idx',
            ),
        ]
        ordering = ['position', 'external_id']

    def __str__(self):
        return self.title


class Routine(SynchronizedModel):
    hevy_account = models.ForeignKey(
        'integrations.HevyAccount',
        on_delete=models.CASCADE,
        related_name='routines',
    )
    external_id = models.CharField(max_length=255)
    folder = models.ForeignKey(
        RoutineFolder,
        on_delete=models.SET_NULL,
        related_name='routines',
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=255)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['hevy_account', 'external_id'],
                name='unique_routine_external_id',
            ),
        ]
        indexes = [
            models.Index(
                fields=['hevy_account', 'is_active'],
                name='routine_active_idx',
            ),
        ]
        ordering = ['title', 'external_id']

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        if self.folder_id and self.folder.hevy_account_id != self.hevy_account_id:
            raise ValidationError(
                {'folder': 'Folder and routine accounts must match.'}
            )


class RoutineExercise(models.Model):
    routine = models.ForeignKey(
        Routine,
        on_delete=models.CASCADE,
        related_name='exercises',
    )
    position = models.PositiveIntegerField()
    exercise_template = models.ForeignKey(
        ExerciseTemplate,
        on_delete=models.PROTECT,
        related_name='routine_exercises',
    )
    title_snapshot = models.CharField(max_length=255)
    notes = models.TextField(blank=True)
    rest_seconds = models.PositiveIntegerField(null=True, blank=True)
    superset_group = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['routine', 'position'],
                name='unique_routine_exercise_position',
            ),
        ]
        ordering = ['position']

    def clean(self):
        super().clean()
        if (
            self.routine_id
            and self.exercise_template_id
            and self.routine.hevy_account_id
            != self.exercise_template.hevy_account_id
        ):
            raise ValidationError(
                {'exercise_template': 'Template and routine accounts must match.'}
            )


class SetType(models.TextChoices):
    WARMUP = 'warmup', 'Warmup'
    NORMAL = 'normal', 'Normal'
    FAILURE = 'failure', 'Failure'
    DROPSET = 'dropset', 'Dropset'


class RoutineSet(models.Model):
    routine_exercise = models.ForeignKey(
        RoutineExercise,
        on_delete=models.CASCADE,
        related_name='sets',
    )
    position = models.PositiveIntegerField()
    set_type = models.CharField(max_length=16, choices=SetType)
    weight_kg = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        validators=[NON_NEGATIVE],
        null=True,
        blank=True,
    )
    reps = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        validators=[NON_NEGATIVE],
        null=True,
        blank=True,
    )
    rep_range_start = models.PositiveIntegerField(null=True, blank=True)
    rep_range_end = models.PositiveIntegerField(null=True, blank=True)
    distance_meters = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        validators=[NON_NEGATIVE],
        null=True,
        blank=True,
    )
    duration_seconds = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        validators=[NON_NEGATIVE],
        null=True,
        blank=True,
    )
    custom_metric = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        validators=[NON_NEGATIVE],
        null=True,
        blank=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['routine_exercise', 'position'],
                name='unique_routine_set_position',
            ),
            models.CheckConstraint(
                condition=(
                    Q(rep_range_start__isnull=True)
                    | Q(rep_range_end__isnull=True)
                    | Q(rep_range_start__lte=F('rep_range_end'))
                ),
                name='valid_routine_rep_range',
            ),
        ]
        ordering = ['position']


class Workout(SynchronizedModel):
    hevy_account = models.ForeignKey(
        'integrations.HevyAccount',
        on_delete=models.CASCADE,
        related_name='workouts',
    )
    external_id = models.CharField(max_length=255)
    routine = models.ForeignKey(
        Routine,
        on_delete=models.SET_NULL,
        related_name='workouts',
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    start_time = models.DateTimeField(validators=[validate_aware_datetime])
    end_time = models.DateTimeField(validators=[validate_aware_datetime])

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['hevy_account', 'external_id'],
                name='unique_workout_external_id',
            ),
            models.CheckConstraint(
                condition=Q(end_time__gte=F('start_time')),
                name='workout_end_not_before_start',
            ),
        ]
        indexes = [
            models.Index(
                fields=['hevy_account', 'start_time', 'is_active'],
                name='workout_account_start_idx',
            ),
            models.Index(
                fields=['routine', 'start_time'],
                name='workout_routine_start_idx',
            ),
        ]
        ordering = ['-start_time', '-external_id']

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        if self.routine_id and self.routine.hevy_account_id != self.hevy_account_id:
            raise ValidationError(
                {'routine': 'Routine and workout accounts must match.'}
            )


class WorkoutExercise(models.Model):
    workout = models.ForeignKey(
        Workout,
        on_delete=models.CASCADE,
        related_name='exercises',
    )
    position = models.PositiveIntegerField()
    exercise_template = models.ForeignKey(
        ExerciseTemplate,
        on_delete=models.PROTECT,
        related_name='workout_exercises',
    )
    title_snapshot = models.CharField(max_length=255)
    notes = models.TextField(blank=True)
    superset_group = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['workout', 'position'],
                name='unique_workout_exercise_position',
            ),
        ]
        indexes = [
            models.Index(
                fields=['exercise_template', 'workout'],
                name='workout_exercise_history_idx',
            ),
        ]
        ordering = ['position']

    def clean(self):
        super().clean()
        if (
            self.workout_id
            and self.exercise_template_id
            and self.workout.hevy_account_id
            != self.exercise_template.hevy_account_id
        ):
            raise ValidationError(
                {'exercise_template': 'Template and workout accounts must match.'}
            )


class WorkoutSet(models.Model):
    workout_exercise = models.ForeignKey(
        WorkoutExercise,
        on_delete=models.CASCADE,
        related_name='sets',
    )
    position = models.PositiveIntegerField()
    set_type = models.CharField(max_length=16, choices=SetType)
    weight_kg = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        validators=[NON_NEGATIVE],
        null=True,
        blank=True,
    )
    reps = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        validators=[NON_NEGATIVE],
        null=True,
        blank=True,
    )
    distance_meters = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        validators=[NON_NEGATIVE],
        null=True,
        blank=True,
    )
    duration_seconds = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        validators=[NON_NEGATIVE],
        null=True,
        blank=True,
    )
    rpe = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        choices=RPE_CHOICES,
        null=True,
        blank=True,
    )
    custom_metric = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        validators=[NON_NEGATIVE],
        null=True,
        blank=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['workout_exercise', 'position'],
                name='unique_workout_set_position',
            ),
            models.CheckConstraint(
                condition=Q(rpe__isnull=True)
                | Q(rpe__in=[value for value, _ in RPE_CHOICES]),
                name='valid_workout_set_rpe',
            ),
        ]
        indexes = [
            models.Index(fields=['set_type'], name='workout_set_type_idx'),
            models.Index(
                fields=['workout_exercise', 'set_type'],
                name='workout_set_exercise_type_idx',
            ),
        ]
        ordering = ['position']
