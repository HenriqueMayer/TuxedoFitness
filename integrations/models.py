import uuid

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.utils.translation import gettext_lazy as _

from core.validators import validate_aware_datetime


class HevyAccount(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='hevy_account',
    )
    encrypted_api_key = models.TextField(blank=True, editable=False)
    credential_updated_at = models.DateTimeField(null=True, blank=True)
    external_user_id = models.CharField(max_length=255, unique=True)
    display_name = models.CharField(max_length=255)
    profile_url = models.URLField(max_length=500, blank=True)
    verified_at = models.DateTimeField(
        validators=[validate_aware_datetime],
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.display_name


class IntegrationState(models.Model):
    class Status(models.TextChoices):
        DISCONNECTED = 'disconnected', _('Disconnected')
        CONNECTED = 'connected', _('Connected')
        ERROR = 'error', _('Error')

    hevy_account = models.OneToOneField(
        HevyAccount,
        on_delete=models.CASCADE,
        related_name='integration_state',
    )
    status = models.CharField(
        max_length=16,
        choices=Status,
        default=Status.DISCONNECTED,
    )
    last_validated_at = models.DateTimeField(
        validators=[validate_aware_datetime],
        null=True,
        blank=True,
    )
    last_success_at = models.DateTimeField(
        validators=[validate_aware_datetime],
        null=True,
        blank=True,
    )
    last_full_refresh_at = models.DateTimeField(
        validators=[validate_aware_datetime],
        null=True,
        blank=True,
    )
    last_incremental_run_at = models.DateTimeField(
        validators=[validate_aware_datetime],
        null=True,
        blank=True,
    )
    is_stale = models.BooleanField(default=True)
    last_plans_at = models.DateTimeField(null=True, blank=True)
    last_catalog_at = models.DateTimeField(null=True, blank=True)
    next_auto_attempt_at = models.DateTimeField(null=True, blank=True)


class SyncRun(models.Model):
    class Mode(models.TextChoices):
        FULL = 'full', _('Full')
        INCREMENTAL = 'incremental', _('Incremental')
        PLANS = 'plans', _('Plans')
        VALIDATE = 'validate', _('Validate')
        ROUTINE_CREATE = 'routine_create', _('Routine create')

    class Trigger(models.TextChoices):
        WEB = 'web', _('Web')
        COMMAND = 'command', _('Command')
        SCHEDULE = 'schedule', _('Schedule')
        RETRY = 'retry', _('Retry')

    class State(models.TextChoices):
        PENDING = 'pending', _('Pending')
        RUNNING = 'running', _('Running')
        SUCCEEDED = 'succeeded', _('Succeeded')
        PARTIAL = 'partial', _('Partial')
        FAILED = 'failed', _('Failed')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hevy_account = models.ForeignKey(
        HevyAccount,
        on_delete=models.CASCADE,
        related_name='sync_runs',
    )
    mode = models.CharField(max_length=16, choices=Mode)
    trigger = models.CharField(max_length=16, choices=Trigger)
    state = models.CharField(
        max_length=16,
        choices=State,
        default=State.PENDING,
    )
    started_at = models.DateTimeField(
        validators=[validate_aware_datetime],
        null=True,
        blank=True,
    )
    finished_at = models.DateTimeField(
        validators=[validate_aware_datetime],
        null=True,
        blank=True,
    )
    duration_ms = models.PositiveBigIntegerField(null=True, blank=True)
    item_counts = models.JSONField(default=dict, blank=True)
    page_counts = models.JSONField(default=dict, blank=True)
    retry_count = models.PositiveSmallIntegerField(default=0)
    cursor_before = models.DateTimeField(
        validators=[validate_aware_datetime],
        null=True,
        blank=True,
    )
    cursor_after = models.DateTimeField(
        validators=[validate_aware_datetime],
        null=True,
        blank=True,
    )
    high_water_at = models.DateTimeField(
        validators=[validate_aware_datetime],
        null=True,
        blank=True,
    )
    error_code = models.CharField(max_length=64, blank=True)
    sanitized_error = models.CharField(max_length=500, blank=True)
    adapter_version = models.CharField(max_length=32, blank=True)
    application_version = models.CharField(max_length=32, blank=True)
    provider_schema_version = models.CharField(max_length=32, blank=True)
    prior_run = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        related_name='retries',
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(started_at__isnull=True)
                    | Q(finished_at__isnull=True)
                    | Q(finished_at__gte=F('started_at'))
                ),
                name='sync_run_valid_time_range',
            ),
        ]
        indexes = [
            models.Index(
                fields=['hevy_account', 'state', 'started_at'],
                name='sync_run_account_state_idx',
            ),
        ]



class SyncCursor(models.Model):
    hevy_account = models.ForeignKey(
        HevyAccount,
        on_delete=models.CASCADE,
        related_name='sync_cursors',
    )
    stream_name = models.CharField(max_length=64)
    confirmed_at = models.DateTimeField(validators=[validate_aware_datetime])
    overlap_seconds = models.PositiveIntegerField(
        default=300,
        validators=[MinValueValidator(0)],
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['hevy_account', 'stream_name'],
                name='unique_sync_cursor_stream',
            ),
        ]


class SyncLock(models.Model):
    hevy_account = models.OneToOneField(
        HevyAccount,
        on_delete=models.CASCADE,
        related_name='sync_lock',
    )
    is_active = models.BooleanField(default=False)
    acquired_at = models.DateTimeField(
        validators=[validate_aware_datetime],
        null=True,
        blank=True,
    )


class ProviderSnapshot(models.Model):
    """Latest complete provider pages, committed with their normalized records."""
    hevy_account = models.ForeignKey(HevyAccount, on_delete=models.CASCADE, related_name='snapshots')
    resource = models.CharField(max_length=32)
    pages = models.JSONField(default=list)
    synced_at = models.DateTimeField()
    source_hash = models.CharField(max_length=64)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['hevy_account', 'resource'], name='unique_provider_snapshot')]
