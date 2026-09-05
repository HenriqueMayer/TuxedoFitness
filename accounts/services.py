from __future__ import annotations

import os
import sqlite3
from datetime import timedelta
from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.db import connection
from django.utils import timezone


class BackupError(RuntimeError):
    code = 'BACKUP_INVALID'


def sqlite_checks(database: Path | str) -> tuple[str, tuple[tuple, ...]]:
    database = Path(database)
    if not database.is_file():
        raise BackupError('The SQLite database does not exist.')
    try:
        with sqlite3.connect(database) as checked:
            integrity = checked.execute('PRAGMA integrity_check').fetchone()[0]
            foreign_keys = tuple(checked.execute('PRAGMA foreign_key_check').fetchall())
    except (OSError, sqlite3.Error) as error:
        raise BackupError('SQLite validation could not be completed.') from error
    return integrity, foreign_keys


def _backup_directory() -> Path:
    configured = os.environ.get('TUXEDO_FITNESS_BACKUP_DIR', '').strip()
    if not configured:
        raise BackupError('Configure TUXEDO_FITNESS_BACKUP_DIR before creating a backup.')
    path = Path(configured).expanduser()
    if not path.is_absolute():
        raise BackupError('The backup directory must be an absolute path.')
    try:
        path.relative_to(settings.BASE_DIR)
    except ValueError:
        return path
    raise BackupError('The backup directory must remain outside the source checkout.')


def create_verified_backup() -> Path:
    database_name = str(settings.DATABASES['default']['NAME'])
    database = Path(database_name)
    memory_database = database_name == ':memory:' or database_name.startswith('file:')
    if not database.is_file() and not memory_database:
        raise BackupError('The configured SQLite database does not exist.')
    directory = _backup_directory()
    source_context = None
    close_source = False
    try:
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(directory, 0o700)
        stamp = timezone.localtime(timezone.now()).strftime('%Y%m%d-%H%M%S')
        target = directory / f'tuxedo-fitness-{stamp}-{uuid4().hex[:8]}.sqlite3'
        if database.is_file():
            source_context = sqlite3.connect(database)
            close_source = True
        else:
            connection.ensure_connection()
            source_context = connection.connection
        with sqlite3.connect(target) as destination:
            source_context.backup(destination)
        try:
            integrity, foreign_keys = sqlite_checks(target)
        except BackupError:
            target.unlink(missing_ok=True)
            raise
        if integrity != 'ok' or foreign_keys:
            target.unlink(missing_ok=True)
            raise BackupError('The backup failed SQLite validation.')
        os.chmod(target, 0o600)
        return target
    except BackupError:
        raise
    except (OSError, sqlite3.Error) as error:
        raise BackupError('The local backup could not be created.') from error
    finally:
        if close_source and source_context is not None:
            source_context.close()


def prune_private_snapshots(retention_days: int, *, now=None) -> int:
    directory = settings.DATA_DIR / 'hevy-snapshots'
    if not directory.is_dir() or directory.is_symlink():
        return 0
    cutoff = (now or timezone.now()).timestamp() - retention_days * 86400
    removed = 0
    for path in directory.iterdir():
        if path.suffix != '.json' or path.is_symlink() or not path.is_file():
            continue
        if retention_days == 0 or path.stat().st_mtime < cutoff:
            path.unlink(missing_ok=True)
            removed += 1
    return removed


def prune_sync_runs(*, now=None) -> int:
    from integrations.models import HevyAccount, SyncRun

    cutoff = (now or timezone.now()) - timedelta(days=180)
    removed = 0
    for account_id in HevyAccount.objects.values_list('pk', flat=True):
        protected = list(
            SyncRun.objects.filter(hevy_account_id=account_id)
            .order_by('-created_at')
            .values_list('pk', flat=True)[:20]
        )
        deleted, _ = SyncRun.objects.filter(
            hevy_account_id=account_id,
            created_at__lt=cutoff,
        ).exclude(pk__in=protected).delete()
        removed += deleted
    return removed
