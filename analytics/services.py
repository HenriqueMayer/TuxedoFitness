from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from statistics import median
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.utils import timezone

from accounts.models import OwnerPreference
from training.models import ExerciseTemplate, SetType, Workout

FORMULA_VERSION = 'sprint-5-v1'
DEFAULT_TIMEZONE = 'America/Sao_Paulo'
WORKING_TYPES = frozenset({SetType.NORMAL, SetType.FAILURE, SetType.DROPSET})
E1RM_TYPES = frozenset({SetType.NORMAL, SetType.FAILURE})
REP_TYPES = frozenset({
    ExerciseTemplate.ExerciseType.WEIGHT_REPS,
    ExerciseTemplate.ExerciseType.REPS_ONLY,
    ExerciseTemplate.ExerciseType.BODYWEIGHT_REPS,
    ExerciseTemplate.ExerciseType.BODYWEIGHT_ASSISTED_REPS,
})


@dataclass(frozen=True)
class LocalPeriod:
    start: date
    end: date
    timezone_name: str

    @property
    def days(self):
        return (self.end - self.start).days + 1

    @property
    def start_at(self):
        return datetime.combine(self.start, time.min, tzinfo=ZoneInfo(self.timezone_name))

    @property
    def end_at(self):
        return datetime.combine(
            self.end + timedelta(days=1), time.min, tzinfo=ZoneInfo(self.timezone_name)
        )


@dataclass(frozen=True)
class MetricResult:
    metric_id: str
    name: str
    question: str
    value: object
    unit: str
    definition: str
    filters: dict
    included_set_types: tuple[str, ...]
    source_entity_count: int
    missing_value_count: int
    validity: str
    limitation: str
    data_freshness: datetime | None = None
    formula_version: str = FORMULA_VERSION

    @property
    def is_valid(self):
        return self.validity == 'valid'

    def as_dict(self):
        return {
            'metric_id': self.metric_id,
            'name': self.name,
            'question': self.question,
            'value': self.value,
            'unit': self.unit,
            'definition': self.definition,
            'filters': self.filters,
            'formula_version': self.formula_version,
            'included_set_types': list(self.included_set_types),
            'source_entity_count': self.source_entity_count,
            'missing_value_count': self.missing_value_count,
            'validity': self.validity,
            'is_valid': self.is_valid,
            'limitation': self.limitation,
            'data_freshness': self.data_freshness,
        }


def _result(metric_id, name, question, value, unit, definition, *, filters=None,
            included=(), source_count=0, missing=0, valid=True, limitation='',
            freshness=None):
    return MetricResult(
        metric_id=metric_id,
        name=name,
        question=question,
        value=value,
        unit=unit,
        definition=definition,
        filters=filters or {},
        included_set_types=tuple(included),
        source_entity_count=source_count,
        missing_value_count=missing,
        validity='valid' if valid else 'insufficient_data',
        limitation=limitation,
        data_freshness=freshness or timezone.now(),
    )


def _zone_for(user=None, timezone_name=None):
    if timezone_name is None and user is not None:
        try:
            timezone_name = user.fitness_preferences.presentation_timezone
        except OwnerPreference.DoesNotExist:
            timezone_name = None
    timezone_name = timezone_name or DEFAULT_TIMEZONE
    try:
        ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f'Unknown presentation timezone: {timezone_name}') from exc
    return timezone_name


def local_period(user=None, start=None, end=None, timezone_name=None):
    zone_name = _zone_for(user, timezone_name)
    today = timezone.localtime(timezone.now(), ZoneInfo(zone_name)).date()
    end = end or today
    start = start or end - timedelta(days=27)
    if isinstance(start, datetime):
        if timezone.is_naive(start):
            raise ValueError('Period datetimes must include a timezone.')
        start = start.astimezone(ZoneInfo(zone_name)).date()
    if isinstance(end, datetime):
        if timezone.is_naive(end):
            raise ValueError('Period datetimes must include a timezone.')
        end = end.astimezone(ZoneInfo(zone_name)).date()
    if end < start:
        raise ValueError('Period end must not precede period start.')
    return LocalPeriod(start, end, zone_name)


def _percent(numerator, denominator):
    if denominator in (None, 0):
        return None
    return (Decimal(numerator) / Decimal(denominator) * Decimal('100')).quantize(Decimal('0.01'))


def _slope(points):
    if len(points) < 2:
        return None
    points = [(Decimal(str(x)), Decimal(y)) for x, y in points]
    mean_x = sum(x for x, _ in points) / Decimal(len(points))
    mean_y = sum(y for _, y in points) / len(points)
    denominator = sum((x - mean_x) ** 2 for x, _ in points)
    if denominator == 0:
        return Decimal('0')
    return sum((x - mean_x) * (y - mean_y) for x, y in points) / denominator


def _x_value(value):
    if isinstance(value, datetime):
        return Decimal(str(value.timestamp())) / Decimal('86400')
    if isinstance(value, date):
        return Decimal(value.toordinal())
    return Decimal(str(value))


class AnalyticsService:
    def __init__(self, account, *, user=None, timezone_name=None):
        self.account = account
        self.user = user or account.user
        self.timezone_name = _zone_for(self.user, timezone_name)
        self.zone = ZoneInfo(self.timezone_name)

    def period(self, start=None, end=None):
        return local_period(self.user, start, end, self.timezone_name)

    def _workouts(self, period, *, routine=None, exercise=None):
        queryset = Workout.objects.filter(
            hevy_account=self.account,
            start_time__gte=period.start_at,
            start_time__lt=period.end_at,
        ).prefetch_related(
            'exercises__sets',
            'exercises__exercise_template__secondary_muscles',
        )
        if routine is not None:
            queryset = queryset.filter(routine_id=getattr(routine, 'pk', routine))
        if exercise is not None:
            queryset = queryset.filter(exercises__exercise_template_id=getattr(exercise, 'pk', exercise))
        return list(queryset.distinct())

    def _rows(self, workouts):
        rows = []
        for workout in workouts:
            for exercise in workout.exercises.all():
                template = exercise.exercise_template
                for recorded_set in exercise.sets.all():
                    rows.append((workout, template, recorded_set))
        return rows

    @staticmethod
    def _compatible(template, recorded_set):
        kind = template.exercise_type
        fields = {
            ExerciseTemplate.ExerciseType.WEIGHT_REPS: ('weight_kg', 'reps'),
            ExerciseTemplate.ExerciseType.REPS_ONLY: ('reps',),
            ExerciseTemplate.ExerciseType.BODYWEIGHT_REPS: ('reps',),
            ExerciseTemplate.ExerciseType.BODYWEIGHT_ASSISTED_REPS: ('weight_kg', 'reps'),
            ExerciseTemplate.ExerciseType.DURATION: ('duration_seconds',),
            ExerciseTemplate.ExerciseType.WEIGHT_DURATION: ('weight_kg', 'duration_seconds'),
            ExerciseTemplate.ExerciseType.DISTANCE_DURATION: ('distance_meters', 'duration_seconds'),
            ExerciseTemplate.ExerciseType.SHORT_DISTANCE_WEIGHT: ('distance_meters', 'weight_kg'),
        }.get(kind, ('custom_metric',))
        return any(getattr(recorded_set, field) is not None for field in fields)

    def _working_rows(self, rows):
        return [
            row for row in rows
            if row[2].set_type in WORKING_TYPES and self._compatible(row[1], row[2])
        ]

    def workout_activity(self, period=None, *, routine=None, exercise=None):
        period = period or self.period()
        workouts = self._workouts(period, routine=routine, exercise=exercise)
        dates = {timezone.localtime(item.start_time, self.zone).date() for item in workouts}
        return {
            'workouts': _result('M-A01', 'Workouts', 'How many sessions occurred?', len(workouts), 'workouts',
                                'Count distinct active workout IDs.', source_count=len(workouts),
                                limitation='A session count does not measure quality.'),
            'training_days': _result('M-A04', 'Training days', 'On how many local dates did training occur?',
                                     len(dates), 'days', 'Count distinct local start dates.', source_count=len(workouts)),
            'average_frequency': _result('M-A03', 'Average frequency', 'How often did training occur?',
                                         (Decimal(len(workouts)) / period.days * 7).quantize(Decimal('0.01')),
                                         'sessions/week', 'workouts / inclusive_days × 7', source_count=len(workouts)),
            'weekday_distribution': _result(
                'M-A06', 'Weekday distribution', 'Which weekdays contain workouts?',
                dict(Counter(timezone.localtime(item.start_time, self.zone).strftime('%A') for item in workouts)),
                'workouts', 'Count workouts by local weekday.', source_count=len(workouts),
            ),
        }

    def activity_buckets(self, period=None, *, bucket='week'):
        period = period or self.period()
        workouts = self._workouts(period)
        if bucket not in {'week', 'month'}:
            raise ValueError('Activity bucket must be week or month.')
        keys = []
        for workout in workouts:
            local_date = timezone.localtime(workout.start_time, self.zone).date()
            keys.append(local_date - timedelta(days=local_date.weekday()) if bucket == 'week'
                        else local_date.replace(day=1))
        return _result('M-A02', 'Workouts by period', 'When did sessions occur?',
                       dict(Counter(keys)), f'workouts/{bucket}', 'Count workouts by local calendar bucket.',
                       source_count=len(workouts))

    def duration_metrics(self, period=None, *, routine=None, exercise=None):
        period = period or self.period()
        workouts = self._workouts(period, routine=routine, exercise=exercise)
        durations = [
            Decimal(str((item.end_time - item.start_time).total_seconds()))
            for item in workouts if item.end_time >= item.start_time
        ]
        values = {
            'total_seconds': sum(durations, Decimal('0')),
            'average_seconds': (sum(durations, Decimal('0')) / len(durations)).quantize(Decimal('0.01'))
            if durations else None,
        }
        return _result('M-A05', 'Duration', 'How much session time was recorded?', values, 'seconds',
                       'Sum and arithmetic mean of end_time - start_time.', source_count=len(workouts),
                       missing=len(workouts) - len(durations), valid=bool(durations),
                       limitation='Elapsed session time is not active exercise time.')

    def set_metrics(self, period=None, *, routine=None, exercise=None):
        period = period or self.period()
        rows = self._rows(self._workouts(period, routine=routine, exercise=exercise))
        counts = Counter(item[2].set_type for item in rows)
        unknown_types = set(counts) - set(SetType.values)
        working = self._working_rows(rows)
        repetitions = [item[2].reps for item in rows if item[1].exercise_type in REP_TYPES and item[2].reps is not None]
        volume_rows = [
            item for item in working
            if item[1].exercise_type == ExerciseTemplate.ExerciseType.WEIGHT_REPS
            and item[2].weight_kg is not None and item[2].weight_kg > 0
            and item[2].reps is not None and item[2].reps > 0
        ]
        volume = sum((item[2].weight_kg * item[2].reps for item in volume_rows), Decimal('0'))
        return {
            'total_sets': _result('M-S01', 'Total sets', 'How many sets were recorded?', len(rows), 'sets',
                                  'Count workout-set rows.', included=counts.keys(), source_count=len(rows)),
            'working_sets': _result('M-S02', 'Working sets', 'How many non-warmup sets were recorded?', len(working), 'sets',
                                    'Count normal, failure, and dropset sets with a compatible metric.',
                                    included=WORKING_TYPES, source_count=len(rows), missing=len(rows) - len(working)),
            'set_type_counts': _result('M-S03', 'Set-type counts', 'What was the set composition?', dict(counts), 'sets',
                                       'Count sets by recorded type.', included=counts.keys(), source_count=len(rows),
                                       valid=not unknown_types, limitation='Unknown set types require mapping.' if unknown_types else ''),
            'repetitions': _result('M-S04', 'Total repetitions', 'How many repetitions were recorded?',
                                   sum(repetitions, Decimal('0')) if repetitions else None, 'reps',
                                   'Sum non-null repetitions on rep-based templates.', included=counts.keys(),
                                   source_count=len(rows), missing=sum(1 for item in rows if item[1].exercise_type in REP_TYPES and item[2].reps is None),
                                   valid=bool(repetitions)),
            'external_load_volume': _result('M-S06', 'External-load volume', 'How much compatible load was recorded?',
                                            volume if volume_rows else None, 'kg·rep', 'Σ(weight_kg × reps).',
                                            included=WORKING_TYPES, source_count=len(rows),
                                            missing=len(working) - len(volume_rows), valid=bool(volume_rows),
                                            limitation='Not valid for incompatible modalities.'),
            'sets_by_exercise': Counter(item[1].external_id for item in working),
        }

    def repetition_metrics(self, period=None, **filters):
        return self.set_metrics(period, **filters)['repetitions']

    def working_set_definition(self, period=None, **filters):
        return self.set_metrics(period, **filters)['working_sets']

    def modality_metrics(self, period=None, *, exercise=None):
        period = period or self.period()
        rows = self._working_rows(self._rows(self._workouts(period, exercise=exercise)))
        grouped = defaultdict(lambda: {'reps': [], 'assistance': [], 'duration_seconds': [], 'distance_meters': [], 'weights': [], 'custom_metric': []})
        for _, template, recorded_set in rows:
            values = grouped[template.external_id]
            if recorded_set.reps is not None:
                values['reps'].append(recorded_set.reps)
            if recorded_set.weight_kg is not None:
                values['weights'].append(recorded_set.weight_kg)
            if recorded_set.duration_seconds is not None:
                values['duration_seconds'].append(recorded_set.duration_seconds)
            if recorded_set.distance_meters is not None:
                values['distance_meters'].append(recorded_set.distance_meters)
            if recorded_set.custom_metric is not None:
                values['custom_metric'].append(recorded_set.custom_metric)
        for template_id, values in grouped.items():
            template = next(template for _, template, _ in rows if template.external_id == template_id)
            values['exercise_type'] = template.exercise_type
            values['reps_total'] = sum(values['reps'], Decimal('0')) if values['reps'] else None
            values['duration_total'] = sum(values['duration_seconds'], Decimal('0')) if values['duration_seconds'] else None
            values['distance_total'] = sum(values['distance_meters'], Decimal('0')) if values['distance_meters'] else None
            values['custom_total'] = sum(values['custom_metric'], Decimal('0')) if values['custom_metric'] else None
            values['maximum_weight'] = max(values['weights']) if values['weights'] else None
        return grouped

    def rpe_metrics(self, period=None, *, routine=None, exercise=None):
        period = period or self.period()
        working = self._working_rows(self._rows(self._workouts(period, routine=routine, exercise=exercise)))
        values = [item[2].rpe for item in working if item[2].rpe is not None]
        missing = len(working) - len(values)
        distribution = Counter(values)
        return {
            'mean': _result('M-R01', 'Mean RPE', 'What effort was recorded?',
                            (sum(values, Decimal('0')) / len(values)).quantize(Decimal('0.01')) if values else None,
                            'RPE', 'Arithmetic mean of recorded working-set RPE.', included=WORKING_TYPES,
                            source_count=len(working), missing=missing, valid=bool(values)),
            'median': _result('M-R01', 'Median RPE', 'What effort was recorded?', median(values) if values else None,
                              'RPE', 'Median of recorded working-set RPE.', included=WORKING_TYPES,
                              source_count=len(working), missing=missing, valid=bool(values)),
            'distribution': _result('M-R02', 'RPE distribution', 'How are recorded RPE values distributed?',
                                    dict(distribution), 'sets/percent', 'Count working sets by recorded RPE.',
                                    included=WORKING_TYPES, source_count=len(working), missing=missing,
                                    valid=bool(values)),
            'missing': _result('M-R03', 'Missing RPE', 'How complete is RPE recording?',
                               {'count': missing, 'percent': _percent(missing, len(working))}, 'count/percent',
                               'working sets without RPE / all working sets.', included=WORKING_TYPES,
                               source_count=len(working), missing=missing, valid=bool(working)),
        }

    def records(self, template, period=None):
        period = period or self.period()
        rows = [row for row in self._working_rows(self._rows(self._workouts(period))) if row[1].pk == getattr(template, 'pk', template)]
        eligible = [row for row in rows if row[1].exercise_type == ExerciseTemplate.ExerciseType.WEIGHT_REPS and row[2].set_type in E1RM_TYPES and row[2].weight_kg and row[2].reps and row[2].reps == int(row[2].reps)]
        by_load = defaultdict(list)
        for _, _, recorded_set in eligible:
            by_load[recorded_set.weight_kg].append(recorded_set.reps)
        e1rms = [recorded_set.weight_kg * (Decimal('1') + recorded_set.reps / Decimal('30')) for _, _, recorded_set in eligible if 1 <= recorded_set.reps <= 10]
        return {
            'maximum_load': max((item[2].weight_kg for item in eligible), default=None),
            'repetitions_at_load': {load: max(reps) for load, reps in by_load.items()},
            'set_volume': max((item[2].weight_kg * item[2].reps for item in eligible), default=None),
            'estimated_1rm': max(e1rms, default=None),
            'estimated_1rm_is_estimate': True,
            'eligible_set_count': len(eligible),
        }

    def e1rm(self, template, period=None):
        return self.records(template, period)['estimated_1rm']

    def compare_periods(self, metric, current, previous):
        current_value = metric(current).value
        previous_value = metric(previous).value
        absolute = None if current_value is None or previous_value is None else current_value - previous_value
        percent = None if absolute is None or previous_value in (None, 0) else _percent(absolute, previous_value)
        return {'current': current_value, 'previous': previous_value, 'absolute': absolute, 'percent': percent,
                'validity': 'valid' if current_value is not None and previous_value is not None else 'insufficient_data'}

    def trend_slope(self, points, *, days=30):
        numeric = [(_x_value(x), Decimal(str(y))) for x, y in points if y is not None]
        slope = _slope(numeric)
        return None if slope is None else (slope * Decimal(days)).quantize(Decimal('0.01'))

    def frequency_duration_trend(self, period=None):
        period = period or self.period()
        workouts = self._workouts(period)
        buckets = defaultdict(lambda: {'count': 0, 'duration': Decimal('0')})
        for workout in workouts:
            local_date = timezone.localtime(workout.start_time, self.zone).date()
            week = local_date - timedelta(days=local_date.weekday())
            buckets[week]['count'] += 1
            if workout.end_time >= workout.start_time:
                buckets[week]['duration'] += Decimal(str((workout.end_time - workout.start_time).total_seconds()))
        ordered = sorted(buckets)
        return {
            'frequency_slope': self.trend_slope([(index * 7, buckets[key]['count']) for index, key in enumerate(ordered)])
            if len(ordered) >= 4 else None,
            'duration_slope': self.trend_slope([(index * 7, buckets[key]['duration']) for index, key in enumerate(ordered)])
            if len(ordered) >= 4 else None,
            'validity': 'valid' if len(ordered) >= 4 else 'insufficient_data',
        }

    def muscle_distribution(self, period=None):
        period = period or self.period()
        rows = self._working_rows(self._rows(self._workouts(period)))
        primary = Counter()
        secondary = Counter()
        for _, template, _ in rows:
            if template.primary_muscle:
                primary[template.primary_muscle] += 1
            secondary.update(muscle.muscle_code for muscle in template.secondary_muscles.all())
        return {
            'executed_primary': _result('M-M01', 'Executed primary-muscle sets', 'Where were working sets assigned?',
                                        dict(primary), 'sets', 'Count each working set once for its primary muscle.',
                                        included=WORKING_TYPES, source_count=len(rows), valid=bool(rows)),
            'executed_secondary': _result('M-M02', 'Executed secondary-muscle coverage', 'Which secondary muscles were associated?',
                                          dict(secondary), 'associations', 'Count each working set once for each listed secondary muscle.',
                                          included=WORKING_TYPES, source_count=len(rows), valid=bool(rows)),
        }

    def primary_secondary_muscles(self, period=None):
        return self.muscle_distribution(period)

    def weekly_target_consistency(self, period=None):
        period = period or self.period()
        target = getattr(getattr(self.user, 'fitness_preferences', None), 'weekly_session_target', None)
        if not target:
            return _result('M-C01', 'Target completion', 'How many target sessions were completed?', None, 'ratio/percent',
                           'completed sessions / weekly target.', valid=False, limitation='Weekly target is not configured.')
        workouts = self._workouts(period)
        counts = Counter(timezone.localtime(item.start_time, self.zone).date() - timedelta(days=timezone.localtime(item.start_time, self.zone).date().weekday()) for item in workouts)
        complete = {week: count for week, count in counts.items() if week + timedelta(days=6) <= period.end and week >= period.start}
        complete_weeks = len(complete)
        completed_weeks = sum(count >= target for count in complete.values())
        completed_sessions = sum(complete.values())
        target_sessions = target * complete_weeks
        return _result('M-C01', 'Target completion', 'How many target sessions were completed?',
                       {'completed_sessions': completed_sessions, 'target_sessions': target_sessions,
                        'completed_weeks': completed_weeks, 'complete_weeks': complete_weeks,
                        'ratio': (Decimal(completed_sessions) / target_sessions) if target_sessions else None,
                        'percent': _percent(completed_sessions, target_sessions)}, 'ratio/percent',
                       'completed sessions / weekly target.', source_count=len(workouts),
                       valid=bool(complete_weeks), limitation='The current partial week is in progress.')

    def streaks(self, period=None):
        period = period or self.period()
        workouts = self._workouts(period)
        weeks = {timezone.localtime(item.start_time, self.zone).date() - timedelta(days=timezone.localtime(item.start_time, self.zone).date().weekday()) for item in workouts}
        if not weeks:
            return {'activity': 0, 'target': None}
        latest = max(weeks)
        activity = 0
        while latest - timedelta(days=7 * activity) in weeks:
            activity += 1
        target_result = self.weekly_target_consistency(period)
        target = getattr(getattr(self.user, 'fitness_preferences', None), 'weekly_session_target', None)
        target_streak = None
        if target:
            weekly_counts = Counter(timezone.localtime(item.start_time, self.zone).date() - timedelta(days=timezone.localtime(item.start_time, self.zone).date().weekday()) for item in workouts)
            target_streak = 0
            complete_weeks = [week for week in weekly_counts if week + timedelta(days=6) <= period.end]
            cursor = max(complete_weeks, default=None)
            if cursor is None:
                return {'activity': activity, 'target': None, 'target_metric': target_result}
            while weekly_counts[cursor] >= target:
                target_streak += 1
                cursor -= timedelta(days=7)
        return {'activity': activity, 'target': target_streak, 'target_metric': target_result}

    def build_overview(self, start=None, end=None, **filters):
        period = self.period(start, end)
        activity = self.workout_activity(period, **filters)
        metrics = {**activity, 'duration': self.duration_metrics(period, **filters), **self.set_metrics(period, **filters),
                   'activity_buckets': self.activity_buckets(
                       period, bucket='week' if period.days <= 365 else 'month'
                   ),
                   'rpe': self.rpe_metrics(period, **filters), 'target': self.weekly_target_consistency(period),
                   'streaks': self.streaks(period), 'muscles': self.muscle_distribution(period)}
        return {'period': period, 'metrics': metrics, 'formula_version': FORMULA_VERSION}
