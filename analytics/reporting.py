"""Local report calculations and comparisons, independent of HTML/SVG rendering."""

from collections import Counter, defaultdict
from datetime import date, timedelta
from decimal import Decimal

from django.utils import timezone
from django.utils.translation import gettext as _

from analytics.services import E1RM_TYPES, AnalyticsService
from training.models import ExerciseTemplate, SetType


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


def build_report_data(account, filters, panel, *, include_comparison=True):
    service = FilteredAnalytics(account, filters)
    period = service.period(filters.get("start"), filters.get("end"))
    workouts = service._workouts(period)
    rows = service._rows(workouts)
    working = service._working_rows(rows)
    charts = []
    preference = getattr(account.user, "fitness_preferences", None)

    def chart(identifier, title, values, unit, definition):
        kind = (
            "horizontal"
            if identifier.startswith("distribution-")
            or identifier in {"volume-types", "frequency-days"}
            else "bar"
        )
        temporal = identifier not in {
            "frequency-days",
            "effort-distribution",
            "volume-types",
        } and not identifier.startswith("distribution-")
        if temporal and identifier not in {"frequency-weeks", "frequency-target"}:
            kind = "line"
        if identifier.startswith("distribution-"):
            values = dict(
                sorted(values.items(), key=lambda item: (-item[1], str(item[0])))
            )
        charts.append(
            {
                "dom_id": identifier,
                "title": title,
                "values": values,
                "unit": unit,
                "definition": definition,
                "kind": kind,
                "temporal": temporal,
                "formula_version": "fitness-2.1",
                "source_count": len(rows),
                "missing_count": sum(s.rpe is None for _, _, s in working)
                if panel == "effort"
                else sum(value is None for value in values.values()),
            }
        )

    by_workout = defaultdict(list)
    for w, template, item in working:
        by_workout[w.pk].append((template, item))
    labels = {w.pk: (w.start_time, w.pk) for w in workouts}
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
            weeks[cursor] = 0
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
            weeks[bucket] += 1
            days[day.weekday()] += 1
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
            {
                label: days[index]
                for index, label in enumerate(
                    [
                        _("Monday"),
                        _("Tuesday"),
                        _("Wednesday"),
                        _("Thursday"),
                        _("Friday"),
                        _("Saturday"),
                        _("Sunday"),
                    ]
                )
            },
            _("workouts"),
            _("Sessions by local weekday."),
        )
        target = getattr(preference, "weekly_session_target", None)
        if target:
            weekly = Counter()
            cursor = period.start - timedelta(days=period.start.weekday())
            while cursor <= period.end:
                weekly[cursor] = 0
                cursor += timedelta(days=7)
            for w in workouts:
                day = timezone.localtime(w.start_time, service.zone).date()
                weekly[day - timedelta(days=day.weekday())] += 1
            chart(
                "frequency-target",
                _("Weekly sessions and target"),
                dict(sorted(weekly.items())),
                _("workouts"),
                _(
                    "Sessions per local week. Boundary weeks may be partial; only complete weeks count toward target completion."
                ),
            )
            charts[-1]["target"] = target
    elif panel == "effort":
        metrics = service.rpe_metrics(period)
        chart(
            "effort-distribution",
            _("RPE distribution"),
            dict(
                sorted(
                    metrics["distribution"].value.items(),
                    key=lambda pair: Decimal(str(pair[0])),
                )
            ),
            _("sets"),
            _("Recorded RPE on working sets; missing values are excluded."),
        )
        means = {}
        for w in ordered:
            values = [s.rpe for _, s in by_workout[w.pk] if s.rpe is not None]
            means[labels[w.pk]] = sum(values) / len(values) if values else None
        chart(
            "effort-evolution",
            _("Mean RPE over time"),
            means,
            "RPE",
            _("Mean recorded RPE per session, with missing observations excluded."),
        )
    elif panel == "distribution":
        # Translate each code once per request, not once per working set.
        muscles = {
            key: str(label) for key, label in ExerciseTemplate.MuscleGroup.choices
        }
        equipment = {
            key: str(label) for key, label in ExerciseTemplate.EquipmentCategory.choices
        }
        modalities = {
            key: str(label) for key, label in ExerciseTemplate.ExerciseType.choices
        }
        unknown = _("Unknown")
        chart(
            "distribution-muscles",
            _("Primary muscles"),
            Counter(muscles.get(t.primary_muscle, unknown) for _, t, _ in working),
            _("sets"),
            _("Each working set contributes once to its primary muscle."),
        )
        chart(
            "distribution-equipment",
            _("Equipment"),
            Counter(
                equipment.get(t.equipment_category, unknown) for _, t, _ in working
            ),
            _("sets"),
            _("Working sets by recorded equipment."),
        )
        chart(
            "distribution-modalities",
            _("Modalities"),
            Counter(modalities.get(t.exercise_type, unknown) for _, t, _ in working),
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
        weekly = Counter()
        cursor = period.start - timedelta(days=period.start.weekday())
        while cursor <= period.end:
            weekly[cursor] = 0
            cursor += timedelta(days=7)
        for w, template, item in working:
            day = timezone.localtime(w.start_time, service.zone).date()
            weekly[day - timedelta(days=day.weekday())] += 1
        muscle = dict(ExerciseTemplate.MuscleGroup.choices).get(
            filters.get("muscle"), _("All primary muscles")
        )
        chart(
            "muscle-weekly",
            _("Weekly working sets") + " · " + str(muscle),
            dict(sorted(weekly.items())),
            _("sets"),
            _(
                "Each working set counts once for its primary muscle. Select a muscle to inspect its weekly distribution."
            ),
        )
    elif panel == "volume":
        set_labels = {key: str(label) for key, label in SetType.choices}
        chart(
            "volume-types",
            _("Sets by type"),
            Counter(set_labels[s.set_type] for _, _, s in rows),
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
            volume[labels[w.pk]] = sum(eligible) if eligible else None
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

            for field in fields:
                if field not in COMPATIBLE_FIELDS.get(
                    exercise.exercise_type, {"custom_metric"}
                ):
                    continue
                unit, title = fields[field]
                values = {}
                for w in ordered:
                    sample = [
                        getattr(s, field)
                        for t, s in by_workout[w.pk]
                        if t.pk == exercise.pk and getattr(s, field) is not None
                    ]
                    values[labels[w.pk]] = max(sample) if sample else None
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
                    volumes[labels[w.pk]] = (
                        sum(s.weight_kg * s.reps for s in sample) if sample else None
                    )
                    eligible = [
                        s.weight_kg * (1 + s.reps / Decimal(30))
                        for s in sample
                        if s.set_type in E1RM_TYPES
                        and 1 <= s.reps <= 10
                        and s.reps == int(s.reps)
                    ]
                    estimates[labels[w.pk]] = max(eligible) if eligible else None
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
                    if len(values) < 2:
                        continue
                    chart(
                        "load-reps-" + str(index),
                        _("Repetitions at the same load"),
                        values,
                        _("repetitions"),
                        _("Maximum repetitions at this exact load, per session."),
                    )
                    charts[-1]["load_kg"] = load
    for view in charts:
        if view["dom_id"] in {"frequency-weeks", "frequency-target", "muscle-weekly"}:
            monthly = view["dom_id"] == "frequency-weeks" and (
                filters.get("grouping") == "month"
                or (not filters.get("grouping") and period.days > 365)
            )
            view["partial_keys"] = []
            for start in view["values"]:
                end = (
                    (start.replace(day=28) + timedelta(days=4)).replace(day=1)
                    - timedelta(days=1)
                    if monthly
                    else start + timedelta(days=6)
                )
                if start < period.start or end > period.end:
                    view["partial_keys"].append(start)
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
    scalars = report_scalars(service, period, panel, filters, charts)
    comparisons = []
    if (
        filters.get("compare")
        and include_comparison
        and period.start > date.min + timedelta(days=period.days)
    ):
        previous_filters = {
            **filters,
            "start": period.start - timedelta(days=period.days),
            "end": period.start - timedelta(days=1),
        }
        previous = build_report_data(
            account, previous_filters, panel, include_comparison=False
        )["scalars"]
        for key in dict.fromkeys([*scalars, *previous]):
            current = scalars.get(key)
            old = previous.get(key)
            meta = current or old
            current_value = current["value"] if current else Decimal(0)
            old_value = old["value"] if old else Decimal(0)
            absolute = (
                current_value - old_value
                if current_value is not None and old_value is not None
                else None
            )
            percent = (
                Decimal(absolute) / Decimal(old_value) * 100
                if absolute is not None and old_value not in (None, 0)
                else None
            )
            comparisons.append(
                {
                    **meta,
                    "current": current_value,
                    "previous": old_value,
                    "absolute": absolute,
                    "percent": percent,
                }
            )
    records = []
    if panel == "progression" and filters.get("exercise"):
        for view in charts:
            if view["dom_id"].startswith("load-reps-"):
                continue
            valid = [
                (key, value)
                for key, value in view["values"].items()
                if value is not None
            ]
            if valid:
                key, value = max(valid, key=lambda pair: pair[1])
                records.append(
                    {
                        "name": view["title"],
                        "value": value,
                        "unit": view["unit"],
                        "at": key[0],
                    }
                )
    return {
        "charts": charts,
        "period": period,
        "summary_metrics": summary,
        "comparisons": comparisons,
        "scalars": scalars,
        "records": records,
        "streaks": service.streaks(period),
        "needs_exercise": panel == "progression" and not filters.get("exercise"),
        "rpe_coverage": service.rpe_metrics(period)["missing"]
        if panel == "effort"
        else None,
    }


def report_scalars(service, period, panel, filters, charts):
    """Comparable values retain canonical units until the presentation boundary."""
    result = {}

    def add(key, name, value, unit):
        result[key] = {"name": name, "value": value, "unit": unit}

    activity = service.workout_activity(period)
    add("sessions", _("Workouts"), activity["workouts"].value, _("workouts"))
    add(
        "frequency",
        _("Weekly frequency"),
        Decimal(activity["workouts"].value) * 7 / period.days,
        _("workouts/week"),
    )
    if panel == "effort":
        add("rpe", _("Mean RPE"), service.rpe_metrics(period)["mean"].value, "RPE")
    if panel in {"volume", "distribution"}:
        working = service._working_rows(service._rows(service._workouts(period)))
        add("working_sets", _("Working sets"), len(working), _("sets"))
    for chart in charts:
        identifier = chart["dom_id"]
        values = [value for value in chart["values"].values() if value is not None]
        if panel == "progression" and not identifier.startswith("load-reps-"):
            add(
                identifier,
                chart["title"],
                max(values) if values else None,
                chart["unit"],
            )
        if identifier in {"volume-external", "exercise-volume"}:
            add(
                identifier,
                chart["title"],
                sum(values) if values else None,
                chart["unit"],
            )
        if identifier == "distribution-muscles":
            for name, value in chart["values"].items():
                add("muscle-" + name, name, value, _("sets"))
        if identifier == "duration-sessions":
            add(
                "duration-total",
                _("Total session duration"),
                sum(values) if values else None,
                chart["unit"],
            )
            add(
                "duration-mean",
                _("Mean session duration"),
                sum(values) / len(values) if values else None,
                chart["unit"],
            )
    return result
