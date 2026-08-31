from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from accounts.services import BackupError, sqlite_checks


class Command(BaseCommand):
    help = 'Run SQLite integrity and foreign-key checks.'

    def add_arguments(self, parser):
        parser.add_argument('--database', type=Path)

    def handle(self, *args, **options):
        database = options['database'] or Path(settings.DATABASES['default']['NAME'])
        try:
            integrity, foreign_keys = sqlite_checks(database)
        except BackupError as error:
            raise CommandError(f'{error.code}: {error}', returncode=6) from error
        if integrity != 'ok' or foreign_keys:
            raise CommandError(
                f'DATABASE_INVALID: integrity={integrity}; foreign_key_violations={len(foreign_keys)}',
                returncode=6,
            )
        self.stdout.write(self.style.SUCCESS('integrity_check=ok'))
        self.stdout.write(self.style.SUCCESS('foreign_key_check=ok'))
