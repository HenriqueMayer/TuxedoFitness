import os
import stat

from django.conf import settings
from django.core.checks import Error, register


@register()
def private_environment_file_permissions(app_configs, **kwargs):
    """Reject an environment file readable or writable by group/others."""

    if os.name != 'posix' or not settings.ENV_FILE.exists():
        return []
    mode = stat.S_IMODE(settings.ENV_FILE.stat().st_mode)
    if mode & 0o077:
        return [Error(
            f'{settings.ENV_FILE} must be accessible only by its owner (mode 0600).',
            hint=f'Run: chmod 600 {settings.ENV_FILE}',
            id='core.E001',
        )]
    return []
