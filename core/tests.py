import tempfile
from pathlib import Path
from unittest import mock

from django.db import DatabaseError
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from core.checks import private_environment_file_permissions


class HealthTests(SimpleTestCase):
    def test_health_is_public_and_database_independent(self):
        response = self.client.get(reverse('health'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok'})

    def test_health_uses_restrictive_csp(self):
        response = self.client.get(reverse('health'))
        policy = response.headers['Content-Security-Policy']

        self.assertIn("default-src 'self'", policy)
        self.assertIn("script-src-attr 'none'", policy)
        self.assertIn("frame-ancestors 'none'", policy)
        self.assertNotIn("'unsafe-inline'", policy)

    def test_security_headers_are_enabled(self):
        response = self.client.get(reverse('health'))

        self.assertEqual(response.headers['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(response.headers['Referrer-Policy'], 'same-origin')
        self.assertEqual(response.headers['Cross-Origin-Opener-Policy'], 'same-origin')
        self.assertEqual(response.headers['X-Frame-Options'], 'DENY')

    @override_settings(SECURE_HSTS_SECONDS=31536000)
    def test_hsts_is_sent_only_on_https(self):
        self.assertNotIn('Strict-Transport-Security', self.client.get(reverse('health')).headers)
        secure = self.client.get(reverse('health'), secure=True)
        self.assertEqual(secure.headers['Strict-Transport-Security'], 'max-age=31536000')


class ReadinessTests(TestCase):
    def test_readiness_checks_the_database(self):
        response = self.client.get(reverse('readiness'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ready'})

    @mock.patch('core.views.connection.cursor', side_effect=DatabaseError)
    def test_readiness_reports_database_failure(self, cursor):
        response = self.client.get(reverse('readiness'))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {'status': 'unavailable'})


class SecretScanTests(SimpleTestCase):
    def test_secret_canary_is_detected_without_flagging_placeholders(self):
        from scripts.security.scan_secrets import CANARY, secret_lines

        self.assertEqual(secret_lines(f'HEVY_API_KEY={CANARY}'.encode()), {1})
        self.assertEqual(secret_lines(b'HEVY_API_KEY=\nHEVY_API_KEY=synthetic-test-value'), set())

    def test_private_runtime_paths_are_rejected(self):
        from pathlib import PurePosixPath

        from scripts.security.scan_secrets import prohibited_private_path

        self.assertTrue(prohibited_private_path(PurePosixPath('.env')))
        self.assertTrue(prohibited_private_path(PurePosixPath('data/Hevy/routines.json')))
        self.assertTrue(prohibited_private_path(PurePosixPath('var/private/app.sqlite3')))
        self.assertFalse(prohibited_private_path(PurePosixPath('.env.example')))


class EnvironmentPermissionTests(SimpleTestCase):
    @mock.patch('core.checks.os.name', 'posix')
    def test_group_readable_environment_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / '.env'
            env_file.write_text('SECRET_KEY=synthetic-test-value\n')
            env_file.chmod(0o640)
            with override_settings(ENV_FILE=env_file):
                errors = private_environment_file_permissions(None)

        self.assertEqual([error.id for error in errors], ['core.E001'])

    @mock.patch('core.checks.os.name', 'posix')
    def test_owner_only_environment_file_is_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / '.env'
            env_file.write_text('SECRET_KEY=synthetic-test-value\n')
            env_file.chmod(0o600)
            with override_settings(ENV_FILE=env_file):
                errors = private_environment_file_permissions(None)

        self.assertEqual(errors, [])
