from datetime import datetime

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from integrations.models import HevyAccount, SyncCursor, SyncRun
from training.tests.factories import create_account


class IntegrationModelTests(TestCase):
    def test_cursor_is_unique_per_account_and_stream(self):
        account = create_account()
        SyncCursor.objects.create(
            hevy_account=account,
            stream_name='workout-events',
            confirmed_at=timezone.now(),
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            SyncCursor.objects.create(
                hevy_account=account,
                stream_name='workout-events',
                confirmed_at=timezone.now(),
            )

    def test_sync_timestamps_reject_naive_values(self):
        account = create_account()
        cursor = SyncCursor(
            hevy_account=account,
            stream_name='workout-events',
            confirmed_at=datetime(2026, 1, 1, 12, 0),
        )

        with self.assertRaises(ValidationError):
            cursor.full_clean()

    def test_account_deletion_cascades_to_sync_state(self):
        account = create_account()
        SyncRun.objects.create(
            hevy_account=account,
            mode=SyncRun.Mode.FULL,
            trigger=SyncRun.Trigger.COMMAND,
        )
        HevyAccount.objects.get(pk=account.pk).delete()

        self.assertFalse(SyncRun.objects.exists())
