"""On-demand exports built from confirmed local integration data."""

from __future__ import annotations

import csv
import json

from django.http import HttpResponse
from django.utils import timezone

from integrations.models import ProviderSnapshot
from training.models import ExerciseTemplate, Routine, Workout


def _filename(stem, extension):
    return f'{stem}-{timezone.localdate():%Y%m%d}.{extension}'


def _download(content, *, content_type, filename):
    response = HttpResponse(content, content_type=content_type)
    response['Cache-Control'] = 'private, no-store'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def exercise_catalog_data(account):
    return [
        {
            'id': item.external_id,
            'title': item.title,
            'type': item.exercise_type,
            'equipment_category': item.equipment_category,
            'primary_muscle_group': item.primary_muscle,
            'secondary_muscle_groups': [
                muscle.muscle_code for muscle in item.secondary_muscles.all()
            ],
            'is_custom': item.is_custom,
        }
        for item in ExerciseTemplate.objects.filter(
            hevy_account=account
        ).prefetch_related('secondary_muscles')
    ]


def exercise_catalog_json(account):
    body = json.dumps(
        {'exercise_templates': exercise_catalog_data(account)},
        ensure_ascii=False,
        indent=2,
    )
    return _download(
        body,
        content_type='application/json; charset=utf-8',
        filename=_filename('exercise-catalog', 'json'),
    )


def exercise_catalog_csv(account):
    response = _download(
        '', content_type='text/csv; charset=utf-8',
        filename=_filename('exercise-catalog', 'csv'),
    )
    writer = csv.writer(response, lineterminator='\n')
    writer.writerow([
        'id', 'title', 'type', 'equipment_category', 'primary_muscle_group',
        'secondary_muscle_groups', 'is_custom',
    ])
    for item in exercise_catalog_data(account):
        writer.writerow([
            item['id'], item['title'], item['type'], item['equipment_category'],
            item['primary_muscle_group'], '|'.join(item['secondary_muscle_groups']),
            str(item['is_custom']).lower(),
        ])
    return response


def routines_json(account):
    snapshot = ProviderSnapshot.objects.filter(hevy_account=account, resource='routines').first()
    body = json.dumps({'pages': snapshot.pages if snapshot else []}, ensure_ascii=False, indent=2)
    return _download(
        body,
        content_type='application/json; charset=utf-8',
        filename=_filename('routines', 'json'),
    )


def routines_csv(account):
    response = _download(
        '', content_type='text/csv; charset=utf-8',
        filename=_filename('routines', 'csv'),
    )
    writer = csv.writer(response, lineterminator='\n')
    writer.writerow([
        'routine_id', 'routine_title', 'folder_id', 'folder_title',
        'exercise_position', 'exercise_template_id', 'exercise_title',
        'rest_seconds', 'superset_id', 'set_position', 'set_type', 'weight_kg',
        'reps', 'distance_meters', 'duration_seconds', 'custom_metric',
        'rep_range_start', 'rep_range_end',
    ])
    for routine in Routine.objects.filter(hevy_account=account).select_related(
        'folder'
    ).prefetch_related('exercises__exercise_template', 'exercises__sets'):
        for exercise in routine.exercises.all():
            for item in exercise.sets.all():
                writer.writerow([
                    routine.external_id,
                    routine.title,
                    routine.folder.external_id if routine.folder else '',
                    routine.folder.title if routine.folder else '',
                    exercise.position,
                    exercise.exercise_template.external_id,
                    exercise.title_snapshot,
                    exercise.rest_seconds if exercise.rest_seconds is not None else '',
                    exercise.superset_group if exercise.superset_group is not None else '',
                    item.position,
                    item.set_type,
                    item.weight_kg if item.weight_kg is not None else '',
                    item.reps if item.reps is not None else '',
                    item.distance_meters if item.distance_meters is not None else '',
                    item.duration_seconds if item.duration_seconds is not None else '',
                    item.custom_metric if item.custom_metric is not None else '',
                    item.rep_range_start if item.rep_range_start is not None else '',
                    item.rep_range_end if item.rep_range_end is not None else '',
                ])
    return response


def workouts_json(account):
    body = json.dumps({'workouts': list(Workout.objects.filter(hevy_account=account).values_list('raw_payload', flat=True))}, ensure_ascii=False, indent=2)
    return _download(body, content_type='application/json; charset=utf-8', filename=_filename('workouts', 'json'))
