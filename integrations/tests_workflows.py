import csv
import json
from datetime import timedelta
from io import StringIO
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from integrations.credentials import session_credentials
from integrations.hevy import HevyClient, HevyError
from integrations.models import RoutineWriteIntent, SyncRun
from integrations.prompting import PromptTemplateService
from integrations.routines import (
    RoutinePayloadValidator,
    RoutineValidationError,
    RoutineWriteService,
)
from training.tests.factories import (
    create_account,
    create_routine,
    create_template,
    create_workout,
)


def routine_request(template_id, folder_id=None):
    return {
        'routine': {
            'title': 'Upper seguro',
            'folder_id': folder_id,
            'notes': 'Controle a execução.',
            'exercises': [{
                'exercise_template_id': template_id,
                'superset_id': None,
                'rest_seconds': 90,
                'notes': None,
                'sets': [{
                    'type': 'normal',
                    'weight_kg': 40,
                    'reps': None,
                    'distance_meters': None,
                    'duration_seconds': None,
                    'custom_metric': None,
                    'rep_range': {'start': 8, 'end': 10},
                }],
            }],
        }
    }


def routine_response(identifier='routine-created'):
    return {
        'routine': {
            'id': identifier,
            'folder_id': None,
            'title': 'Upper seguro',
            'exercises': [{
                'index': 0,
                'title': 'Synthetic Press',
                'exercise_template_id': 'template-write',
                'rest_seconds': 90,
                'notes': None,
                'supersets_id': None,
                'sets': [{
                    'index': 0,
                    'type': 'normal',
                    'weight_kg': 40,
                    'reps': None,
                    'distance_meters': None,
                    'duration_seconds': None,
                    'custom_metric': None,
                    'rep_range': {'start': 8, 'end': 10},
                }],
            }],
        }
    }


class EphemeralCredentialFlowTests(TestCase):
    def setUp(self):
        session_credentials.clear()
        self.account = create_account('ephemeral-owner')
        self.client.force_login(self.account.user)

    def tearDown(self):
        session_credentials.clear()

    @patch('integrations.views.FullImportService.validate_account')
    def test_key_is_available_only_to_same_session_and_cleared_on_disconnect(self, validate):
        validate.return_value = self.account
        self.client.post(
            reverse('integrations:validate'), {'api_key': 'credential-canary'}
        )

        connected = self.client.get(reverse('integrations:sync'))
        self.assertContains(connected, 'Sessão conectada')
        self.assertNotContains(connected, 'credential-canary')

        other = self.client_class()
        other.force_login(self.account.user)
        self.assertContains(other.get(reverse('integrations:sync')), 'Sessão desconectada')

        self.client.post(reverse('integrations:disconnect'))
        self.assertContains(
            self.client.get(reverse('integrations:sync')), 'Sessão desconectada'
        )

    @patch('integrations.views.FullImportService.validate_account')
    def test_logout_forgets_key(self, validate):
        validate.return_value = self.account
        self.client.post(
            reverse('integrations:validate'), {'api_key': 'credential-canary'}
        )
        self.client.post(reverse('accounts:logout'))
        self.client.force_login(self.account.user)

        self.assertContains(
            self.client.get(reverse('integrations:sync')), 'Sessão desconectada'
        )


class RoutineWorkflowTests(TestCase):
    def setUp(self):
        self.account = create_account('routine-workflow-owner')
        self.template = create_template(
            self.account, external_id='template-write'
        )

    def test_validator_normalizes_known_references_and_rejects_incompatible_metrics(self):
        validator = RoutinePayloadValidator(self.account)
        payload = validator.validate(routine_request(self.template.external_id))
        self.assertEqual(payload['routine']['exercises'][0]['rest_seconds'], 90)

        invalid = routine_request(self.template.external_id)
        training_set = invalid['routine']['exercises'][0]['sets'][0]
        training_set['duration_seconds'] = 30
        with self.assertRaisesMessage(RoutineValidationError, 'métrica incompatível'):
            validator.validate(invalid)

        without_range = routine_request(self.template.external_id)
        training_set = without_range['routine']['exercises'][0]['sets'][0]
        training_set['reps'] = 8
        training_set['rep_range'] = None
        normalized = validator.validate(without_range)
        self.assertNotIn(
            'rep_range', normalized['routine']['exercises'][0]['sets'][0]
        )

    def test_client_posts_once_and_never_retries_timeout(self):
        calls = []

        def write_transport(url, headers, body, timeout):
            calls.append((url, headers, body, timeout))
            return 201, {}, json.dumps(routine_response()).encode()

        result = HevyClient(
            'credential-canary', write_transport=write_transport
        ).create_routine(routine_request(self.template.external_id))

        self.assertEqual(result.external_id, 'routine-created')
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][1]['api-key'], 'credential-canary')
        self.assertNotIn(b'credential-canary', calls[0][2])

        timed_out = HevyClient(
            'credential-canary',
            write_transport=lambda *_: (_ for _ in ()).throw(TimeoutError),
        )
        with self.assertRaises(HevyError) as error:
            timed_out.create_routine(routine_request(self.template.external_id))
        self.assertEqual(error.exception.code, 'WRITE_UNKNOWN')

    def test_client_classifies_write_responses_without_retrying(self):
        cases = [
            (201, b'{}', 'WRITE_UNKNOWN'),
            (401, b'{}', 'AUTH_INVALID'),
            (503, b'{}', 'WRITE_UNKNOWN'),
            (422, b'{}', 'HTTP_PERMANENT'),
        ]
        for status, body, expected_code in cases:
            calls = []

            def transport(*args):
                calls.append(args)
                return status, {}, body

            with self.subTest(status=status), self.assertRaises(HevyError) as error:
                HevyClient(
                    'credential-canary', write_transport=transport
                ).create_routine(routine_request(self.template.external_id))
            self.assertEqual(error.exception.code, expected_code)
            self.assertEqual(len(calls), 1)

        oversized = routine_request(self.template.external_id)
        oversized['routine']['notes'] = 'x' * 66_000
        with self.assertRaisesMessage(HevyError, 'size limit'):
            HevyClient('credential-canary').create_routine(oversized)

    def test_validator_rejects_unknown_references_shapes_and_empty_prescriptions(self):
        validator = RoutinePayloadValidator(self.account)
        invalid_payloads = [
            ([], 'objeto JSON'),
            ({'unexpected': {}}, 'não permitido'),
            ({'routine': {'title': '', 'exercises': []}}, 'texto válido'),
            ({'routine': {'title': 'A', 'folder_id': 999, 'exercises': []}}, 'não existe'),
            ({'routine': {'title': 'A', 'exercises': []}}, 'entre 1 e 50'),
        ]
        for payload, message in invalid_payloads:
            with self.subTest(message=message), self.assertRaisesMessage(
                RoutineValidationError, message
            ):
                validator.validate(payload)

        unknown_template = routine_request('missing-template')
        with self.assertRaisesMessage(RoutineValidationError, 'catálogo local'):
            validator.validate(unknown_template)

        invalid_set = routine_request(self.template.external_id)
        invalid_set['routine']['exercises'][0]['sets'][0] = {
            'type': 'normal',
            'weight_kg': None,
            'reps': None,
            'distance_meters': None,
            'duration_seconds': None,
            'custom_metric': None,
            'rep_range': None,
        }
        with self.assertRaisesMessage(RoutineValidationError, 'mensurável'):
            validator.validate(invalid_set)

        invalid_range = routine_request(self.template.external_id)
        invalid_range['routine']['exercises'][0]['sets'][0]['rep_range'] = {
            'start': 10, 'end': 8,
        }
        with self.assertRaisesMessage(RoutineValidationError, 'início positivo'):
            validator.validate(invalid_range)

    def test_intent_is_single_use_and_unknown_write_is_audited(self):
        payload = RoutinePayloadValidator(self.account).validate(
            routine_request(self.template.external_id)
        )
        service = RoutineWriteService()
        intent = service.create_intent(self.account, payload)
        client = Mock()
        client.create_routine.side_effect = HevyError(
            'WRITE_UNKNOWN', 'Hevy did not confirm whether the routine was created.'
        )

        with self.assertRaises(HevyError):
            service.submit(self.account, intent.pk, client)

        intent.refresh_from_db()
        self.assertEqual(intent.state, RoutineWriteIntent.State.UNKNOWN)
        self.assertEqual(SyncRun.objects.get().state, SyncRun.State.PARTIAL)
        with self.assertRaisesMessage(RoutineValidationError, 'já foi consumida'):
            service.submit(self.account, intent.pk, client)
        client.create_routine.assert_called_once()

    def test_expired_intent_never_calls_provider(self):
        payload = RoutinePayloadValidator(self.account).validate(
            routine_request(self.template.external_id)
        )
        intent = RoutineWriteService().create_intent(self.account, payload)
        RoutineWriteIntent.objects.filter(pk=intent.pk).update(
            expires_at=timezone.now() - timedelta(seconds=1)
        )
        client = Mock()

        with self.assertRaisesMessage(RoutineValidationError, 'expirou'):
            RoutineWriteService().submit(self.account, intent.pk, client)
        client.create_routine.assert_not_called()


class ExportAndPromptTests(TestCase):
    def setUp(self):
        self.account = create_account('export-prompt-owner')
        self.template = create_template(self.account, external_id='prompt-template')
        self.routine = create_routine(self.account, self.template)
        create_workout(self.account, self.template, routine=self.routine)
        self.client.force_login(self.account.user)

    def test_exercise_and_routine_exports_are_structured_and_secret_free(self):
        exercises = self.client.get(
            reverse('integrations:local-export', args=['exercises', 'json'])
        )
        self.assertEqual(exercises['Content-Type'], 'application/json; charset=utf-8')
        self.assertEqual(
            json.loads(exercises.content)['exercise_templates'][0]['id'],
            'prompt-template',
        )

        routines = self.client.get(
            reverse('integrations:local-export', args=['routines', 'csv'])
        )
        rows = list(csv.DictReader(StringIO(routines.content.decode())))
        self.assertEqual(rows[0]['routine_title'], self.routine.title)
        self.assertNotIn('api_key', routines.content.decode().lower())

        exercises_csv = self.client.get(
            reverse('integrations:local-export', args=['exercises', 'csv'])
        )
        self.assertIn('prompt-template', exercises_csv.content.decode())
        routines_json = self.client.get(
            reverse('integrations:local-export', args=['routines', 'json'])
        )
        self.assertEqual(
            json.loads(routines_json.content)['routines'][0]['title'],
            self.routine.title,
        )

    def test_prompt_contains_local_context_and_no_credential_placeholder(self):
        generated = PromptTemplateService(self.account).build({
            'objective': 'Ganhar força',
            'desired_frequency': 4,
            'session_duration_minutes': 45,
            'available_equipment': 'Barra e halteres',
            'limitations': '',
            'observations': '',
            'period_mode': 'last_7_days',
            'period_value': 1,
        })

        self.assertIn('Ganhar força', generated)
        self.assertIn(self.routine.title, generated)
        self.assertIn('retorne somente JSON válido', generated)
        self.assertNotIn('HEVY_API_KEY', generated)
        self.assertNotIn('<API_KEY>', generated)

    def test_prompt_form_enforces_period_limits(self):
        response = self.client.post(reverse('integrations:prompt-template'), {
            'objective': 'Força',
            'desired_frequency': 4,
            'session_duration_minutes': 45,
            'available_equipment': 'Halteres',
            'limitations': '',
            'observations': '',
            'period_mode': 'weeks',
            'period_value': 53,
            'action': 'preview',
        })
        self.assertContains(response, 'O limite para esta opção é 52.')

    def test_prompt_preview_and_download_are_local_http_workflows(self):
        data = {
            'objective': 'Força',
            'desired_frequency': 4,
            'session_duration_minutes': 45,
            'available_equipment': 'Halteres',
            'limitations': '',
            'observations': '',
            'period_mode': 'workouts',
            'period_value': 1,
        }
        preview = self.client.post(
            reverse('integrations:prompt-template'), {**data, 'action': 'preview'}
        )
        self.assertContains(preview, 'Prompt gerado')
        self.assertContains(preview, 'Synthetic Workout')

        download = self.client.post(
            reverse('integrations:prompt-template'), {**data, 'action': 'download'}
        )
        self.assertEqual(download['Content-Type'], 'text/markdown; charset=utf-8')
        self.assertIn('attachment;', download['Content-Disposition'])


class GuidedWorkflowViewTests(TestCase):
    def setUp(self):
        session_credentials.clear()
        self.account = create_account('guided-view-owner')
        self.template = create_template(self.account, external_id='guided-template')
        self.client.force_login(self.account.user)

    def tearDown(self):
        session_credentials.clear()

    def test_routine_json_is_validated_before_preview(self):
        url = reverse('integrations:routine-create')
        self.assertContains(self.client.get(url), 'Criar rotina via JSON')
        self.assertContains(self.client.post(url, {'payload': '['}), 'JSON inválido')
        self.assertContains(
            self.client.post(url, {'payload': json.dumps({'routine': {}})}),
            'texto válido',
        )

        response = self.client.post(
            url, {'payload': json.dumps(routine_request(self.template.external_id))}
        )
        self.assertContains(response, 'Prévia validada')
        self.assertContains(response, 'Upper seguro')
        self.assertEqual(RoutineWriteIntent.objects.count(), 1)

    def test_provider_actions_require_a_valid_ephemeral_credential(self):
        response = self.client.post(
            reverse('integrations:plan-refresh'), follow=True
        )
        self.assertContains(response, 'CONFIG_MISSING_KEY')
        self.assertContains(response, 'Conecte sua API key')

        response = self.client.post(
            reverse('integrations:validate'), {'api_key': ' '}, follow=True
        )
        self.assertContains(response, 'Informe uma API key válida')

    @patch('integrations.views.PlanRefreshService.run')
    @patch('integrations.views.RoutineWriteService.submit')
    @patch('integrations.views._client_for_request')
    def test_confirmed_routine_is_submitted_and_refreshed_once(
        self, client_factory, submit, refresh
    ):
        intent = RoutineWriteService().create_intent(
            self.account,
            RoutinePayloadValidator(self.account).validate(
                routine_request(self.template.external_id)
            ),
        )
        submit.return_value = SimpleNamespace(external_id='remote-routine')
        response = self.client.post(reverse('integrations:routine-confirm'), {
            'intent_id': intent.pk,
            'confirmation': 'on',
        })

        self.assertRedirects(response, reverse('integrations:sync'))
        submit.assert_called_once_with(self.account, intent.pk, client_factory.return_value)
        refresh.assert_called_once_with(self.account.user, trigger=SyncRun.Trigger.WEB)

    @patch('integrations.views.PlanRefreshService.run')
    @patch('integrations.views.RoutineWriteService.submit')
    @patch('integrations.views._client_for_request')
    def test_confirmed_remote_write_warns_when_local_refresh_fails(
        self, client_factory, submit, refresh
    ):
        intent = RoutineWriteService().create_intent(
            self.account,
            RoutinePayloadValidator(self.account).validate(
                routine_request(self.template.external_id)
            ),
        )
        submit.return_value = SimpleNamespace(external_id='remote-routine')
        refresh.side_effect = HevyError('HTTP_TRANSIENT', 'temporary')

        response = self.client.post(
            reverse('integrations:routine-confirm'),
            {'intent_id': intent.pk, 'confirmation': 'on'},
            follow=True,
        )
        self.assertContains(response, 'foi criada no Hevy')
        self.assertContains(response, 'não puderam ser atualizados')

    @patch('integrations.views.PlanRefreshService.run')
    @patch('integrations.views._client_for_request')
    def test_plan_refresh_redirects_to_audited_run(self, client_factory, refresh):
        run = SyncRun.objects.create(
            hevy_account=self.account,
            mode=SyncRun.Mode.PLANS,
            state=SyncRun.State.SUCCEEDED,
            started_at=timezone.now(),
        )
        refresh.return_value = run
        response = self.client.post(reverse('integrations:plan-refresh'))
        self.assertRedirects(response, reverse('integrations:run-detail', args=[run.pk]))
        refresh.assert_called_once_with(self.account.user, trigger=SyncRun.Trigger.WEB)

    def test_invalid_export_and_confirmation_are_controlled(self):
        self.assertEqual(
            self.client.get(
                reverse('integrations:local-export', args=['unknown', 'txt'])
            ).status_code,
            404,
        )
        response = self.client.post(reverse('integrations:routine-confirm'), {}, follow=True)
        self.assertContains(response, 'confirmação da rotina é inválida')
