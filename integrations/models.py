import uuid

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q

from core.validators import validate_aware_datetime


class HevyAccount(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='hevy_account',
    )
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
        DISCONNECTED = 'disconnected', 'Disconnected'
        CONNECTED = 'connected', 'Connected'
        ERROR = 'error', 'Error'

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


class SyncRun(models.Model):
    class Mode(models.TextChoices):
        FULL = 'full', 'Full'
        INCREMENTAL = 'incremental', 'Incremental'
        PLANS = 'plans', 'Plans'
        VALIDATE = 'validate', 'Validate'

    class Trigger(models.TextChoices):
        WEB = 'web', 'Web'
        COMMAND = 'command', 'Command'
        SCHEDULE = 'schedule', 'Schedule'
        RETRY = 'retry', 'Retry'

    class State(models.TextChoices):
        PENDING = 'pending', 'Pending'
        RUNNING = 'running', 'Running'
        SUCCEEDED = 'succeeded', 'Succeeded'
        PARTIAL = 'partial', 'Partial'
        FAILED = 'failed', 'Failed'

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
