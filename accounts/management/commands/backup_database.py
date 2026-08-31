from django.core.management.base import BaseCommand, CommandError

from accounts.services import BackupError, create_verified_backup


class Command(BaseCommand):
    help = 'Create and verify a private SQLite backup.'

    def handle(self, *args, **options):
        try:
            backup = create_verified_backup()
        except BackupError as error:
            raise CommandError(f'{error.code}: {error}', returncode=6) from error
        self.stdout.write(self.style.SUCCESS(f'Backup verified: {backup}'))
