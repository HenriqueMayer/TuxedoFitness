"""Build offline prompts from confirmed local training data."""

from __future__ import annotations

import json
from calendar import monthrange
from datetime import datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.utils import timezone

from integrations.exports import exercise_catalog_data, routine_data
from training.models import Workout


def _months_ago(value, count):
    absolute = value.year * 12 + value.month - 1 - count
    year, month_zero = divmod(absolute, 12)
    month = month_zero + 1
    return value.replace(year=year, month=month, day=min(value.day, monthrange(year, month)[1]))


def _json_value(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime,)):
        return value.isoformat()
    raise TypeError


def _serialize_workouts(workouts, zone):
    result = []
    for workout in workouts:
        exercises = []
        for exercise in workout.exercises.all():
            exercises.append({
                'exercise_template_id': exercise.exercise_template.external_id,
                'title': exercise.title_snapshot,
                'sets': [
                    {
                        'type': item.set_type,
                        'weight_kg': item.weight_kg,
                        'reps': item.reps,
                        'distance_meters': item.distance_meters,
                        'duration_seconds': item.duration_seconds,
                        'rpe': item.rpe,
                        'custom_metric': item.custom_metric,
                    }
                    for item in exercise.sets.all()
                ],
            })
        result.append({
            'id': workout.external_id,
            'title': workout.title,
            'start_time_local': timezone.localtime(workout.start_time, zone).isoformat(),
            'end_time_local': timezone.localtime(workout.end_time, zone).isoformat(),
            'routine_id': workout.routine.external_id if workout.routine else None,
            'exercises': exercises,
        })
    return result


class PromptTemplateService:
    def __init__(self, account):
        self.account = account
        preference = getattr(account.user, 'fitness_preferences', None)
        self.timezone_name = getattr(
            preference, 'presentation_timezone', 'America/Sao_Paulo'
        )
        self.zone = ZoneInfo(self.timezone_name)

    def _workouts(self, mode, value):
        queryset = Workout.objects.filter(
            hevy_account=self.account
        ).select_related('routine').prefetch_related(
            'exercises__exercise_template', 'exercises__sets'
        )
        if mode == 'workouts':
            return list(queryset.order_by('-start_time', '-external_id')[:value])
        today = timezone.localtime(timezone.now(), self.zone).date()
        if mode == 'last_7_days':
            start = today - timedelta(days=6)
        elif mode == 'weeks':
            start = today - timedelta(days=7 * value - 1)
        elif mode == 'months':
            start = _months_ago(today, value)
        else:
            raise ValueError('Unknown prompt period mode.')
        start_at = timezone.make_aware(datetime.combine(start, time.min), self.zone)
        end_at = timezone.make_aware(
            datetime.combine(today + timedelta(days=1), time.min), self.zone
        )
        return list(queryset.filter(start_time__gte=start_at, start_time__lt=end_at))

    def build(self, cleaned_data):
        workouts = self._workouts(
            cleaned_data['period_mode'], cleaned_data['period_value']
        )
        context = {
            'objective': cleaned_data['objective'],
            'desired_frequency_per_week': cleaned_data['desired_frequency'],
            'desired_session_duration_minutes': cleaned_data['session_duration_minutes'],
            'available_equipment': cleaned_data['available_equipment'],
            'limitations': cleaned_data['limitations'],
            'observations': cleaned_data['observations'],
            'presentation_timezone': self.timezone_name,
            'history_selection': {
                'mode': cleaned_data['period_mode'],
                'value': cleaned_data['period_value'],
                'returned_workouts': len(workouts),
            },
        }
        routines = routine_data(self.account)
        catalog = exercise_catalog_data(self.account)
        history = _serialize_workouts(workouts, self.zone)
        payload_example = {
            'routine': {
                'title': 'Nome da rotina',
                'folder_id': None,
                'notes': 'Orientações gerais',
                'exercises': [{
                    'exercise_template_id': 'ID_DO_CATALOGO',
                    'superset_id': None,
                    'rest_seconds': 90,
                    'notes': None,
                    'sets': [{
                        'type': 'normal',
                        'weight_kg': None,
                        'reps': None,
                        'distance_meters': None,
                        'duration_seconds': None,
                        'custom_metric': None,
                        'rep_range': {'start': 8, 'end': 12},
                    }],
                }],
            }
        }
        return '\n'.join([
            '# Análise externa de treino — Tuxedo Fitness',
            '',
            'Analise os dados fornecidos de forma observacional e fundamentada. '
            'Não faça diagnóstico, tratamento ou promessa clínica. Diferencie rotina '
            'planejada de treino executado e preserve valores ausentes como ausentes.',
            '',
            '## Objetivo da análise',
            '',
            '1. Avalie frequência, distribuição, progressão, esforço e recuperação '
            'somente quando os dados sustentarem a conclusão.',
            '2. Identifique limitações dos dados e explique cada recomendação.',
            '3. Proponha uma rotina compatível com objetivo, tempo, equipamento e limitações.',
            '4. Use exclusivamente IDs de exercícios presentes no catálogo fornecido à ferramenta.',
            '5. Ao final, retorne somente JSON válido, sem bloco Markdown, comentários, '
            'comando cURL, API key ou placeholder.',
            '',
            '## Contexto do usuário',
            '',
            '```json',
            json.dumps(context, ensure_ascii=False, indent=2),
            '```',
            '',
            '## Rotinas atuais',
            '',
            '```json',
            json.dumps({'routines': routines}, ensure_ascii=False, indent=2),
            '```',
            '',
            '## Catálogo de exercícios permitido',
            '',
            '```json',
            json.dumps({'exercise_templates': catalog}, ensure_ascii=False, indent=2),
            '```',
            '',
            '## Histórico selecionado',
            '',
            '```json',
            json.dumps({'workouts': history}, ensure_ascii=False, indent=2, default=_json_value),
            '```',
            '',
            '## Formato obrigatório da resposta',
            '',
            '```json',
            json.dumps(payload_example, ensure_ascii=False, indent=2),
            '```',
            '',
            'A resposta deve substituir os valores de exemplo e conter somente o objeto JSON.',
        ])
