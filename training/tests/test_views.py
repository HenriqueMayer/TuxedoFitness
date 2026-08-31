import csv
from datetime import datetime
from datetime import timezone as dt_timezone
from io import StringIO

from django.test import TestCase
from django.urls import reverse

from accounts.models import OwnerPreference
from training.models import SetType, WorkoutExercise, WorkoutSet
from training.tests.factories import (
    create_account,
    create_routine,
    create_template,
    create_workout,
)


class TrainingReadViewTests(TestCase):
    def setUp(self):
        self.account = create_account('training-view-owner')
        self.template = create_template(self.account)
        self.client.force_login(self.account.user)

    def test_history_filter_is_reproducible_through_get(self):
        included = create_workout(
            self.account, self.template,
            title='Normal session',
            start_time=datetime(2026, 1, 2, 12, tzinfo=dt_timezone.utc),
            end_time=datetime(2026, 1, 2, 13, tzinfo=dt_timezone.utc),
        )
        excluded = create_workout(
            self.account, self.template,
            title='Warmup session',
            start_time=datetime(2026, 1, 3, 12, tzinfo=dt_timezone.utc),
            end_time=datetime(2026, 1, 3, 13, tzinfo=dt_timezone.utc),
        )
        warmup = excluded.exercises.get().sets.get()
        warmup.set_type = SetType.WARMUP
        warmup.save()

        response = self.client.get(reverse('training:history'), {
            'inicio': '2026-01-01', 'fim': '2026-01-03', 'tipo': 'normal',
        })

        self.assertContains(response, included.title)
        self.assertNotContains(response, excluded.title)
        self.assertContains(response, 'value="2026-01-01"')
        self.assertContains(response, 'value="2026-01-03"')

    def test_history_paginates_twenty_five_workouts(self):
        for index in range(26):
            create_workout(self.account, self.template, title=f'Workout {index:02d}')

        first = self.client.get(reverse('training:history'))
        second = self.client.get(reverse('training:history'), {'page': 2})

        self.assertEqual(len(first.context['page_obj']), 25)
        self.assertEqual(len(second.context['page_obj']), 1)

    def test_workout_detail_preserves_source_order(self):
        workout = create_workout(
            self.account, self.template,
            start_time=datetime(2026, 1, 2, 12, tzinfo=dt_timezone.utc),
            end_time=datetime(2026, 1, 2, 13, tzinfo=dt_timezone.utc),
        )
        second_template = create_template(self.account, external_id='second', title='Second exercise')
        second = WorkoutExercise.objects.create(
            workout=workout, position=1, exercise_template=second_template,
            title_snapshot='Second exercise',
        )
        WorkoutSet.objects.create(workout_exercise=second, position=0, set_type=SetType.NORMAL, reps=5)

        response = self.client.get(reverse('training:workout-detail', args=[workout.pk]))

        self.assertContains(response, 'Synthetic Press')
        self.assertContains(response, 'Second exercise')
        self.assertLess(response.content.index(b'Synthetic Press'), response.content.index(b'Second exercise'))

    def test_exercise_search_and_incompatible_detail(self):
        duration = create_template(self.account, external_id='duration', title='Tempo bike', exercise_type='duration')

        response = self.client.get(reverse('training:exercises'), {'q': 'Tempo'})
        self.assertContains(response, duration.title)
        self.assertNotContains(response, self.template.title)

        response = self.client.get(reverse('training:exercise-detail', args=[duration.pk]))
        self.assertContains(response, 'Métricas de carga não compatíveis')
        self.assertNotContains(response, '1RM estimado')

    def test_exercise_catalog_paginates_fifty_templates(self):
        for index in range(50):
            create_template(
                self.account,
                external_id=f'catalog-{index:02d}',
                title=f'Catalog exercise {index:02d}',
            )

        first = self.client.get(reverse('training:exercises'))
        second = self.client.get(reverse('training:exercises'), {'page': 2})

        self.assertEqual(len(first.context['page_obj']), 50)
        self.assertEqual(len(second.context['page_obj']), 1)
        self.assertContains(first, 'Próxima')

    def test_workout_detail_uses_owner_mass_unit(self):
        OwnerPreference.objects.create(user=self.account.user, mass_unit='lb')
        workout = create_workout(self.account, self.template)

        response = self.client.get(
            reverse('training:workout-detail', args=[workout.pk])
        )

        self.assertContains(response, '93,7 lb')

    def test_routines_show_planned_sets_and_no_write_controls(self):
        routine = create_routine(self.account, self.template)

        response = self.client.get(reverse('training:routines'))

        self.assertContains(response, routine.title)
        self.assertContains(response, 'Rotina é planejamento. Treino concluído é execução.')
        self.assertNotContains(response, 'Excluir')

        detail = self.client.get(reverse('training:routine-detail', args=[routine.pk]))
        self.assertContains(detail, '40,000')
        self.assertContains(detail, '90 s')
        self.assertNotContains(detail, 'Salvar')

    def test_csv_export_respects_type_filter_and_preserves_nulls(self):
        normal = create_workout(self.account, self.template, title='Normal export')
        warmup = create_workout(self.account, self.template, title='Warmup export')
        normal_set = normal.exercises.get().sets.get()
        normal_set.weight_kg = None
        normal_set.save()
        warmup_set = warmup.exercises.get().sets.get()
        warmup_set.set_type = SetType.WARMUP
        warmup_set.save()

        response = self.client.get(reverse('training:workout-export'), {'tipo': 'warmup'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')
        rows = list(csv.DictReader(StringIO(response.content.decode())))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['treino_titulo'], 'Warmup export')
        self.assertEqual(rows[0]['peso_kg'], '42.500')

        all_rows = list(csv.DictReader(StringIO(
            self.client.get(reverse('training:workout-export')).content.decode()
        )))
        normal_row = next(row for row in all_rows if row['treino_titulo'] == 'Normal export')
        self.assertEqual(normal_row['peso_kg'], '')

        removed = create_workout(self.account, self.template, title='Removed export')
        removed.is_active = False
        removed.removed_at = datetime(2026, 1, 4, 12, tzinfo=dt_timezone.utc)
        removed.save(update_fields=['is_active', 'removed_at'])
        removed_rows = list(csv.DictReader(StringIO(
            self.client.get(reverse('training:workout-export')).content.decode()
        )))
        removed_row = next(row for row in removed_rows if row['treino_titulo'] == 'Removed export')
        self.assertEqual(removed_row['estado'], 'removido')
        self.assertTrue(removed_row['removido_em'].startswith('2026-01-04T12:00:00'))
