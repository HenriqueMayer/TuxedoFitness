"""Validation and audited submission of user-supplied routine JSON."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from django.utils.translation import gettext as _

from training.models import ExerciseTemplate, RoutineFolder


class RoutineValidationError(ValueError):
    pass


SET_TYPES = {'warmup', 'normal', 'failure', 'dropset'}
SET_FIELDS = {
    'type', 'weight_kg', 'reps', 'distance_meters', 'duration_seconds',
    'custom_metric', 'rep_range',
}
METRIC_FIELDS = SET_FIELDS - {'type', 'rep_range'}
COMPATIBLE_FIELDS = {
    ExerciseTemplate.ExerciseType.WEIGHT_REPS: {'weight_kg', 'reps', 'rep_range'},
    ExerciseTemplate.ExerciseType.REPS_ONLY: {'reps', 'rep_range'},
    ExerciseTemplate.ExerciseType.BODYWEIGHT_REPS: {'reps', 'rep_range'},
    ExerciseTemplate.ExerciseType.BODYWEIGHT_ASSISTED_REPS: {
        'weight_kg', 'reps', 'rep_range',
    },
    ExerciseTemplate.ExerciseType.DURATION: {'duration_seconds'},
    ExerciseTemplate.ExerciseType.WEIGHT_DURATION: {'weight_kg', 'duration_seconds'},
    ExerciseTemplate.ExerciseType.DISTANCE_DURATION: {
        'distance_meters', 'duration_seconds',
    },
    ExerciseTemplate.ExerciseType.SHORT_DISTANCE_WEIGHT: {
        'distance_meters', 'weight_kg',
    },
    ExerciseTemplate.ExerciseType.CUSTOM: {'custom_metric'},
}


def _object(value, label):
    if not isinstance(value, dict):
        raise RoutineValidationError(f'{label}: ' + _('Expected a JSON object.'))
    return value


def _reject_unknown(value, allowed, label):
    unknown = set(value) - allowed
    if unknown:
        raise RoutineValidationError(
            f'{label}: ' + _('Unknown fields: ') + ', '.join(sorted(unknown))
        )


def _text(value, label, *, required=False, maximum=2_000):
    if value is None and not required:
        return None
    if not isinstance(value, str) or (required and not value.strip()):
        raise RoutineValidationError(f'{label}: ' + _('Expected valid text.'))
    if len(value) > maximum:
        raise RoutineValidationError(f'{label}: ' + _('Maximum characters: %(count)s.') % {'count': maximum})
    return value.strip()


def _number(value, label, *, integer=False):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise RoutineValidationError(f'{label}: ' + _('Expected a number.'))
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise RoutineValidationError(f'{label}: ' + _('Expected a number.')) from None
    if not parsed.is_finite() or parsed < 0 or (integer and parsed != parsed.to_integral_value()):
        kind = _('nonnegative integer') if integer else _('nonnegative number')
        raise RoutineValidationError(f'{label}: {kind}.')
    if parsed > Decimal('1000000000'):
        raise RoutineValidationError(f'{label}: value exceeds 1000000000.')
    return int(parsed) if integer else float(parsed)


class RoutinePayloadValidator:
    def __init__(self, account):
        self.account = account
        self.templates = {
            item.external_id: item
            for item in ExerciseTemplate.objects.filter(hevy_account=account)
        }
        self.folder_ids = set(
            RoutineFolder.objects.filter(hevy_account=account).values_list(
                'external_id', flat=True
            )
        )

    def validate(self, payload):
        root = _object(payload, 'payload')
        _reject_unknown(root, {'routine'}, 'payload')
        if set(root) != {'routine'}:
            raise RoutineValidationError(_('The payload must contain only routine.'))
        routine = _object(root['routine'], 'routine')
        _reject_unknown(routine, {'title', 'folder_id', 'notes', 'exercises'}, 'routine')
        title = _text(routine.get('title'), 'routine.title', required=True, maximum=255)
        notes = _text(routine.get('notes'), 'routine.notes')
        folder_id = routine.get('folder_id')
        if folder_id is not None:
            folder_id = _number(folder_id, 'routine.folder_id', integer=True)
            if folder_id not in self.folder_ids:
                raise RoutineValidationError('routine.folder_id: ' + _('Unknown local catalogue ID.'))
        exercises = routine.get('exercises')
        if not isinstance(exercises, list) or not 1 <= len(exercises) <= 50:
            raise RoutineValidationError('routine.exercises: ' + _('Expected between 1 and 50 items.'))
        cleaned_exercises = [
            self._exercise(item, index) for index, item in enumerate(exercises)
        ]
        return {
            'routine': {
                'title': title,
                'folder_id': folder_id,
                'notes': notes or '',
                'exercises': cleaned_exercises,
            }
        }

    def _exercise(self, value, index):
        label = f'routine.exercises[{index}]'
        exercise = _object(value, label)
        allowed = {
            'exercise_template_id', 'superset_id', 'rest_seconds', 'notes', 'sets',
        }
        _reject_unknown(exercise, allowed, label)
        template_id = _text(
            exercise.get('exercise_template_id'),
            f'{label}.exercise_template_id', required=True, maximum=255,
        )
        template = self.templates.get(template_id)
        if template is None:
            raise RoutineValidationError(
                f'{label}.exercise_template_id: ' + _('Unknown local catalogue ID.')
            )
        superset_id = _number(
            exercise.get('superset_id'), f'{label}.superset_id', integer=True
        )
        rest_seconds = _number(
            exercise.get('rest_seconds'), f'{label}.rest_seconds', integer=True
        )
        notes = _text(exercise.get('notes'), f'{label}.notes')
        sets = exercise.get('sets')
        if not isinstance(sets, list) or not 1 <= len(sets) <= 20:
            raise RoutineValidationError(f'{label}.sets: ' + _('Expected between 1 and 20 items.'))
        return {
            'exercise_template_id': template_id,
            'superset_id': superset_id,
            'rest_seconds': rest_seconds,
            'notes': notes,
            'sets': [
                self._set(item, template, f'{label}.sets[{set_index}]')
                for set_index, item in enumerate(sets)
            ],
        }

    def _set(self, value, template, label):
        training_set = _object(value, label)
        _reject_unknown(training_set, SET_FIELDS, label)
        set_type = training_set.get('type')
        if not isinstance(set_type, str) or set_type not in SET_TYPES:
            raise RoutineValidationError(f'{label}.type: ' + _('Unsupported set type.'))
        cleaned = {'type': set_type}
        integer_fields = {'reps', 'distance_meters', 'duration_seconds'}
        populated = set()
        for field in METRIC_FIELDS:
            parsed = _number(
                training_set.get(field), f'{label}.{field}',
                integer=field in integer_fields,
            )
            cleaned[field] = parsed
            if parsed is not None:
                populated.add(field)
        rep_range = training_set.get('rep_range')
        if rep_range is not None:
            rep_range = _object(rep_range, f'{label}.rep_range')
            _reject_unknown(rep_range, {'start', 'end'}, f'{label}.rep_range')
            start = _number(rep_range.get('start'), f'{label}.rep_range.start', integer=True)
            end = _number(rep_range.get('end'), f'{label}.rep_range.end', integer=True)
            if start is None or end is None or start < 1 or end < start:
                raise RoutineValidationError(
                    f'{label}.rep_range: ' + _('Use a positive start and an end greater than or equal to start.')
                )
            cleaned['rep_range'] = {'start': start, 'end': end}
            populated.add('rep_range')
        compatible = COMPATIBLE_FIELDS.get(template.exercise_type, {'custom_metric'})
        incompatible = populated - compatible
        if incompatible:
            raise RoutineValidationError(
                f'{label}: ' + _('Incompatible metric: ') + ', '.join(sorted(incompatible))
            )
        if not populated:
            raise RoutineValidationError(f'{label}: ' + _('A measurable prescription is required.'))
        return cleaned

    def preview(self, payload):
        routine = payload['routine']
        exercises = []
        for item in routine['exercises']:
            template = self.templates[item['exercise_template_id']]
            exercises.append({
                'title': template.title,
                'set_count': len(item['sets']),
                'rest_seconds': item['rest_seconds'],
                'notes': item['notes'],
            })
        return {
            'title': routine['title'],
            'notes': routine['notes'],
            'exercise_count': len(exercises),
            'set_count': sum(item['set_count'] for item in exercises),
            'exercises': exercises,
        }
