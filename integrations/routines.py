"""Validation and audited submission of user-supplied routine JSON."""

from __future__ import annotations

import hashlib
import json
from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils import timezone

from integrations.hevy import HevyClient, HevyError
from integrations.models import RoutineWriteIntent, SyncRun
from integrations.services import (
    ADAPTER_VERSION,
    PROVIDER_SCHEMA_VERSION,
    IncrementalSyncService,
)
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
        raise RoutineValidationError(f'{label} deve ser um objeto JSON.')
    return value


def _reject_unknown(value, allowed, label):
    unknown = set(value) - allowed
    if unknown:
        raise RoutineValidationError(
            f'{label} contém campo(s) não permitido(s): {", ".join(sorted(unknown))}.'
        )


def _text(value, label, *, required=False, maximum=2_000):
    if value is None and not required:
        return None
    if not isinstance(value, str) or (required and not value.strip()):
        raise RoutineValidationError(f'{label} deve ser um texto válido.')
    if len(value) > maximum:
        raise RoutineValidationError(f'{label} excede {maximum} caracteres.')
    return value.strip()


def _number(value, label, *, integer=False):
    if value is None:
        return None
    if isinstance(value, bool):
        raise RoutineValidationError(f'{label} deve ser numérico.')
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise RoutineValidationError(f'{label} deve ser numérico.') from None
    if not parsed.is_finite() or parsed < 0 or (integer and parsed != parsed.to_integral_value()):
        kind = 'inteiro não negativo' if integer else 'número não negativo'
        raise RoutineValidationError(f'{label} deve ser um {kind}.')
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
        root = _object(payload, 'O payload')
        _reject_unknown(root, {'routine'}, 'O payload')
        if set(root) != {'routine'}:
            raise RoutineValidationError('O payload deve conter somente a chave routine.')
        routine = _object(root['routine'], 'routine')
        _reject_unknown(routine, {'title', 'folder_id', 'notes', 'exercises'}, 'routine')
        title = _text(routine.get('title'), 'routine.title', required=True, maximum=255)
        notes = _text(routine.get('notes'), 'routine.notes')
        folder_id = routine.get('folder_id')
        if folder_id is not None:
            folder_id = _number(folder_id, 'routine.folder_id', integer=True)
            if folder_id not in self.folder_ids:
                raise RoutineValidationError('routine.folder_id não existe no catálogo local.')
        exercises = routine.get('exercises')
        if not isinstance(exercises, list) or not 1 <= len(exercises) <= 50:
            raise RoutineValidationError('routine.exercises deve conter entre 1 e 50 itens.')
        cleaned_exercises = [
            self._exercise(item, index) for index, item in enumerate(exercises, 1)
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
                f'{label}.exercise_template_id não existe no catálogo local.'
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
            raise RoutineValidationError(f'{label}.sets deve conter entre 1 e 20 itens.')
        return {
            'exercise_template_id': template_id,
            'superset_id': superset_id,
            'rest_seconds': rest_seconds,
            'notes': notes,
            'sets': [
                self._set(item, template, f'{label}.sets[{set_index}]')
                for set_index, item in enumerate(sets, 1)
            ],
        }

    def _set(self, value, template, label):
        training_set = _object(value, label)
        _reject_unknown(training_set, SET_FIELDS, label)
        set_type = training_set.get('type')
        if set_type not in SET_TYPES:
            raise RoutineValidationError(f'{label}.type não é permitido.')
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
                    f'{label}.rep_range deve ter início positivo e fim igual ou maior.'
                )
            cleaned['rep_range'] = {'start': start, 'end': end}
            populated.add('rep_range')
        compatible = COMPATIBLE_FIELDS.get(template.exercise_type, {'custom_metric'})
        incompatible = populated - compatible
        if incompatible:
            raise RoutineValidationError(
                f'{label} usa métrica incompatível com {template.title}: '
                f'{", ".join(sorted(incompatible))}.'
            )
        if not populated:
            raise RoutineValidationError(f'{label} precisa de uma prescrição mensurável.')
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


class RoutineWriteService:
    INTENT_LIFETIME = timedelta(minutes=30)

    def create_intent(self, account, payload):
        canonical = json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'),
        )
        return RoutineWriteIntent.objects.create(
            hevy_account=account,
            payload=payload,
            payload_hash=hashlib.sha256(canonical.encode()).hexdigest(),
            expires_at=timezone.now() + self.INTENT_LIFETIME,
        )

    def submit(self, account, intent_id, client: HevyClient):
        now = timezone.now()
        IncrementalSyncService._acquire_lock(account)
        try:
            with transaction.atomic():
                intent = RoutineWriteIntent.objects.select_for_update().get(
                    pk=intent_id, hevy_account=account
                )
                if intent.state != RoutineWriteIntent.State.PREVIEWED:
                    raise RoutineValidationError('Esta confirmação já foi consumida.')
                expired = intent.expires_at <= now
                if expired:
                    intent.state = RoutineWriteIntent.State.EXPIRED
                    intent.finished_at = now
                    intent.save(update_fields=['state', 'finished_at'])
                else:
                    intent.state = RoutineWriteIntent.State.SUBMITTING
                    intent.submitted_at = now
                    intent.save(update_fields=['state', 'submitted_at'])
            if expired:
                raise RoutineValidationError(
                    'A prévia expirou. Valide o JSON novamente.'
                )

            run = SyncRun.objects.create(
                hevy_account=account,
                mode=SyncRun.Mode.ROUTINE_CREATE,
                trigger=SyncRun.Trigger.WEB,
                state=SyncRun.State.RUNNING,
                started_at=now,
                adapter_version=ADAPTER_VERSION,
                provider_schema_version=PROVIDER_SCHEMA_VERSION,
            )
            try:
                routine = client.create_routine(intent.payload)
            except HevyError as error:
                finished = timezone.now()
                intent_state = (
                    RoutineWriteIntent.State.UNKNOWN
                    if error.code == 'WRITE_UNKNOWN'
                    else RoutineWriteIntent.State.FAILED
                )
                RoutineWriteIntent.objects.filter(pk=intent.pk).update(
                    state=intent_state,
                    finished_at=finished,
                    error_code=error.code,
                    sanitized_error=str(error)[:500],
                )
                SyncRun.objects.filter(pk=run.pk).update(
                    state=(
                        SyncRun.State.PARTIAL
                        if error.code == 'WRITE_UNKNOWN'
                        else SyncRun.State.FAILED
                    ),
                    finished_at=finished,
                    duration_ms=int((finished - now).total_seconds() * 1000),
                    error_code=error.code,
                    sanitized_error=str(error)[:500],
                )
                raise
            else:
                finished = timezone.now()
                RoutineWriteIntent.objects.filter(pk=intent.pk).update(
                    state=RoutineWriteIntent.State.SUCCEEDED,
                    finished_at=finished,
                    external_routine_id=routine.external_id,
                )
                SyncRun.objects.filter(pk=run.pk).update(
                    state=SyncRun.State.SUCCEEDED,
                    finished_at=finished,
                    duration_ms=int((finished - now).total_seconds() * 1000),
                    item_counts={'routines_created': 1},
                )
                return routine
        finally:
            IncrementalSyncService._release_lock(account)
