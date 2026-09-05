"""Configurable local analytics; presentation receives calculated series only."""

from collections import Counter, defaultdict
from datetime import date, timedelta
from decimal import Decimal

from django import forms
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from accounts.presentation import date_label
from analytics.services import E1RM_TYPES, AnalyticsService
from dashboard.presenters import DashboardPresenter
from planning.forms import StyledForm
from training.models import ExerciseTemplate, Routine, SetType

PANELS = [
    ("frequency", gettext_lazy("Frequency and consistency")),
    ("progression", gettext_lazy("Load and progression")),
    ("effort", gettext_lazy("Recorded effort")),
    ("volume", gettext_lazy("Training volume")),
    ("distribution", gettext_lazy("Training distribution")),
    ("duration", gettext_lazy("Duration and modalities")),
]


class ReportForm(StyledForm, forms.Form):
    grouping = forms.ChoiceField(
        required=False,
        label=gettext_lazy("Group frequency by"),
        choices=[("week", gettext_lazy("Week")), ("month", gettext_lazy("Month"))],
    )
    start = forms.DateField(
        required=False,
        label=gettext_lazy("Start date"),
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    end = forms.DateField(
        required=False,
        label=gettext_lazy("End date"),
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    exercise = forms.ModelChoiceField(
        queryset=ExerciseTemplate.objects.none(),
        required=False,
        label=gettext_lazy("Exercise"),
    )
    routine = forms.ModelChoiceField(
        queryset=Routine.objects.none(), required=False, label=gettext_lazy("Routine")
    )
    muscle = forms.ChoiceField(
        required=False,
        label=gettext_lazy("Primary muscle"),
        choices=[("", gettext_lazy("All"))]
        + list(ExerciseTemplate.MuscleGroup.choices),
    )
    equipment = forms.ChoiceField(
        required=False,
        label=gettext_lazy("Equipment"),
        choices=[("", gettext_lazy("All"))]
        + list(ExerciseTemplate.EquipmentCategory.choices),
    )
    set_type = forms.ChoiceField(
        required=False,
        label=gettext_lazy("Set type"),
        choices=[("", gettext_lazy("All"))] + list(SetType.choices),
    )
    compare = forms.BooleanField(
        required=False, label=gettext_lazy("Compare with previous period")
    )

    def __init__(self, *args, account=None, panel="frequency", **kwargs):
        super().__init__(*args, **kwargs)
        if panel != "frequency":
            self.fields.pop("grouping")
        self.fields["exercise"].queryset = ExerciseTemplate.objects.filter(
            hevy_account=account
        )
        from training.translations import display_name

        self.fields["exercise"].label_from_instance = display_name
        self.fields["exercise"].empty_label = gettext_lazy("All")
        self.fields["routine"].empty_label = gettext_lazy("All")
        self.fields["routine"].queryset = Routine.objects.filter(hevy_account=account)

    def clean(self):
        values = super().clean()
        if values.get("end") == date.max:
            self.add_error("end", gettext_lazy("Choose an end date before 9999-12-31."))
        if (
            values.get("start")
            and values.get("end")
            and values["end"] < values["start"]
        ):
            self.add_error(
                "end", gettext_lazy("The end date must not precede the start date.")
            )
        return values


class PreferenceForm(StyledForm, forms.Form):
    panels = forms.MultipleChoiceField(
        label=gettext_lazy("Visible panels"),
        choices=PANELS,
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    favorites = forms.ModelMultipleChoiceField(
        label=gettext_lazy("Favorite exercises"),
        queryset=ExerciseTemplate.objects.none(),
        required=False,
    )

    def __init__(self, *args, account=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["favorites"].queryset = ExerciseTemplate.objects.filter(
            hevy_account=account
        )
        from training.translations import display_name

        self.fields["favorites"].label_from_instance = display_name
        order = self.initial.get("order", [])
        for index in range(1, len(PANELS) + 1):
            self.fields[f"position_{index}"] = forms.ChoiceField(
                label=gettext_lazy("Panel position %(number)s") % {"number": index},
                widget=forms.Select(attrs={"class": "input"}),
                choices=[("", gettext_lazy("Automatic order"))] + PANELS,
                required=False,
                initial=order[index - 1] if index <= len(order) else "",
            )

    def clean(self):
        values = super().clean()
        order = [values.get(f"position_{index}") for index in range(1, len(PANELS) + 1)]
        order = [item for item in order if item]
        if len(order) != len(set(order)):
            raise forms.ValidationError(gettext_lazy("Choose each panel only once in the order."))
        values["order"] = order
        return values


class FilteredAnalytics(AnalyticsService):
    def __init__(self, account, filters):
        super().__init__(account)
        self.filters = filters
        self.cache = {}

    def _matches(self, template, item):
        f = self.filters
        return (
            (not f.get("exercise") or template.pk == f["exercise"].pk)
            and (not f.get("muscle") or template.primary_muscle == f["muscle"])
            and (
                not f.get("equipment") or template.equipment_category == f["equipment"]
            )
            and (not f.get("set_type") or item.set_type == f["set_type"])
        )

    def _workouts(self, period, *, routine=None, exercise=None):
        routine = routine or self.filters.get("routine")
        exercise = exercise or self.filters.get("exercise")
        key = (
            period.start,
            period.end,
            getattr(routine, "pk", routine),
            getattr(exercise, "pk", exercise),
        )
        if key not in self.cache:
            workouts = super()._workouts(period, routine=routine, exercise=exercise)
            if any(
                self.filters.get(key)
                for key in ("muscle", "equipment", "set_type", "exercise")
            ):
                workouts = [
                    w
                    for w in workouts
                    if any(
                        self._matches(e.exercise_template, s)
                        for e in w.exercises.all()
                        for s in e.sets.all()
                    )
                ]
            self.cache[key] = workouts
        return self.cache[key]

    def _rows(self, workouts):
        return [row for row in super()._rows(workouts) if self._matches(row[1], row[2])]


def build_reports(account, filters, panel):
    service = FilteredAnalytics(account, filters)
    period = service.period(filters.get("start"), filters.get("end"))
    workouts = service._workouts(period)
    rows = service._rows(workouts)
    working = service._working_rows(rows)
    presenter = DashboardPresenter()
    charts = []
    preference = getattr(account.user, "fitness_preferences", None)

    def chart(identifier, title, values, unit, definition):
        from accounts.presentation import convert_series
        values, unit = convert_series(values, unit, preference)
        view = presenter._categorical_chart(
            dom_id=identifier,
            title=title,
            values=values,
            first_header=_("Observation"),
            unit=unit,
            summarize_points=True,
        )
        view.update(
            {
                "definition": definition,
                "source_count": len(rows),
                "missing_count": sum(item.rpe is None for _, _, item in working)
                if panel == "effort"
                else 0,
                "formula_version": "fitness-2.0",
                "freshness": max((w.synced_at for w in workouts), default=None),
            }
        )
        charts.append(view)

    by_workout = defaultdict(list)
    for w, template, item in working:
        by_workout[w.pk].append((template, item))
    labels = {
        w.pk: date_label(w.start_time, preference, include_time=True)
        + f" · {w.pk}"
        for w in workouts
    }
    ordered = sorted(workouts, key=lambda w: (w.start_time, w.pk))
    if panel == "frequency":
        monthly = filters.get("grouping") == "month" or (
            not filters.get("grouping") and period.days > 365
        )
        weeks = Counter()
        days = Counter()
        cursor = (
            period.start.replace(day=1)
            if monthly
            else period.start - timedelta(days=period.start.weekday())
        )
        while cursor <= period.end:
            weeks[cursor.isoformat()] = 0
            cursor = (
                (cursor.replace(day=28) + timedelta(days=4)).replace(day=1)
                if monthly
                else cursor + timedelta(days=7)
            )
        for w in workouts:
            day = timezone.localtime(w.start_time, service.zone).date()
            bucket = (
                day.replace(day=1) if monthly else day - timedelta(days=day.weekday())
            )
            weeks[bucket.isoformat()] += 1
            days[day.strftime("%A")] += 1
        chart(
            "frequency-weeks",
            _("Workouts per month") if monthly else _("Workouts per week"),
            dict(sorted(weeks.items())),
            _("workouts"),
            _("Sessions by local calendar period. Boundary periods may be incomplete."),
        )
        chart(
            "frequency-days",
            _("Training days"),
            days,
            _("workouts"),
            _("Sessions by local weekday."),
        )
    elif panel == "effort":
        metrics = service.rpe_metrics(period)
        chart(
            "effort-distribution",
            _("RPE distribution"),
            metrics["distribution"].value,
            _("sets"),
            _("Recorded RPE on working sets; missing values are excluded."),
        )
        means = {}
        for w in ordered:
            values = [s.rpe for _, s in by_workout[w.pk] if s.rpe is not None]
            if values:
                means[labels[w.pk]] = sum(values) / len(values)
        chart(
            "effort-evolution",
            _("Mean RPE over time"),
            means,
            "RPE",
            _("Mean recorded RPE per session, with missing observations excluded."),
        )
    elif panel == "distribution":
        chart(
            "distribution-muscles",
            _("Primary muscles"),
            Counter(t.primary_muscle or _("Unknown") for _, t, _ in working),
            _("sets"),
            _("Each working set contributes once to its primary muscle."),
        )
        chart(
            "distribution-equipment",
            _("Equipment"),
            Counter(t.equipment_category or _("Unknown") for _, t, _ in working),
            _("sets"),
            _("Working sets by recorded equipment."),
        )
        chart(
            "distribution-modalities",
            _("Modalities"),
            Counter(t.exercise_type for _, t, _ in working),
            _("sets"),
            _("Working-set counts, without adding incompatible quantities."),
        )
        chart(
            "distribution-routines",
            _("Routines"),
            Counter(
                w.routine.title if w.routine else _("Unassigned") for w in workouts
            ),
            _("workouts"),
            _("Recorded routine association, not historical prescription compliance."),
        )
    elif panel == "volume":
        chart(
            "volume-types",
            _("Sets by type"),
            Counter(s.set_type for _, _, s in rows),
            _("sets"),
            _("Warmups remain separate from working sets."),
        )
        volume = {}
        for w in ordered:
            eligible = [
                s.weight_kg * s.reps
                for t, s in by_workout[w.pk]
                if t.exercise_type == "weight_reps" and s.weight_kg and s.reps
            ]
            if eligible:
                volume[labels[w.pk]] = sum(eligible)
        chart(
            "volume-external",
            _("External-load volume"),
            volume,
            "kg·rep",
            _("Sum weight × repetitions on compatible working sets."),
        )
    elif panel in {"duration", "progression"}:
        if panel == "duration":
            chart(
                "duration-sessions",
                _("Session duration"),
                {
                    labels[w.pk]: Decimal(
                        str((w.end_time - w.start_time).total_seconds())
                    )
                    / 60
                    for w in ordered
                },
                _("minutes"),
                _("Elapsed session time is not active exercise time."),
            )
        exercise = filters.get("exercise")
        if exercise:
            fields = {
                "weight_kg": ("kg", _("Recorded load / assistance")),
                "reps": (_("repetitions"), _("Recorded repetitions")),
                "duration_seconds": ("s", _("Recorded duration")),
                "distance_meters": ("m", _("Recorded distance")),
                "custom_metric": (_("custom units"), _("Custom metric")),
            }
            from integrations.routines import COMPATIBLE_FIELDS

            for field in COMPATIBLE_FIELDS.get(
                exercise.exercise_type, {"custom_metric"}
            ) - {"rep_range"}:
                unit, title = fields[field]
                values = {}
                for w in ordered:
                    sample = [
                        getattr(s, field)
                        for t, s in by_workout[w.pk]
                        if t.pk == exercise.pk and getattr(s, field) is not None
                    ]
                    if sample:
                        values[labels[w.pk]] = max(sample)
                chart(
                    "exercise-" + field,
                    title,
                    values,
                    unit,
                    _(
                        "Maximum recorded value per session for the selected exercise only."
                    ),
                )
            if exercise.exercise_type == "weight_reps":
                estimates, volumes, by_load = {}, {}, defaultdict(dict)
                for w in ordered:
                    sample = [
                        s
                        for t, s in by_workout[w.pk]
                        if t.pk == exercise.pk and s.weight_kg and s.reps
                    ]
                    for s in sample:
                        by_load[s.weight_kg][labels[w.pk]] = max(
                            by_load[s.weight_kg].get(labels[w.pk], 0), s.reps
                        )
                    if sample:
                        volumes[labels[w.pk]] = sum(
                            s.weight_kg * s.reps for s in sample
                        )
                    eligible = [
                        s.weight_kg * (1 + s.reps / Decimal(30))
                        for s in sample
                        if s.set_type in E1RM_TYPES
                        and 1 <= s.reps <= 10
                        and s.reps == int(s.reps)
                    ]
                    if eligible:
                        estimates[labels[w.pk]] = max(eligible)
                chart(
                    "exercise-e1rm",
                    _("Estimated 1RM"),
                    estimates,
                    "kg",
                    _(
                        "Epley estimate: weight × (1 + reps / 30), normal/failure sets, 1–10 integer repetitions."
                    ),
                )
                chart(
                    "exercise-volume",
                    _("Exercise volume"),
                    volumes,
                    "kg·rep",
                    _("External-load working volume for this exercise."),
                )
                for index, (load, values) in enumerate(sorted(by_load.items())):
                    chart(
                        "load-reps-" + str(index),
                        _("Repetitions at the same load") + f" · {load} kg",
                        values,
                        _("repetitions"),
                        _("Maximum repetitions at this exact load, per session."),
                    )
    activity = service.workout_activity(period)
    summary = [
        value for key, value in activity.items() if key != "weekday_distribution"
    ]
    if panel == "effort":
        summary.extend(
            [service.rpe_metrics(period)["mean"], service.rpe_metrics(period)["median"]]
        )
    if panel == "frequency":
        summary.extend([service.weekly_target_consistency(period)])
    previous = None
    if filters.get("compare"):
        previous_period = service.period(
            period.start - timedelta(days=period.days), period.start - timedelta(days=1)
        )
        previous = service.compare_periods(
            lambda p: service.workout_activity(p)["workouts"], period, previous_period
        )
    return {
        "charts": charts,
        "period": period,
        "summary_metrics": summary,
        "comparison": previous,
        "streaks": service.streaks(period),
        "needs_exercise": panel == "progression" and not filters.get("exercise"),
    }
