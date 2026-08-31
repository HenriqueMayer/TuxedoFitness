#!/bin/sh
set -eu

database="${TUXEDO_FITNESS_DB:-var/private/e2e.sqlite3}"
mkdir -p "$(dirname "$database")"
rm -f "$database" "$database-shm" "$database-wal"
uv run python manage.py migrate --noinput
uv run python -m scripts.seed_e2e
exec uv run python manage.py runserver 127.0.0.1:8010 --noreload --insecure
