from unittest.mock import patch

from django.db import DatabaseError
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from integrations.credentials import session_credentials
from integrations.hevy import HevyError
from integrations.models import SyncRun
from training.tests.factories import create_account


class IntegrationReadViewTests(TestCase):
    def setUp(self):
        session_credentials.clear()
        self.account = create_account('integration-view-owner')
        self.client.force_login(self.account.user)

    def tearDown(self):
        session_credentials.clear()

    def test_sync_overview_does_not_render_credentials(self):
        response = self.client.get(reverse('integrations:sync'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Hevy connection')
        self.assertNotContains(response, 'HEVY_API_KEY')
        self.assertNotContains(response, 'api-key')
        self.assertContains(response, 'Disconnected')
        self.assertContains(response, 'type="password"')

    @patch('integrations.views._client_for_request')
    def test_incremental_without_cursor_returns_a_controlled_message(self, client_factory):
        response = self.client.post(reverse('integrations:incremental'), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'SYNC_NOT_INITIALIZED')
        self.assertFalse(SyncRun.objects.exists())

    def test_full_refresh_requires_confirmation(self):
        response = self.client.get(reverse('integrations:full-refresh'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Complete synchronization')

        response = self.client.post(reverse('integrations:full-refresh'), {})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This field is required.')

    def test_sync_mutations_require_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.account.user)

        self.assertEqual(client.post(reverse('integrations:validate')).status_code, 403)
        self.assertEqual(client.post(reverse('integrations:incremental')).status_code, 403)

    @patch('integrations.views.FullImportService.validate_account', side_effect=HevyError('AUTH_INVALID', 'Credential rejected.'))
    def test_validation_failure_is_sanitized_for_the_owner(self, validate):
        response = self.client.post(
            reverse('integrations:validate'), {'api_key': 'synthetic-key'}, follow=True
        )

        self.assertContains(response, 'AUTH_INVALID: Credential rejected.')
        self.assertNotContains(response, 'api-key')

    @patch('integrations.views._client_for_request')
    @patch('integrations.views.IncrementalSyncService.run', side_effect=DatabaseError('private database detail'))
    def test_database_failure_does_not_render_internal_detail(self, run_sync, client_factory):
        response = self.client.post(reverse('integrations:incremental'), follow=True)

        self.assertContains(response, 'DATABASE_ERROR: Local persistence failed.')
        self.assertNotContains(response, 'private database detail')

    @patch('integrations.views.FullImportService.validate_account')
    def test_validate_action_is_post_only_and_redirects(self, validate):
        validate.return_value = self.account

        response = self.client.post(
            reverse('integrations:validate'), {'api_key': 'synthetic-key'}
        )

        self.assertRedirects(response, reverse('integrations:sync'))
        validate.assert_called_once_with(self.account.user)
        follow = self.client.get(reverse('integrations:sync'))
        self.assertContains(follow, 'Connected')
        self.assertNotContains(follow, 'synthetic-key')

    @patch('integrations.views._client_for_request')
    @patch('integrations.views.IncrementalSyncService.run')
    def test_incremental_action_redirects_to_run_detail(self, run_sync, client_factory):
        run = SyncRun.objects.create(
            hevy_account=self.account,
            mode=SyncRun.Mode.INCREMENTAL,
            trigger=SyncRun.Trigger.WEB,
            state=SyncRun.State.SUCCEEDED,
            started_at=timezone.now(),
        )
        run_sync.return_value = run

        response = self.client.post(reverse('integrations:incremental'))

        self.assertRedirects(response, reverse('integrations:run-detail', args=[run.pk]))
        run_sync.assert_called_once_with(self.account.user, trigger=SyncRun.Trigger.WEB)
        client_factory.assert_called_once()

    @patch('integrations.views._client_for_request')
    @patch('integrations.views.FullImportService.run')
    def test_full_refresh_action_uses_explicit_confirmation(self, run_full, client_factory):
        run = SyncRun.objects.create(
            hevy_account=self.account,
            mode=SyncRun.Mode.FULL,
            trigger=SyncRun.Trigger.WEB,
            state=SyncRun.State.SUCCEEDED,
            started_at=timezone.now(),
        )
        run_full.return_value = run

        response = self.client.post(reverse('integrations:full-refresh'), {'confirmation': '1'})

        self.assertRedirects(response, reverse('integrations:run-detail', args=[run.pk]))
        run_full.assert_called_once_with(self.account.user, trigger=SyncRun.Trigger.WEB)
        client_factory.assert_called_once()

    @patch('integrations.views._client_for_request')
    @patch(
        'integrations.views.FullImportService.run',
        side_effect=HevyError('HTTP_TRANSIENT', 'Provider temporarily unavailable.'),
    )
    def test_full_refresh_failure_returns_to_sync_without_sensitive_data(self, run_full, client_factory):
        response = self.client.post(
            reverse('integrations:full-refresh'),
            {'confirmation': '1'},
            follow=True,
        )

        self.assertContains(response, 'HTTP_TRANSIENT: Provider temporarily unavailable.')
        self.assertNotContains(response, 'api-key')

    def test_partial_run_is_not_presented_as_success(self):
        run = SyncRun.objects.create(
            hevy_account=self.account,
            mode=SyncRun.Mode.INCREMENTAL,
            trigger=SyncRun.Trigger.WEB,
            state=SyncRun.State.PARTIAL,
            started_at=timezone.now(),
            error_code='PAGINATION_INVALID',
            sanitized_error='Pagination metadata was invalid.',
        )

        response = self.client.get(reverse('integrations:run-detail', args=[run.pk]))

        self.assertContains(response, 'Partial')
        self.assertContains(response, 'Retry synchronization')
        self.assertNotContains(response, 'succeeded')

    def test_retry_rejects_ineligible_run(self):
        run = SyncRun.objects.create(
            hevy_account=self.account,
            mode=SyncRun.Mode.FULL,
            state=SyncRun.State.SUCCEEDED,
            started_at=timezone.now(),
        )

        response = self.client.post(reverse('integrations:retry', args=[run.pk]), follow=True)

        self.assertContains(response, 'Only failed or partial incremental')

    @patch('integrations.views._client_for_request')
    @patch('integrations.views.IncrementalSyncService.run')
    def test_retry_links_to_previous_run(self, run_sync, client_factory):
        prior = SyncRun.objects.create(
            hevy_account=self.account,
            mode=SyncRun.Mode.INCREMENTAL,
            trigger=SyncRun.Trigger.WEB,
            state=SyncRun.State.FAILED,
            started_at=timezone.now(),
        )
        retry = SyncRun.objects.create(
            hevy_account=self.account,
            mode=SyncRun.Mode.INCREMENTAL,
            trigger=SyncRun.Trigger.RETRY,
            state=SyncRun.State.SUCCEEDED,
            started_at=timezone.now(),
            prior_run=prior,
        )
        run_sync.return_value = retry

        response = self.client.post(reverse('integrations:retry', args=[prior.pk]))

        self.assertRedirects(response, reverse('integrations:run-detail', args=[retry.pk]))
        run_sync.assert_called_once_with(
            self.account.user,
            prior_run=prior,
            trigger=SyncRun.Trigger.RETRY,
        )
        client_factory.assert_called_once()
