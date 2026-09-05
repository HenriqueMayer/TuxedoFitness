"""Prepared, non-persistent history read models for dashboard presentation."""

from __future__ import annotations

from collections import Counter, defaultdict
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.utils import timezone
from django.utils.translation import gettext as _

from training.models import ExerciseTemplate, Workout

SET_LABELS = {
    "warmup": _("Warmup"),
    "normal": _("Normal"),
    "failure": _("Failure"),
    "dropset": _("Drop set"),
}


class HistoryPreparationService:
    """Transform normalized rows into chart-ready values without persisting copies."""

    def __init__(self, account, period, *, exercise=None):
        self.account = account
        self.period = period
        self.exercise = exercise
        self.zone = ZoneInfo(period.timezone_name)

    def build(self):
        queryset = Workout.objects.filter(
            hevy_account=self.account,
            start_time__gte=self.period.start_at,
            start_time__lt=self.period.end_at,
        ).prefetch_related("exercises__exercise_template", "exercises__sets")
        set_types = Counter()
        rpe = Counter()
        evolution = defaultdict(list)
        for workout in queryset:
            local_day = timezone.localtime(workout.start_time, self.zone).date()
            for exercise in workout.exercises.all():
                template = exercise.exercise_template
                for item in exercise.sets.all():
                    set_types[SET_LABELS.get(item.set_type, item.set_type)] += 1
                    if item.set_type != "warmup" and item.rpe is not None:
                        rpe[str(item.rpe.normalize())] += 1
                    if self.exercise is not None and template.pk == self.exercise.pk:
                        value = self._evolution_value(template, item)
                        if item.set_type != "warmup" and value is not None:
                            evolution[local_day].append(value)
        from accounts.presentation import convert_series, date_label

        preference = getattr(self.account.user, "fitness_preferences", None)
        values, unit = convert_series(
            {
                date_label(day, preference): max(values)
                for day, values in sorted(evolution.items())
            },
            self._unit(self.exercise),
            preference,
        )
        return {
            "set_type_counts": dict(set_types),
            "rpe_distribution": dict(
                sorted(rpe.items(), key=lambda pair: Decimal(pair[0]))
            ),
            "exercise_evolution": values,
            "exercise_evolution_title": self.exercise.title if self.exercise else "",
            "exercise_evolution_unit": unit,
        }

    @staticmethod
    def _evolution_value(template, item):
        kind = template.exercise_type
        if kind in {
            ExerciseTemplate.ExerciseType.WEIGHT_REPS,
            ExerciseTemplate.ExerciseType.WEIGHT_DURATION,
            ExerciseTemplate.ExerciseType.BODYWEIGHT_ASSISTED_REPS,
        }:
            return item.weight_kg
        if kind in {
            ExerciseTemplate.ExerciseType.REPS_ONLY,
            ExerciseTemplate.ExerciseType.BODYWEIGHT_REPS,
        }:
            return item.reps
        if kind in {
            ExerciseTemplate.ExerciseType.DISTANCE_DURATION,
            ExerciseTemplate.ExerciseType.SHORT_DISTANCE_WEIGHT,
        }:
            return item.distance_meters
        if kind == ExerciseTemplate.ExerciseType.DURATION:
            return item.duration_seconds
        return item.custom_metric

    @staticmethod
    def _unit(template):
        if template is None:
            return ""
        if template.exercise_type in {
            ExerciseTemplate.ExerciseType.WEIGHT_REPS,
            ExerciseTemplate.ExerciseType.WEIGHT_DURATION,
            ExerciseTemplate.ExerciseType.BODYWEIGHT_ASSISTED_REPS,
        }:
            return "kg"
        if template.exercise_type in {
            ExerciseTemplate.ExerciseType.REPS_ONLY,
            ExerciseTemplate.ExerciseType.BODYWEIGHT_REPS,
        }:
            return _("repetitions")
        if template.exercise_type in {
            ExerciseTemplate.ExerciseType.DISTANCE_DURATION,
            ExerciseTemplate.ExerciseType.SHORT_DISTANCE_WEIGHT,
        }:
            return "m"
        if template.exercise_type == ExerciseTemplate.ExerciseType.DURATION:
            return "s"
        return _("custom units")
