from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.db import DatabaseError, IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone

from integrations.hevy import HevyClient, HevyError
from integrations.models import (
    HevyAccount,
    IntegrationState,
    ProviderSnapshot,
    SyncCursor,
    SyncLock,
    SyncRun,
)
from training.models import ExerciseTemplate, Routine, RoutineFolder, Workout
from training.repositories import TrainingRepository

ADAPTER_VERSION = '2.0'
PROVIDER_SCHEMA_VERSION = '2026-09-05'
WORKOUT_EVENT_STREAM = 'workout-events'


class FullImportService:
    def __init__(self, client: HevyClient, repository: TrainingRepository | None = None):
        self.client = client
        self.repository = repository or TrainingRepository()

    def validate_account(self, user) -> HevyAccount:
        dto = self.client.user_info()
        current = HevyAccount.objects.filter(user=user).first()
        if current is not None and current.external_user_id != dto.external_id:
            raise HevyError('ACCOUNT_MISMATCH', 'This key belongs to a different Hevy account.')
        account, _ = HevyAccount.objects.update_or_create(
            user=user,
            defaults={
                'external_user_id': dto.external_id,
                'display_name': dto.display_name,
                'profile_url': dto.profile_url,
                'verified_at': timezone.now(),
            },
        )
        IntegrationState.objects.update_or_create(
            hevy_account=account,
            defaults={
                'status': IntegrationState.Status.CONNECTED,
                'last_validated_at': timezone.now(),
                'is_stale': True,
            },
        )
        return account

    def run(self, user, *, trigger=SyncRun.Trigger.COMMAND) -> SyncRun:
        run_started = timezone.now()
        account = self.validate_account(user)
        IncrementalSyncService._acquire_lock(account)
        run = SyncRun.objects.create(
            hevy_account=account,
            mode=SyncRun.Mode.FULL,
            trigger=trigger,
            state=SyncRun.State.RUNNING,
            started_at=run_started,
            adapter_version=ADAPTER_VERSION,
            provider_schema_version=PROVIDER_SCHEMA_VERSION,
        )
        try:
            templates, folders, routines, workouts, pages = self.client.full_import_payload()
            self._validate_references(templates, folders, routines, workouts)
            with transaction.atomic():
                IncrementalSyncService._assert_lock(account)
                item_counts = self.repository.persist_full_import(
                    account,
                    templates=templates,
                    folders=folders,
                    routines=routines,
                    workouts=workouts,
                    synced_at=run_started,
                    provider_schema_version=PROVIDER_SCHEMA_VERSION,
                )
                self.persist_snapshots(account, run_started)
                removed_at = timezone.now()
                item_counts['removed'] = sum([
                    self.repository.mark_missing_inactive(ExerciseTemplate, account, {dto.external_id for dto in templates}, removed_at),
                    self.repository.mark_missing_inactive(RoutineFolder, account, {dto.external_id for dto in folders}, removed_at),
                    self.repository.mark_missing_inactive(Routine, account, {dto.external_id for dto in routines}, removed_at),
                    self.repository.mark_missing_inactive(Workout, account, {dto.external_id for dto in workouts}, removed_at),
                ])
                SyncCursor.objects.get_or_create(
                    hevy_account=account,
                    stream_name=WORKOUT_EVENT_STREAM,
                    defaults={'confirmed_at': run_started},
                )
                finished = timezone.now()
                SyncRun.objects.filter(pk=run.pk).update(
                    state=SyncRun.State.SUCCEEDED,
                    finished_at=finished,
                    duration_ms=int((finished - run_started).total_seconds() * 1000),
                    item_counts=item_counts,
                    page_counts=pages,
                    retry_count=self.client.retry_count,
                )
                IntegrationState.objects.filter(hevy_account=account).update(
                    status=IntegrationState.Status.CONNECTED,
                    last_success_at=finished,
                    last_full_refresh_at=finished,
                    last_plans_at=finished,
                    last_catalog_at=finished,
                    is_stale=False,
                )
            return SyncRun.objects.get(pk=run.pk)
        except (DatabaseError, HevyError, ValueError, KeyError) as error:
            finished = timezone.now()
            if isinstance(error, HevyError):
                code = error.code
            elif isinstance(error, DatabaseError):
                code = 'DATABASE_ERROR'
            else:
                code = 'REFERENCE_MISSING'
            message = 'Database persistence failed.' if isinstance(error, DatabaseError) else str(error)
            SyncRun.objects.filter(pk=run.pk).update(
                state=SyncRun.State.FAILED,
                finished_at=finished,
                duration_ms=int((finished - run_started).total_seconds() * 1000),
                retry_count=self.client.retry_count,
                error_code=code,
                sanitized_error=message[:500],
            )
            IntegrationState.objects.filter(hevy_account=account).update(
                status=IntegrationState.Status.ERROR,
                is_stale=True,
            )
            raise
        finally:
            IncrementalSyncService._release_lock(account)

    def persist_snapshots(self, account, synced_at):
        from integrations.dtos import payload_hash
        for resource, pages in getattr(self.client, 'captured_pages', {}).items():
            if resource == 'workouts':
                continue
            ProviderSnapshot.objects.update_or_create(
                hevy_account=account, resource=resource,
                defaults={'pages': pages, 'source_hash': payload_hash(pages), 'synced_at': synced_at},
            )

    @staticmethod
    def _validate_references(templates, folders, routines, workouts) -> None:
        template_ids = {dto.external_id for dto in templates}
        folder_ids = {dto.external_id for dto in folders}
        routine_ids = {dto.external_id for dto in routines}
        if len(template_ids) != len(templates) or len(folder_ids) != len(folders) or len(routine_ids) != len(routines):
            raise ValueError('A collection contains duplicate external IDs.')
        if len({dto.external_id for dto in workouts}) != len(workouts):
            raise ValueError('A collection contains duplicate external IDs.')
        for routine in routines:
            if routine.folder_id is not None and routine.folder_id not in folder_ids:
                raise ValueError('Routine refers to an unavailable folder.')
            if any(exercise.template_id not in template_ids for exercise in routine.exercises):
                raise ValueError('Routine refers to an unavailable exercise template.')
            if len({exercise.position for exercise in routine.exercises}) != len(routine.exercises):
                raise ValueError('Routine contains duplicate exercise positions.')
            for exercise in routine.exercises:
                if len({set_dto.position for set_dto in exercise.sets}) != len(exercise.sets):
                    raise ValueError('Routine contains duplicate set positions.')
        for workout in workouts:
            if workout.routine_id is not None and workout.routine_id not in routine_ids:
                raise ValueError('Workout refers to an unavailable routine.')
            if any(exercise.template_id not in template_ids for exercise in workout.exercises):
                raise ValueError('Workout refers to an unavailable exercise template.')
            if len({exercise.position for exercise in workout.exercises}) != len(workout.exercises):
                raise ValueError('Workout contains duplicate exercise positions.')
            for exercise in workout.exercises:
                if len({set_dto.position for set_dto in exercise.sets}) != len(exercise.sets):
                    raise ValueError('Workout contains duplicate set positions.')


class PlanRefreshService(FullImportService):
    def run(self, user, *, trigger=SyncRun.Trigger.COMMAND) -> SyncRun:
        run_started = timezone.now()
        account = self.validate_account(user)
        IncrementalSyncService._acquire_lock(account)
        run = SyncRun.objects.create(
            hevy_account=account,
            mode=SyncRun.Mode.PLANS,
            trigger=trigger,
            state=SyncRun.State.RUNNING,
            started_at=run_started,
            adapter_version=ADAPTER_VERSION,
            provider_schema_version=PROVIDER_SCHEMA_VERSION,
        )
        try:
            templates, folders, routines, pages = self.client.plans_payload()
            self._validate_references(templates, folders, routines, ())
            with transaction.atomic():
                IncrementalSyncService._assert_lock(account)
                counts = self.repository.persist_full_import(
                    account,
                    templates=templates,
                    folders=folders,
                    routines=routines,
                    workouts=(),
                    synced_at=run_started,
                    provider_schema_version=PROVIDER_SCHEMA_VERSION,
                )
                self.persist_snapshots(account, run_started)
                removed_at = timezone.now()
                counts['removed'] = sum([
                    self.repository.mark_missing_inactive(ExerciseTemplate, account, {dto.external_id for dto in templates}, removed_at),
                    self.repository.mark_missing_inactive(RoutineFolder, account, {dto.external_id for dto in folders}, removed_at),
                    self.repository.mark_missing_inactive(Routine, account, {dto.external_id for dto in routines}, removed_at),
                ])
                finished = timezone.now()
                SyncRun.objects.filter(pk=run.pk).update(
                    state=SyncRun.State.SUCCEEDED,
                    finished_at=finished,
                    duration_ms=int((finished - run_started).total_seconds() * 1000),
                    item_counts=counts,
                    page_counts=pages,
                    retry_count=self.client.retry_count,
                )
                IntegrationState.objects.filter(hevy_account=account).update(
                    status=IntegrationState.Status.CONNECTED,
                    last_success_at=finished,
                    last_plans_at=finished,

                    is_stale=False,
                )
                if getattr(self.client, 'cached_catalog_pages', None) is None:
                    IntegrationState.objects.filter(hevy_account=account).update(last_catalog_at=finished)
            return SyncRun.objects.get(pk=run.pk)
        except (DatabaseError, HevyError, ValueError, KeyError) as error:
            finished = timezone.now()
            code = error.code if isinstance(error, HevyError) else (
                'DATABASE_ERROR' if isinstance(error, DatabaseError) else 'REFERENCE_MISSING'
            )
            SyncRun.objects.filter(pk=run.pk).update(
                state=SyncRun.State.FAILED,
                finished_at=finished,
                duration_ms=int((finished - run_started).total_seconds() * 1000),
                retry_count=self.client.retry_count,
                error_code=code,
                sanitized_error=(str(error) if not isinstance(error, DatabaseError) else 'Database persistence failed.')[:500],
            )
            IntegrationState.objects.filter(hevy_account=account).update(
                status=IntegrationState.Status.ERROR,
                is_stale=True,
            )
            raise
        finally:
            IncrementalSyncService._release_lock(account)


class IncrementalSyncService:
    def __init__(self, client: HevyClient, repository: TrainingRepository | None = None):
        self.client = client
        self.repository = repository or TrainingRepository()

    def run(
        self,
        user,
        *,
        prior_run: SyncRun | None = None,
        trigger=None,
    ) -> SyncRun:
        account = HevyAccount.objects.get(user=user)
        cursor = SyncCursor.objects.filter(
            hevy_account=account,
            stream_name=WORKOUT_EVENT_STREAM,
        ).first()
        if cursor is None:
            raise HevyError(
                'SYNC_NOT_INITIALIZED',
                'Execute a complete refresh before incremental synchronization.',
            )
        if prior_run is not None and (
            prior_run.hevy_account_id != account.id
            or prior_run.state not in {SyncRun.State.FAILED, SyncRun.State.PARTIAL}
        ):
            raise ValueError('Retry source is not eligible.')
        self._acquire_lock(account)
        run_started = timezone.now()
        run = None
        try:
            run = SyncRun.objects.create(
                hevy_account=account,
                mode=SyncRun.Mode.INCREMENTAL,
                trigger=trigger or (SyncRun.Trigger.RETRY if prior_run else SyncRun.Trigger.COMMAND),
                state=SyncRun.State.RUNNING,
                started_at=run_started,
                cursor_before=cursor.confirmed_at,
                high_water_at=run_started,
                adapter_version=ADAPTER_VERSION,
                provider_schema_version=PROVIDER_SCHEMA_VERSION,
                prior_run=prior_run,
            )
            fetched_events = self.client.workout_events(
                cursor.confirmed_at - timedelta(seconds=cursor.overlap_seconds)
            )
            events = tuple(event for event in fetched_events.items if event.occurred_at <= run_started)
            ordered_events = self._deduplicate_events(events)
            workouts = []
            deletions = []
            for event in ordered_events:
                if event.event_type == 'deleted':
                    deletions.append(event)
                else:
                    workouts.append(
                        self.client.get_workout(event.external_id)
                        if event.needs_repair else event.workout
                    )
            with transaction.atomic():
                self._assert_lock(account)
                locked_cursor = SyncCursor.objects.select_for_update().get(pk=cursor.pk)
                counts = self.repository.persist_incremental_workouts(
                    account,
                    workouts,
                    synced_at=run_started,
                    provider_schema_version=PROVIDER_SCHEMA_VERSION,
                )
                counts['removed'] = sum(
                    self.repository.mark_workout_removed(account, event.external_id, event.occurred_at)
                    for event in deletions
                )
                counts['ignored'] = len(fetched_events.items) - len(ordered_events) + len(deletions) - counts['removed']
                counts['invalid'] = 0
                locked_cursor.confirmed_at = run_started
                locked_cursor.save(update_fields=['confirmed_at', 'updated_at'])
                finished = timezone.now()
                SyncRun.objects.filter(pk=run.pk).update(
                    state=SyncRun.State.SUCCEEDED,
                    finished_at=finished,
                    duration_ms=int((finished - run_started).total_seconds() * 1000),
                    item_counts=counts,
                    page_counts={'workout_events': {'requested': fetched_events.requested_pages, 'received': fetched_events.received_pages}},
                    retry_count=self.client.retry_count,
                    cursor_after=run_started,
                )
                IntegrationState.objects.filter(hevy_account=account).update(
                    status=IntegrationState.Status.CONNECTED,
                    last_success_at=finished,
                    last_incremental_run_at=finished,
                    is_stale=False,
                )
            return SyncRun.objects.get(pk=run.pk)
        except (DatabaseError, HevyError, ValueError, KeyError) as error:
            if run is not None:
                finished = timezone.now()
                code = error.code if isinstance(error, HevyError) else (
                    'DATABASE_ERROR' if isinstance(error, DatabaseError) else 'REFERENCE_MISSING'
                )
                state = SyncRun.State.PARTIAL if code == 'PAGINATION_INVALID' else SyncRun.State.FAILED
                SyncRun.objects.filter(pk=run.pk).update(
                    state=state,
                    finished_at=finished,
                    duration_ms=int((finished - run_started).total_seconds() * 1000),
                    retry_count=self.client.retry_count,
                    error_code=code,
                    sanitized_error=(str(error) if not isinstance(error, DatabaseError) else 'Database persistence failed.')[:500],
                )
                IntegrationState.objects.filter(hevy_account=account).update(
                    status=IntegrationState.Status.ERROR,
                    is_stale=True,
                )
            raise
        finally:
            self._release_lock(account)

    @staticmethod
    def _deduplicate_events(events):
        unique = {}
        for event in events:
            identity = (event.event_type, event.external_id, event.occurred_at)
            unique[identity] = event
        return sorted(
            unique.values(),
            key=lambda event: (
                event.occurred_at,
                event.external_id,
                1 if event.event_type == 'deleted' else 0,
            ),
        )

    @staticmethod
    def _acquire_lock(account: HevyAccount) -> None:
        try:
            with transaction.atomic():
                now = timezone.now()
                stale_before = now - timedelta(seconds=settings.SYNC_LOCK_STALE_SECONDS)
                lock, _ = SyncLock.objects.get_or_create(hevy_account=account)
                stale = lock.is_active and (
                    lock.acquired_at is None or lock.acquired_at < stale_before
                )
                if stale:
                    from planning.models import RoutineProposal
                    for proposal in RoutineProposal.objects.filter(account=account, state='submitting'):
                        proposal.state = 'unknown'
                        proposal.local_refresh_pending = any(item['state'] == 'succeeded' for item in proposal.results)
                        proposal.results = [{**item, 'state': 'unknown'} if item['state'] == 'submitting' else item for item in proposal.results]
                        proposal.save(update_fields=['state', 'results', 'local_refresh_pending'])
                    SyncRun.objects.filter(
                        hevy_account=account,
                        state=SyncRun.State.RUNNING,
                    ).filter(
                        Q(started_at__lt=stale_before) | Q(started_at__isnull=True)
                    ).update(
                        state=SyncRun.State.FAILED,
                        finished_at=now,
                        error_code='SYNC_INTERRUPTED',
                        sanitized_error='A stale synchronization lock was recovered.',
                    )
                if not SyncLock.objects.filter(pk=lock.pk).filter(
                    Q(is_active=False)
                    | Q(acquired_at__lt=stale_before)
                    | Q(acquired_at__isnull=True)
                ).update(
                    is_active=True,
                    acquired_at=now,
                ):
                    raise HevyError('SYNC_IN_PROGRESS', 'A workout synchronization is already running.')
                account._sync_lock_acquired_at = now
        except IntegrityError as error:
            raise HevyError('SYNC_IN_PROGRESS', 'A workout synchronization is already running.') from error

    @staticmethod
    def _assert_lock(account: HevyAccount) -> None:
        token = getattr(account, '_sync_lock_acquired_at', None)
        if token is None or not SyncLock.objects.filter(hevy_account=account, is_active=True, acquired_at=token).exists():
            raise HevyError('SYNC_LOCK_LOST', 'The execution lock expired; local publication was cancelled.')

    @staticmethod
    def _release_lock(account: HevyAccount) -> None:
        SyncLock.objects.filter(hevy_account=account, acquired_at=getattr(account, '_sync_lock_acquired_at', None)).update(
            is_active=False,
            acquired_at=None,
        )
