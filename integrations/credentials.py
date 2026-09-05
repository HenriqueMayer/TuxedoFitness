"""Encrypted, owner-scoped Hevy credentials. No secret is rendered back."""
from cryptography.fernet import Fernet, InvalidToken, MultiFernet
from django.conf import settings
from django.utils import timezone

from integrations.hevy import HevyError
from integrations.models import HevyAccount


def cipher():
    try:
        keys = [key.strip() for key in settings.HEVY_ENCRYPTION_KEYS.split(',') if key.strip()]
        if not keys:
            raise ValueError
        return MultiFernet([Fernet(key.encode('ascii')) for key in keys])
    except (ValueError, TypeError, UnicodeError):
        raise HevyError('ENCRYPTION_CONFIG', 'Configure HEVY_ENCRYPTION_KEYS for this installation.') from None


def key_for_user(user):
    account = HevyAccount.objects.filter(user=user).first()
    if account is None or not account.encrypted_api_key:
        return None
    try:
        return cipher().decrypt(account.encrypted_api_key.encode()).decode()
    except (InvalidToken, UnicodeError):
        raise HevyError('ENCRYPTION_KEY_UNAVAILABLE', 'Restore the installation encryption key or reconnect.') from None


class StoredCredentials:
    def put(self, request, api_key):
        encrypted = cipher().encrypt(api_key.strip().encode()).decode()
        HevyAccount.objects.filter(user=request.user).update(
            encrypted_api_key=encrypted, credential_updated_at=timezone.now(),
        )

    def get(self, request):
        return key_for_user(request.user)

    def delete(self, request):
        HevyAccount.objects.filter(user=request.user).update(encrypted_api_key='')

    def clear(self):
        """No process cache remains; retained for older test teardown."""


session_credentials = StoredCredentials()
