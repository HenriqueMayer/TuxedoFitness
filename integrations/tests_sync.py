import json
import os
from datetime import timedelta
from io import StringIO
from types import SimpleNamespace
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import DatabaseError
from django.test import TestCase, override_settings
from django.utils import timezone

from integrations.hevy import HevyClient, HevyError
from integrations.models import SyncCursor, SyncLock, SyncRun
from integrations.services import (
    WORKOUT_EVENT_STREAM,
    FullImportService,
    IncrementalSyncService,
    PlanRefreshService,
)
from training.models import ExerciseTemplate, Routine, RoutineFolder, Workout
from training.tests.factories import create_account


def response(payload, status=200, headers=None):
    return status, headers or {}, json.dumps(payload).encode()


def template(identifier='template-1'):
    return {
        'id': identifier, 'title': 'Synthetic Press', 'type': 'weight_reps',
        'equipment_category': 'barbell', 'primary_muscle_group': 'chest',
        'secondary_muscle_groups': ['triceps'], 'is_custom': False,
    }


def folder(identifier=1):
    return {'id': identifier, 'index': 0, 'title': 'Synthetic Folder'}


def routine(identifier='routine-1'):
    return {
        'id': identifier, 'folder_id': 1, 'title': 'Synthetic Routine',
        'exercises': [{
            'index': 0, 'title': 'Synthetic Press', 'exercise_template_id': 'template-1',
            'rest_seconds': 90, 'supersets_id': None,
            'sets': [{'index': 0, 'type': 'normal', 'weight_kg': 20, 'reps': 8,
                      'distance_meters': None, 'duration_seconds': None,
                      'custom_metric': None, 'rep_range': {'start': 8, 'end': 10}}],
        }],
    }


def workout(identifier='workout-1'):
    return {
        'id': identifier, 'routine_id': 'routine-1', 'title': 'Synthetic Workout',
        'description': None, 'start_time': '2026-08-01T10:00:00Z',
        'end_time': '2026-08-01T11:00:00Z', 'exercises': [{
            'index': 0, 'title': 'Synthetic Press', 'exercise_template_id': 'template-1',
            'notes': None, 'supersets_id': None,
            'sets': [{'index': 0, 'type': 'normal', 'weight_kg': 25, 'reps': 8,
                      'distance_meters': None, 'duration_seconds': None,
                      'custom_metric': None, 'rpe': 8.5}],
        }],
    }


def updated_event(payload=None, timestamp='2026-08-02T12:00:00Z'):
    payload = payload or workout()
    payload['updated_at'] = timestamp
    return {'type': 'updated', 'workout': payload}


def deleted_event(identifier='workout-1', timestamp='2026-08-02T12:00:00Z'):
    return {'type': 'deleted', 'id': identifier, 'deleted_at': timestamp}


class HevyClientTests(TestCase):
    def test_requires_key_and_strict_read_only_host(self):
        with self.assertRaises(HevyError) as missing:
            HevyClient('')
        self.assertEqual(missing.exception.code, 'CONFIG_MISSING_KEY')

        with self.assertRaises(HevyError) as host:
            HevyClient('synthetic-key', 'http://api.hevyapp.com/')
        self.assertEqual(host.exception.code, 'CONFIG_INVALID_HOST')

        client = HevyClient('synthetic-key', transport=lambda *_: response({}))
        with self.assertRaises(HevyError) as endpoint:
            client._get('/v1/routines/unsafe')
        self.assertEqual(endpoint.exception.code, 'HTTP_PERMANENT')

    def test_fetches_each_page_including_last(self):
        calls = []

        def transport(url, headers, timeout):
            calls.append((url, headers, timeout))
            page = 1 if 'page=1' in url else 2
            return response({'page': page, 'page_count': 2, 'workouts': []})

        result = HevyClient('synthetic-key', transport=transport).pages('workouts')
        self.assertEqual(result.received_pages, 2)
        self.assertEqual(len(calls), 2)
        self.assertTrue(all(call[1] == {'api-key': 'synthetic-key', 'Accept': 'application/json'} for call in calls))
        self.assertTrue(all('pageSize=10' in call[0] for call in calls))

    def test_retries_transient_response_without_exposing_body(self):
        statuses = iter([500, 200])
        sleeps = []

        def transport(url, headers, timeout):
            return response({'page': 1, 'page_count': 1, 'workouts': []}, next(statuses))

        client = HevyClient('synthetic-key', transport=transport, sleep=sleeps.append, jitter=lambda: 0)
        client.pages('workouts')
        self.assertEqual(client.retry_count, 1)
        self.assertEqual(sleeps, [1])

    def test_classifies_auth_timeout_and_permanent_failures(self):
        cases = ((401, 'AUTH_INVALID'), (408, 'HTTP_TIMEOUT'), (422, 'HTTP_PERMANENT'))
        for status, code in cases:
            with self.subTest(status=status):
                client = HevyClient(
                    'synthetic-key',
                    transport=lambda *_, status=status: response({'private': 'not exposed'}, status),
                    sleep=lambda _: None,
                    jitter=lambda: 0,
                )
                with self.assertRaises(HevyError) as error:
                    client.user_info()
                self.assertEqual(error.exception.code, code)
                self.assertNotIn('private', str(error.exception))

    def test_rejects_invalid_json_shape_and_oversized_response(self):
        payloads = (b'not-json', b'[]', b'{}' + b' ' * (HevyClient.MAX_RESPONSE_BYTES + 1))
        for body in payloads:
            with self.subTest(length=len(body)):
                client = HevyClient('synthetic-key', transport=lambda *_, body=body: (200, {}, body))
                with self.assertRaises(HevyError) as error:
                    client.user_info()
                self.assertEqual(error.exception.code, 'PAYLOAD_INVALID')

    def test_retry_after_is_bounded_and_invalid_values_fall_back(self):
        for value, expected in (('99', 30), ('-1', 1), ('not-a-number', 1)):
            sleeps = []
            statuses = iter([429, 200])

            def transport(*_):
                status = next(statuses)
                return response(
                    {'data': {'id': 'owner', 'name': 'Synthetic Owner', 'url': None}},
                    status,
                    {'Retry-After': value},
                )

            client = HevyClient('synthetic-key', transport=transport, sleep=sleeps.append, jitter=lambda: 0)
            client.user_info()
            self.assertEqual(sleeps, [expected])

    def test_rejects_invalid_host_and_pagination(self):
        with self.assertRaises(HevyError) as host_error:
            HevyClient('synthetic-key', 'https://example.com/')
        self.assertEqual(host_error.exception.code, 'CONFIG_INVALID_HOST')
        client = HevyClient('synthetic-key', transport=lambda *_: response({'page': 2, 'page_count': 2, 'workouts': []}))
        with self.assertRaises(HevyError) as page_error:
            client.pages('workouts')
        self.assertEqual(page_error.exception.code, 'PAGINATION_INVALID')

    def test_fetches_workout_event_pages_with_since(self):
        calls = []

        def transport(url, headers, timeout):
            calls.append(url)
            page = 1 if 'page=1' in url else 2
            return response({'page': page, 'page_count': 2, 'events': []})

        result = HevyClient('synthetic-key', transport=transport).workout_events(
            timezone.now()
        )
        self.assertEqual(result.received_pages, 2)
        self.assertTrue(all('pageSize=10' in url and 'since=' in url for url in calls))


class FullImportServiceTests(TestCase):
    def setUp(self):
        self.account = create_account()

    def hevy_client(self, *, invalid_reference=False, invalid_plan_reference=False):
        data = {
            '/v1/user/info': {'data': {'id': 'hevy-owner', 'name': 'Synthetic Owner', 'url': 'https://hevy.com/u/synthetic'}},
            '/v1/exercise_templates': {'page': 1, 'page_count': 1, 'exercise_templates': [template()]},
            '/v1/routine_folders': {'page': 1, 'page_count': 1, 'routine_folders': [folder()]},
            '/v1/routines': {'page': 1, 'page_count': 1, 'routines': [routine()]},
            '/v1/workouts': {'page': 1, 'page_count': 1, 'workouts': [workout()]},
        }
        if invalid_reference:
            data['/v1/workouts']['workouts'][0]['routine_id'] = 'missing'
        if invalid_plan_reference:
            data['/v1/routines']['routines'][0]['folder_id'] = 999

        def transport(url, headers, timeout):
            path = url.split('?', 1)[0].replace('https://api.hevyapp.com', '')
            return response(data[path])

        return HevyClient('synthetic-key', transport=transport)

    def incremental_client(self, events, *, repaired=None):
        data = {
            '/v1/workouts/events': {'page': 1, 'page_count': 1, 'events': events},
            '/v1/workouts/workout-1': repaired or workout(),
        }

        def transport(url, headers, timeout):
            path = url.split('?', 1)[0].replace('https://api.hevyapp.com', '')
            return response(data[path])

        return HevyClient('synthetic-key', transport=transport)

    def test_complete_import_is_idempotent_and_initializes_cursor(self):
        service = FullImportService(self.hevy_client())
        first = service.run(self.account.user)
        second = service.run(self.account.user)
        self.assertEqual(first.state, SyncRun.State.SUCCEEDED)
        self.assertEqual(second.state, SyncRun.State.SUCCEEDED)
        self.assertEqual(ExerciseTemplate.objects.count(), 1)
        self.assertEqual(RoutineFolder.objects.count(), 1)
        self.assertEqual(Routine.objects.count(), 1)
        self.assertEqual(Workout.objects.count(), 1)
        self.assertEqual(SyncCursor.objects.filter(stream_name=WORKOUT_EVENT_STREAM).count(), 1)

    def test_invalid_references_leave_canonical_data_unchanged(self):
        with self.assertRaises(ValueError):
            FullImportService(self.hevy_client(invalid_reference=True)).run(self.account.user)
        self.assertEqual(ExerciseTemplate.all_objects.count(), 0)
        run = SyncRun.objects.get()
        self.assertEqual(run.state, SyncRun.State.FAILED)
        self.assertFalse(SyncCursor.objects.exists())

    def test_command_requires_explicit_full_confirmation(self):
        with self.assertRaises(CommandError):
            call_command('sync_hevy', '--username', self.account.user.username)

    def test_command_maps_missing_key_to_configuration_exit_code(self):
        with patch.dict(os.environ, {'HEVY_API_KEY': ''}):
            with self.assertRaises(CommandError) as error:
                call_command(
                    'sync_hevy',
                    '--validate-only',
                    '--username',
                    self.account.user.username,
                )
        self.assertEqual(error.exception.returncode, 2)

    def test_full_import_records_adapter_and_database_failures(self):
        statuses = iter([200, 500, 500, 500])

        def failing_transport(url, headers, timeout):
            status = next(statuses)
            return response(
                {'data': {'id': 'hevy-owner', 'name': 'Synthetic Owner'}},
                status,
            )

        client = HevyClient(
            'synthetic-key',
            transport=failing_transport,
            sleep=lambda _: None,
            jitter=lambda: 0,
        )
        with self.assertRaises(HevyError):
            FullImportService(client).run(self.account.user)
        external_run = SyncRun.objects.get()
        self.assertEqual(external_run.state, SyncRun.State.FAILED)
        self.assertEqual(external_run.error_code, 'HTTP_TRANSIENT')

        SyncRun.objects.all().delete()
        repository = self.hevy_client()
        with patch('training.repositories.TrainingRepository.persist_full_import', side_effect=DatabaseError):
            with self.assertRaises(DatabaseError):
                FullImportService(repository).run(self.account.user)
        database_run = SyncRun.objects.get()
        self.assertEqual(database_run.state, SyncRun.State.FAILED)
        self.assertEqual(database_run.error_code, 'DATABASE_ERROR')
        self.assertEqual(database_run.sanitized_error, 'Database persistence failed.')

    def test_invalid_event_pagination_is_partial_and_keeps_cursor(self):
        FullImportService(self.hevy_client()).run(self.account.user)
        cursor = SyncCursor.objects.get(stream_name=WORKOUT_EVENT_STREAM)
        confirmed_at = cursor.confirmed_at
        client = HevyClient(
            'synthetic-key',
            transport=lambda *_: response({'page': 2, 'page_count': 2, 'events': []}),
        )

        with self.assertRaises(HevyError):
            IncrementalSyncService(client).run(self.account.user)

        cursor.refresh_from_db()
        run = SyncRun.objects.filter(mode=SyncRun.Mode.INCREMENTAL).get()
        self.assertEqual(run.state, SyncRun.State.PARTIAL)
        self.assertEqual(run.error_code, 'PAGINATION_INVALID')
        self.assertEqual(cursor.confirmed_at, confirmed_at)

    def test_incremental_requires_a_completed_initial_import(self):
        with self.assertRaises(HevyError) as error:
            IncrementalSyncService(self.incremental_client([])).run(self.account.user)

        self.assertEqual(error.exception.code, 'SYNC_NOT_INITIALIZED')
        self.assertFalse(SyncLock.objects.filter(is_active=True).exists())

    def test_incremental_overlap_deduplicates_and_advances_cursor_after_commit(self):
        FullImportService(self.hevy_client()).run(self.account.user)
        cursor = SyncCursor.objects.get(stream_name=WORKOUT_EVENT_STREAM)
        before = cursor.confirmed_at
        changed = workout()
        changed['title'] = 'Updated Workout'
        run = IncrementalSyncService(self.incremental_client([
            updated_event(changed), updated_event(changed),
        ])).run(self.account.user)
        cursor.refresh_from_db()
        self.assertEqual(run.state, SyncRun.State.SUCCEEDED)
        self.assertEqual(run.cursor_before, before)
        self.assertEqual(run.cursor_after, run.high_water_at)
        self.assertGreater(cursor.confirmed_at, before)
        self.assertEqual(Workout.objects.get().title, 'Updated Workout')
        self.assertEqual(run.item_counts['ignored'], 1)

    def test_equal_timestamp_delete_wins_and_changes_only_workouts(self):
        FullImportService(self.hevy_client()).run(self.account.user)
        changed = workout()
        changed['title'] = 'Would be restored'
        IncrementalSyncService(self.incremental_client([
            updated_event(changed), deleted_event(),
        ])).run(self.account.user)
        self.assertFalse(Workout.objects.exists())
        self.assertEqual(ExerciseTemplate.objects.count(), 1)
        self.assertEqual(Routine.objects.count(), 1)
        self.assertEqual(RoutineFolder.objects.count(), 1)

    def test_repair_and_failure_leave_cursor_and_workout_unchanged(self):
        FullImportService(self.hevy_client()).run(self.account.user)
        cursor = SyncCursor.objects.get(stream_name=WORKOUT_EVENT_STREAM)
        before = cursor.confirmed_at
        partial = {'id': 'workout-1', 'updated_at': '2026-08-02T12:00:00Z'}
        repaired = workout()
        repaired['title'] = 'Repaired Workout'
        IncrementalSyncService(self.incremental_client([
            updated_event(partial),
        ], repaired=repaired)).run(self.account.user)
        self.assertEqual(Workout.objects.get().title, 'Repaired Workout')
        cursor.refresh_from_db()
        self.assertGreater(cursor.confirmed_at, before)
        cursor_before_failure = cursor.confirmed_at
        invalid = workout()
        invalid['routine_id'] = 'missing'
        with self.assertRaises(ValueError):
            IncrementalSyncService(self.incremental_client([
                updated_event(invalid, '2026-08-03T12:00:00Z'),
            ])).run(self.account.user)
        cursor.refresh_from_db()
        self.assertEqual(cursor.confirmed_at, cursor_before_failure)
        self.assertEqual(Workout.objects.get().title, 'Repaired Workout')

    def test_incremental_lock_rejects_second_writer(self):
        FullImportService(self.hevy_client()).run(self.account.user)
        SyncLock.objects.update(is_active=True, acquired_at=timezone.now())
        with self.assertRaises(HevyError) as error:
            IncrementalSyncService(self.incremental_client([])).run(self.account.user)
        self.assertEqual(error.exception.code, 'SYNC_IN_PROGRESS')

    @override_settings(SYNC_LOCK_STALE_SECONDS=60)
    def test_incremental_recovers_a_stale_lock_and_audits_interrupted_run(self):
        FullImportService(self.hevy_client()).run(self.account.user)
        stale_at = timezone.now() - timedelta(minutes=5)
        SyncLock.objects.update(is_active=True, acquired_at=stale_at)
        interrupted = SyncRun.objects.create(
            hevy_account=self.account,
            mode=SyncRun.Mode.INCREMENTAL,
            trigger=SyncRun.Trigger.COMMAND,
            state=SyncRun.State.RUNNING,
            started_at=stale_at,
        )

        completed = IncrementalSyncService(self.incremental_client([])).run(
            self.account.user
        )

        interrupted.refresh_from_db()
        self.assertEqual(interrupted.state, SyncRun.State.FAILED)
        self.assertEqual(interrupted.error_code, 'SYNC_INTERRUPTED')
        self.assertEqual(completed.state, SyncRun.State.SUCCEEDED)
        self.assertFalse(SyncLock.objects.get().is_active)

    def test_plan_refresh_keeps_workouts_unchanged(self):
        FullImportService(self.hevy_client()).run(self.account.user)
        run = PlanRefreshService(self.hevy_client()).run(self.account.user)
        self.assertEqual(run.mode, SyncRun.Mode.PLANS)
        self.assertEqual(run.state, SyncRun.State.SUCCEEDED)
        self.assertEqual(Workout.objects.count(), 1)

    def test_plan_refresh_failure_is_audited(self):
        client = self.hevy_client(invalid_plan_reference=True)
        with self.assertRaises(ValueError):
            PlanRefreshService(client).run(self.account.user)

        run = SyncRun.objects.get()
        self.assertEqual(run.mode, SyncRun.Mode.PLANS)
        self.assertEqual(run.state, SyncRun.State.FAILED)
        self.assertEqual(run.error_code, 'REFERENCE_MISSING')


class SyncCommandTests(TestCase):
    def setUp(self):
        self.account = create_account('command-owner')

    @patch('integrations.management.commands.sync_hevy.HevyClient.from_environment')
    def test_validate_and_all_sync_modes_use_sanitized_output(self, client_factory):
        run = SimpleNamespace(
            id='synthetic-run',
            mode='incremental',
            state='succeeded',
            duration_ms=12,
            page_counts={'workouts': {'received': 1}},
            item_counts={'created': 1},
        )
        output = StringIO()
        with patch('integrations.management.commands.sync_hevy.FullImportService.validate_account', return_value=self.account):
            call_command('sync_hevy', '--validate-only', '--username', self.account.user.username, stdout=output)
        for mode, service_path in (
            ('full', 'integrations.management.commands.sync_hevy.FullImportService.run'),
            ('plans', 'integrations.management.commands.sync_hevy.PlanRefreshService.run'),
            ('incremental', 'integrations.management.commands.sync_hevy.IncrementalSyncService.run'),
        ):
            arguments = ['sync_hevy', f'--mode={mode}', '--username', self.account.user.username]
            if mode == 'full':
                arguments.append('--confirm-full-refresh')
            with patch(service_path, return_value=run):
                call_command(*arguments, stdout=output)
        self.assertIn('Hevy account validated:', output.getvalue())
        self.assertIn('run=synthetic-run', output.getvalue())
        self.assertNotIn('synthetic-key', output.getvalue())
        client_factory.assert_called()

    def test_error_codes_and_invalid_retry_are_stable(self):
        from integrations.management.commands.sync_hevy import Command

        self.assertEqual(Command._returncode('AUTH_INVALID'), 2)
        self.assertEqual(Command._returncode('HTTP_TIMEOUT'), 3)
        self.assertEqual(Command._returncode('PAGINATION_INVALID'), 4)
        self.assertEqual(Command._returncode('SYNC_IN_PROGRESS'), 5)
        self.assertEqual(Command._returncode('DATABASE_ERROR'), 6)
        with self.assertRaises(CommandError):
            call_command(
                'sync_hevy',
                '--mode=incremental',
                '--retry-run=not-a-uuid',
                '--username',
                self.account.user.username,
            )
