import json

from django.test import TestCase

from integrations.hevy import HevyClient, HevyError
from integrations.routines import (
    RoutinePayloadValidator,
    RoutineValidationError,
)
from training.tests.factories import (
    create_account,
    create_template,
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
        with self.assertRaisesMessage(RoutineValidationError, 'Incompatible metric'):
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
            ([], 'JSON object'),
            ({'unexpected': {}}, 'Unknown fields'),
            ({'routine': {'title': '', 'exercises': []}}, 'valid text'),
            ({'routine': {'title': 'A', 'folder_id': 999, 'exercises': []}}, 'Unknown local catalogue ID'),
            ({'routine': {'title': 'A', 'exercises': []}}, 'between 1 and 50'),
        ]
        for payload, message in invalid_payloads:
            with self.subTest(message=message), self.assertRaisesMessage(
                RoutineValidationError, message
            ):
                validator.validate(payload)

        unknown_template = routine_request('missing-template')
        with self.assertRaisesMessage(RoutineValidationError, 'local catalogue'):
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
        with self.assertRaisesMessage(RoutineValidationError, 'measurable prescription'):
            validator.validate(invalid_set)

        invalid_range = routine_request(self.template.external_id)
        invalid_range['routine']['exercises'][0]['sets'][0]['rep_range'] = {
            'start': 10, 'end': 8,
        }
        with self.assertRaisesMessage(RoutineValidationError, 'positive start'):
            validator.validate(invalid_range)
