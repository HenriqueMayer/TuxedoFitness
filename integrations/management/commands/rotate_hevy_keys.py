from cryptography.fernet import InvalidToken
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from integrations.credentials import cipher
from integrations.models import HevyAccount


class Command(BaseCommand):
    help = 'Re-encrypt stored Hevy credentials with the first HEVY_ENCRYPTION_KEYS key.'

    @transaction.atomic
    def handle(self, *args, **options):
        encryption = cipher()
        count = 0
        try:
            for account in HevyAccount.objects.exclude(encrypted_api_key=''):
                account.encrypted_api_key = encryption.rotate(account.encrypted_api_key.encode()).decode()
                account.save(update_fields=['encrypted_api_key'])
                count += 1
        except InvalidToken:
            raise CommandError('Cannot decrypt all credentials; no rotation was committed.') from None
        self.stdout.write(f'Rotated {count} stored connection(s).')
