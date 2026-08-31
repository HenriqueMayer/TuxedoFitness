from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError

from integrations.hevy import HevyClient, HevyError
from integrations.models import SyncRun
from integrations.services import (
    FullImportService,
    IncrementalSyncService,
    PlanRefreshService,
)


class Command(BaseCommand):
    help = 'Validate Hevy or run a read-only synchronization.'

    def add_arguments(self, parser):
        parser.add_argument('--username')
        parser.add_argument('--validate-only', action='store_true')
        parser.add_argument('--mode', choices=['full', 'incremental', 'plans'])
        parser.add_argument('--confirm-full-refresh', action='store_true')
        parser.add_argument('--retry-run')

    def handle(self, *args, **options):
        user = self._user(options['username'])
        if not options['validate_only'] and not options['mode']:
            raise CommandError('A synchronization mode is required.', returncode=2)
        if options['mode'] == 'full' and not options['confirm_full_refresh']:
            raise CommandError(
                'Full import requires --mode=full --confirm-full-refresh.',
                returncode=4,
            )
        if options['retry_run'] and options['mode'] != 'incremental':
            raise CommandError(
                '--retry-run is available only for incremental synchronization.',
                returncode=4,
            )
        try:
            client = HevyClient.from_environment()
            service = FullImportService(client)
            if options['validate_only']:
                account = service.validate_account(user)
                self.stdout.write(self.style.SUCCESS(f'Hevy account validated: {account.display_name}'))
                return
            if options['mode'] == 'full':
                run = service.run(user)
            elif options['mode'] == 'plans':
                run = PlanRefreshService(client).run(user)
            else:
                prior_run = self._retry_run(options['retry_run'])
                run = IncrementalSyncService(client).run(user, prior_run=prior_run)
        except (DatabaseError, HevyError, ValueError) as error:
            code = error.code if isinstance(error, HevyError) else 'SYNC_INVALID'
            if isinstance(error, DatabaseError):
                code = 'DATABASE_ERROR'
            returncode = self._returncode(code)
            message = 'Database persistence failed.' if isinstance(error, DatabaseError) else str(error)
            raise CommandError(f'{code}: {message}', returncode=returncode) from error
        self.stdout.write(self.style.SUCCESS(
            f'run={run.id} mode={run.mode} state={run.state} duration_ms={run.duration_ms} '
            f'pages={run.page_counts} counts={run.item_counts}'
        ))

    @staticmethod
    def _returncode(code):
        if code.startswith('CONFIG_') or code == 'AUTH_INVALID':
            return 2
        if code in {'HTTP_TIMEOUT', 'HTTP_TRANSIENT'}:
            return 3
        if code in {'SYNC_IN_PROGRESS'}:
            return 5
        if code in {'DATABASE_ERROR'}:
            return 6
        return 4

    @staticmethod
    def _retry_run(run_id):
        if not run_id:
            return None
        try:
            return SyncRun.objects.get(pk=run_id)
        except (SyncRun.DoesNotExist, ValidationError, ValueError) as error:
            raise CommandError('Retry source does not exist.', returncode=4) from error

    @staticmethod
    def _user(username):
        users = get_user_model().objects
        if username:
            try:
                return users.get(username=username)
            except get_user_model().DoesNotExist as error:
                raise CommandError('Configured user does not exist.', returncode=2) from error
        candidates = list(users.order_by('pk')[:2])
        if len(candidates) != 1:
            raise CommandError('Use --username when the local owner is ambiguous.', returncode=2)
        return candidates[0]
