#!/usr/bin/env python3
from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

import django

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()


def main() -> int:
    from accounts.services import BackupError, create_verified_backup, sqlite_checks

    try:
        backup = create_verified_backup()
        with tempfile.TemporaryDirectory(prefix='tuxedo-fitness-restore-') as directory:
            restored = Path(directory) / 'restored.sqlite3'
            shutil.copy2(backup, restored)
            integrity, foreign_keys = sqlite_checks(restored)
            if integrity != 'ok' or foreign_keys:
                raise BackupError('The isolated restored copy failed SQLite validation.')
    except BackupError as error:
        print(f'{error.code}: {error}')
        return 1
    print(f'Isolated restore rehearsal passed from {backup.name}.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
