from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from django.utils import timezone
from django.utils.dateparse import parse_datetime


class PayloadError(ValueError):
    pass


def payload_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(encoded.encode()).hexdigest()


def alias_payload(payload, primary, legacy):
    if primary in payload and legacy in payload and payload[primary] != payload[legacy]:
        raise PayloadError(f'Conflicting {primary} aliases.')
    return {**payload, primary: payload.get(primary, payload.get(legacy))}


def required_string(payload: dict[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise PayloadError(f'{field} must be a non-empty string.')
    return value.strip()


def nullable_string(payload: dict[str, Any], field: str) -> str:
    value = payload.get(field)
    if value is None:
        return ''
    if not isinstance(value, str):
        raise PayloadError(f'{field} must be a string or null.')
    return value


def nullable_datetime(payload: dict[str, Any], field: str) -> datetime | None:
    value = payload.get(field)
    if value is None:
        return None
    if not isinstance(value, str):
        raise PayloadError(f'{field} must be an ISO 8601 timestamp or null.')
    parsed = parse_datetime(value.replace('Z', '+00:00'))
    if parsed is None:
        raise PayloadError(f'{field} must be an ISO 8601 timestamp.')
    if timezone.is_naive(parsed):
        raise PayloadError(f'{field} must include a timezone.')
    return parsed.astimezone(UTC)


def nullable_decimal(payload: dict[str, Any], field: str) -> Decimal | None:
    value = payload.get(field)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise PayloadError(f'{field} must be numeric or null.')
    try:
        decimal = Decimal(str(value))
    except InvalidOperation as error:
        raise PayloadError(f'{field} must be numeric or null.') from error
    if not decimal.is_finite() or decimal < 0:
        raise PayloadError(f'{field} must not be negative.')
    return decimal


def nullable_integer(payload: dict[str, Any], field: str) -> int | None:
    value = payload.get(field)
    if value is None:
        return None
    if isinstance(value, bool):
        raise PayloadError(f'{field} must be an integer or null.')
    try:
        number = int(value)
    except (TypeError, ValueError) as error:
        raise PayloadError(f'{field} must be an integer or null.') from error
    if number < 0 or number != value and not isinstance(value, str):
        raise PayloadError(f'{field} must be a non-negative integer.')
    return number


def required_integer(payload: dict[str, Any], field: str) -> int:
    value = nullable_integer(payload, field)
    if value is None:
        raise PayloadError(f'{field} is required.')
    return value


def required_list(payload: dict[str, Any], field: str) -> list[dict[str, Any]]:
    value = payload.get(field)
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise PayloadError(f'{field} must be a list of objects.')
    return value


@dataclass(frozen=True)
class AccountDTO:
    external_id: str
    display_name: str
    profile_url: str

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> AccountDTO:
        data = payload.get('data', payload)
        if not isinstance(data, dict):
            raise PayloadError('user response must contain an object.')
        return cls(
            external_id=required_string(data, 'id'),
            display_name=required_string(data, 'name'),
            profile_url=nullable_string(data, 'url'),
        )


@dataclass(frozen=True)
class SetDTO:
    position: int
    set_type: str
    weight_kg: Decimal | None
    reps: Decimal | None
    distance_meters: Decimal | None
    duration_seconds: Decimal | None
    custom_metric: Decimal | None
    rep_range_start: int | None = None
    rep_range_end: int | None = None
    rpe: Decimal | None = None


def set_dto(payload: dict[str, Any], *, routine: bool) -> SetDTO:
    rep_range = payload.get('rep_range')
    if rep_range is not None and not isinstance(rep_range, dict):
        raise PayloadError('rep_range must be an object or null.')
    range_start = nullable_integer(rep_range or {}, 'start')
    range_end = nullable_integer(rep_range or {}, 'end')
    if range_start is not None and range_end is not None and range_start > range_end:
        raise PayloadError('rep_range start must not exceed end.')
    rpe = nullable_decimal(payload, 'rpe') if not routine else None
    if rpe is not None and rpe not in {
        Decimal('6'), Decimal('7'), Decimal('7.5'), Decimal('8'), Decimal('8.5'),
        Decimal('9'), Decimal('9.5'), Decimal('10'),
    }:
        raise PayloadError('rpe is not an approved value.')
    set_type = required_string(payload, 'type')
    if set_type not in {'warmup', 'normal', 'failure', 'dropset'}:
        raise PayloadError('set type is not approved.')
    return SetDTO(
        position=required_integer(payload, 'index'),
        set_type=set_type,
        weight_kg=nullable_decimal(payload, 'weight_kg'),
        reps=nullable_decimal(payload, 'reps'),
        distance_meters=nullable_decimal(payload, 'distance_meters'),
        duration_seconds=nullable_decimal(payload, 'duration_seconds'),
        custom_metric=nullable_decimal(payload, 'custom_metric'),
        rep_range_start=range_start,
        rep_range_end=range_end,
        rpe=rpe,
    )


@dataclass(frozen=True)
class ExerciseDTO:
    position: int
    template_id: str
    title: str
    notes: str
    superset_group: int | None
    rest_seconds: int | None
    sets: tuple[SetDTO, ...]


def exercise_dto(payload: dict[str, Any], *, routine: bool) -> ExerciseDTO:
    rest = nullable_integer(payload, 'rest_seconds') if routine else None
    return ExerciseDTO(
        position=required_integer(payload, 'index'),
        template_id=required_string(payload, 'exercise_template_id'),
        title=required_string(payload, 'title'),
        notes=nullable_string(payload, 'notes'),
        superset_group=nullable_integer(alias_payload(payload, 'superset_id', 'supersets_id'), 'superset_id'),
        rest_seconds=rest,
        sets=tuple(set_dto(item, routine=routine) for item in required_list(payload, 'sets')),
    )


@dataclass(frozen=True)
class ExerciseTemplateDTO:
    external_id: str
    title: str
    exercise_type: str
    equipment_category: str
    primary_muscle: str
    secondary_muscles: tuple[str, ...]
    is_custom: bool
    created_at: datetime | None
    updated_at: datetime | None
    source_hash: str
    raw_payload: dict = field(default_factory=dict, compare=False)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> ExerciseTemplateDTO:
        secondaries = payload.get('secondary_muscle_groups') or []
        if not isinstance(secondaries, list) or not all(isinstance(item, str) for item in secondaries):
            raise PayloadError('secondary_muscle_groups must be a list of strings.')
        custom = payload.get('is_custom', False)
        if not isinstance(custom, bool):
            raise PayloadError('is_custom must be a boolean.')
        return cls(
            external_id=required_string(payload, 'id'), title=required_string(payload, 'title'),
            exercise_type=required_string(payload, 'type'),
            equipment_category=nullable_string(alias_payload(payload, 'equipment', 'equipment_category'), 'equipment'),
            primary_muscle=nullable_string(payload, 'primary_muscle_group'),
            secondary_muscles=tuple(sorted(set(secondaries))), is_custom=custom,
            created_at=nullable_datetime(payload, 'created_at'),
            updated_at=nullable_datetime(payload, 'updated_at'), source_hash=payload_hash(payload), raw_payload=payload,
        )


@dataclass(frozen=True)
class RoutineFolderDTO:
    external_id: int
    position: int
    title: str
    created_at: datetime | None
    updated_at: datetime | None
    source_hash: str
    raw_payload: dict = field(default_factory=dict, compare=False)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> RoutineFolderDTO:
        return cls(required_integer(payload, 'id'), required_integer(payload, 'index'),
                   required_string(payload, 'title'), nullable_datetime(payload, 'created_at'),
                   nullable_datetime(payload, 'updated_at'), payload_hash(payload), payload)


@dataclass(frozen=True)
class RoutineDTO:
    external_id: str
    folder_id: int | None
    title: str
    exercises: tuple[ExerciseDTO, ...]
    created_at: datetime | None
    updated_at: datetime | None
    source_hash: str
    raw_payload: dict = field(default_factory=dict, compare=False)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> RoutineDTO:
        return cls(required_string(payload, 'id'), nullable_integer(payload, 'folder_id'),
                   required_string(payload, 'title'),
                   tuple(exercise_dto(item, routine=True) for item in required_list(payload, 'exercises')),
                   nullable_datetime(payload, 'created_at'), nullable_datetime(payload, 'updated_at'),
                   payload_hash(payload), payload)


@dataclass(frozen=True)
class WorkoutDTO:
    external_id: str
    routine_id: str | None
    title: str
    description: str
    start_time: datetime
    end_time: datetime
    exercises: tuple[ExerciseDTO, ...]
    created_at: datetime | None
    updated_at: datetime | None
    source_hash: str
    raw_payload: dict = field(default_factory=dict, compare=False)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> WorkoutDTO:
        start = nullable_datetime(payload, 'start_time')
        end = nullable_datetime(payload, 'end_time')
        if start is None or end is None:
            raise PayloadError('workout times are required.')
        if end < start:
            raise PayloadError('workout end_time must not precede start_time.')
        return cls(required_string(payload, 'id'), nullable_string(payload, 'routine_id') or None,
                   required_string(payload, 'title'), nullable_string(payload, 'description'), start, end,
                   tuple(exercise_dto(item, routine=False) for item in required_list(payload, 'exercises')),
                   nullable_datetime(payload, 'created_at'), nullable_datetime(payload, 'updated_at'),
                   payload_hash(payload), payload)


@dataclass(frozen=True)
class WorkoutEventDTO:
    event_type: str
    external_id: str
    occurred_at: datetime
    workout: WorkoutDTO | None
    needs_repair: bool

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> WorkoutEventDTO:
        event_type = required_string(payload, 'type')
        if event_type == 'deleted':
            deleted_at = nullable_datetime(payload, 'deleted_at')
            if deleted_at is None:
                raise PayloadError('deleted_at is required for a deleted workout event.')
            return cls(event_type, required_string(payload, 'id'), deleted_at, None, False)
        if event_type != 'updated':
            raise PayloadError('workout event type is not approved.')
        workout_payload = payload.get('workout')
        if not isinstance(workout_payload, dict):
            raise PayloadError('updated workout event must contain a workout object.')
        external_id = required_string(workout_payload, 'id')
        occurred_at = nullable_datetime(workout_payload, 'updated_at')
        if occurred_at is None:
            raise PayloadError('updated_at is required for an updated workout event.')
        try:
            workout = WorkoutDTO.from_payload(workout_payload)
        except PayloadError:
            workout = None
        return cls(event_type, external_id, occurred_at, workout, workout is None)
