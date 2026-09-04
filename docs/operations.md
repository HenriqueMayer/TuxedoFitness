# Local operations

## Native installation

Install from the lockfiles and keep the environment file private:

```bash
uv python install 3.12
uv venv --python 3.12 .venv
uv sync --locked
npm ci
npm run build
install -m 600 .env.example .env
```

Generate a Django secret with the following command, then paste it into
`SECRET_KEY` in `.env` using a local editor. Do not `source` the file.

```bash
uv run python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Set the rotated Hevy credential only in `HEVY_API_KEY`. Process variables take
priority over `.env`; `TUXEDO_ENV_FILE` selects another environment file.

Initialize the local database and start it on loopback:

```bash
uv run python manage.py migrate
uv run python manage.py check
uv run python manage.py runserver 127.0.0.1:8000
```

Open `http://127.0.0.1:8000/`. Signup is available from the landing and login
pages by default; set `ALLOW_SIGNUPS=False` to close new registration without
disabling login. Alternatively, create the first owner with
`uv run python manage.py create_owner your-username`. The command prompts for a password and is
intended only for an empty database. For
unattended local initialization, expose `TUXEDO_OWNER_PASSWORD` only to that
process and pass `--no-input`. Recover a forgotten password locally with:

```bash
uv run python manage.py changepassword your-username
```

The MVP has no email recovery flow or application-level login throttler. Keep
the service on the intended owner network; if it is exposed, enforce request
rate limits at the reverse proxy in addition to HTTPS.

The private database defaults to `var/private/tuxedo-fitness.sqlite3`.
`TUXEDO_DATA_DIR` changes the directory; `TUXEDO_FITNESS_DB` selects an exact
file. Restrict private paths to the owner account.

## Quality pipeline

```bash
uv lock --check
uv sync --locked
uv run python scripts/check_version.py
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
uv run coverage erase
uv run coverage run manage.py test
uv run coverage report --fail-under=80
uv run coverage report --include='integrations/*' --fail-under=90
uv run coverage report --include='analytics/*' --fail-under=90
uv run ruff check .
uv run python scripts/security/scan_secrets.py
uv run python scripts/security/scan_secrets.py --history
npm ci
npm run build
npm audit --audit-level=high
npm run test:e2e
git diff --check
```

All tests use synthetic local data and mocked Hevy transports. The secret scan
checks the tracked tree and fails for credential-like assignments or tracked
personal-fixture paths.

## Read-only synchronization

```bash
uv run python manage.py sync_hevy --validate-only --username your-username
uv run python manage.py sync_hevy --mode=full --confirm-full-refresh --username your-username
uv run python manage.py sync_hevy --mode=incremental --username your-username
uv run python manage.py sync_hevy --mode=plans --username your-username
```

The command reports a sanitized run summary only after commit. Failures leave
the cursor unchanged. Run a complete import before the first incremental run.
A lock older than `SYNC_LOCK_STALE_SECONDS` is recovered and its interrupted
run is audited as failed. Exit codes are 2 for configuration/authentication, 3 for
transient provider failures, 4 for payload/validation/partial failures, 5 for a
writer conflict, and 6 for database failure.

## Scheduling

Cron can run the incremental command every 30 minutes and plan refresh weekly:

```cron
*/30 * * * * cd /path/to/TuxedoFitness && /path/to/uv run python manage.py sync_hevy --mode=incremental --username=your-username
15 3 * * 1 cd /path/to/TuxedoFitness && /path/to/uv run python manage.py sync_hevy --mode=plans --username=your-username
30 3 * * * cd /path/to/TuxedoFitness && /path/to/uv run python manage.py prune_runtime_data
```

Equivalent systemd service:

```ini
[Unit]
Description=Tuxedo Fitness incremental Hevy synchronization
After=network-online.target

[Service]
Type=oneshot
User=tuxedofitness
WorkingDirectory=/srv/TuxedoFitness
EnvironmentFile=/srv/TuxedoFitness/.env
ExecStart=/usr/local/bin/uv run python manage.py sync_hevy --mode=incremental --username=your-username
```

Timer:

```ini
[Unit]
Description=Run Tuxedo Fitness synchronization

[Timer]
OnBootSec=5min
OnUnitActiveSec=30min
Persistent=true

[Install]
WantedBy=timers.target
```

The environment file must be readable only by the service account. Never put
the API key in a unit, timer, cron line, or shell history.

## Backup, verification, and restore

Configure an absolute backup directory outside the checkout:

```bash
export TUXEDO_FITNESS_BACKUP_DIR=/absolute/path/to/tuxedo-fitness-backups
mkdir -p "$TUXEDO_FITNESS_BACKUP_DIR"
chmod 700 "$TUXEDO_FITNESS_BACKUP_DIR"
uv run python manage.py backup_database
```

The command uses SQLite's online backup API, writes a mode-`0600` file, and
requires `integrity_check=ok` plus an empty foreign-key check. Settings deletion
uses the same verified backup gate. Validate any selected database without
changing it:

```bash
uv run python manage.py check_database
uv run python manage.py check_database --database /absolute/path/to/selected-backup.sqlite3
```

The non-destructive rehearsal creates a new verified backup, copies it to an
isolated temporary directory, validates the copy, and removes only that
temporary restored copy:

```bash
uv run python scripts/rehearse_restore.py
```

For a real restore, stop the web process and schedulers, preserve the current
database as a rollback copy, choose one exact backup, and then:

```bash
cp /absolute/path/to/selected-backup.sqlite3 "$TUXEDO_FITNESS_DB"
chmod 600 "$TUXEDO_FITNESS_DB"
uv run python manage.py migrate
uv run python manage.py check
uv run python manage.py check_database
```

Restart only after both checks pass. Never restore over a running writer.

## Optional Docker Compose topology

Container packaging is optional and does not change the architecture. A
Compose deployment has one application service, no database service, and no
queue. Its equivalent shape is:

```yaml
services:
  app:
    build: .
    command: uv run gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 1 --threads 2
    env_file: .env
    volumes:
      - fitness-data:/app/var/private
      - fitness-backups:/backups
    healthcheck:
      test: ["CMD", "curl", "--fail", "http://127.0.0.1:8000/ready/"]
      interval: 30s
      timeout: 5s
      retries: 3

volumes:
  fitness-data:
  fitness-backups:
```

The operator-provided image must run `uv sync --locked`, build static assets,
and never copy `.env` or runtime data. Keep one application replica because
SQLite has a one-writer deployment contract.

## Optional single-instance VPS

Use one service account, one local SQLite volume, and one Gunicorn instance:

```bash
uv run python manage.py collectstatic --noinput
uv run gunicorn core.wsgi:application --bind 127.0.0.1:8000 --workers 1 --threads 2
```

Terminate HTTPS at a local reverse proxy. Set `DEBUG=False`, `HTTPS=True`, an
exact `ALLOWED_HOSTS`, and exact HTTPS origins in `CSRF_TRUSTED_ORIGINS`.
Restrict the proxy to the intended owner network or access layer, serve
`STATIC_ROOT`, schedule verified off-checkout backups, and rehearse restores.
Do not add replicas, shared-network SQLite, Redis, Celery, or an internal queue.
SQLite WAL permits reads while one synchronization writer is active; two
threads prevent that slow request from occupying the only request slot. Prefer
the management command for the first large import and configure the reverse
proxy timeout accordingly.
