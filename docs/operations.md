# Operations · 0.2.0

## Clean installation and reset

Install Python 3.12+ and uv. `uv sync --locked` includes the developer tools; use `uv sync --locked --no-dev` for runtime only. No Node is needed to run the app. `uv run python scripts/init_local.py` creates `.env` with mode 0600 and independent random Django/Fernet keys, without printing them. It refuses to overwrite existing configuration. Run `manage.py migrate`, then `manage.py runserver 127.0.0.1:8000`.

The legacy 0.1.x → 0.2.0 transition requires a new database. For a legacy installation: stop Django, preserve the old SQLite database and its configuration, then select a new empty path using `TUXEDO_DATA_DIR=var/private/v020` (remove/replace an old `TUXEDO_FITNESS_DB` override). Add a newly generated Fernet key to HEVY_ENCRYPTION_KEYS using a private editor. Run migrations and recreate local accounts. Do not copy legacy tables into the new database. Old source and database backups provide the rollback path.

`TUXEDO_ENV_FILE` selects a private configuration file. Process environment overrides that file; never source an untrusted .env in a shell. Local defaults bind loopback. Production uses HTTPS, secure cookies, explicit hosts/origins, a reverse proxy serving collected static files and a WSGI server. Keep CSRF/CSP protections enabled. No email password-reset service is configured; owners can use `manage.py changepassword USER`. `ALLOW_SIGNUPS=False` disables new registrations without disabling login.

## Credential lifecycle

Connect in Hevy connection after login. The API key is masked on input, validated server-side, encrypted and never displayed again. It survives logout/restart. Disconnect removes the stored credential, preserving local training records. Replacing it requires the same remote identity. Keep installation keys separate from SQLite and SECRET_KEY.

For rotation, securely generate a fresh Fernet key; place it first in the comma-separated `HEVY_ENCRYPTION_KEYS`, followed by old keys. Restart processes and run:

```bash
uv run python manage.py rotate_hevy_keys
```

The command re-encrypts stored credentials atomically and does not print secrets. Verify the connection in an isolated restore before removing old keys. Historical backups still require their original encryption keys. Never remove keys needed by retained backups. Lost keys cannot decrypt old credentials; reconnect to the same account using a valid key if necessary. [Fernet/MultiFernet reference](https://cryptography.io/en/latest/fernet/).

## Backup and restore

Before running these commands, set `TUXEDO_FITNESS_BACKUP_DIR` in the private environment to an absolute directory outside the source checkout. The application deliberately requires an explicit destination; it does not silently put backups beside the live database.

```bash
uv run python manage.py backup_database
uv run python manage.py check_database
uv run python scripts/rehearse_restore.py
```

The SQLite online-backup API produces a consistent copy with integrity/foreign-key checks; do not copy a running WAL database using a plain file copy. Backups use owner-only storage. Choose an external private backup destination through `TUXEDO_FITNESS_BACKUP_DIR` and separately back up the private installation key ring. Database encryption is limited to provider credentials; training/profile/prompt data remains readable to the installation owner and should be protected by filesystem/full-disk encryption as needed.

To restore, stop Django, preserve the current DB, restore the verified SQLite backup to a new path and supply the corresponding installation key ring. Run `check_database --database PATH`. Start a disposable instance using a private TUXEDO_ENV_FILE and that restored DB, verify login/local data and decryptability, then switch the production path. Never point a preview/E2E runner at a real backup. The rehearsal script checks SQLite integrity; credential decryption/rotation is additionally covered by synthetic tests and should be rehearsed with the owner's key backup.

## Sync, recovery and maintenance

```bash
uv run python manage.py sync_hevy --username USER --validate-only
uv run python manage.py sync_hevy --username USER --mode=full --confirm-full-refresh
uv run python manage.py sync_hevy --username USER --mode=incremental
uv run python manage.py sync_hevy --username USER --mode=plans
uv run python manage.py prune_runtime_data
```

The CLI uses that user's encrypted stored credential. First import must be full. The browser automatically reserves 15-minute retry intervals; manual refresh remains available. Incomplete collections preserve the prior cursor/base. A stale lock is recovered after SYNC_LOCK_STALE_SECONDS (default six hours); stop the original worker before forcing an earlier recovery. Unknown writes require checking Hevy and synchronizing, never blind resubmission. Partial batches retain their successful operations and do not roll back remotely. After a successful remote write with failed local refresh, refresh plans rather than applying the write again.

Routine JSON preview has a 15-minute expiry and single consumption. Saved prompt generations are immutable and deletable by their owner. Synchronization never edits an old prompt. Research datasets are not used at runtime.


## Updating an existing 0.2.0 installation

This revision preserves the database and key ring. Back up both before updating;
then run `uv sync --locked`, `uv run python manage.py migrate` and
`uv run python manage.py translate_exercises`. Restart the application.
Do not run the new-installation initializer or reset the database.
If a production web server serves `STATIC_ROOT`, run `uv run python manage.py collectstatic --noinput` after updating the compiled assets. Development `runserver` serves the versioned checkout assets directly.

`translate_exercises --check` performs no writes and fails if known display
fields need refreshing or unknown standard exercises remain. The command
updates only translation fields, skips custom exercises, and never calls Hevy.
Unknown IDs/titles require a reviewed catalogue addition. The catalogue contains
only standard provider IDs and titles, with no account or workout records.

## Interface preview on GitHub Pages

An administrator must select **Settings → Pages → Build and deployment →
Source: GitHub Actions**. The existing workflow publishes only `preview/` from
`main`, or through its manual dispatch. Review the `github-pages` environment
and permit deployments from `main`. A private repository requires an eligible
GitHub plan; do not change repository visibility to work around permissions.

`configure-pages` cannot create the site using the ordinary `GITHUB_TOKEN`.
Do not add `enablement: true` without the administrative token it requires.
An HTTP 404 may mean an absent site or insufficient access. Configure the site
with an authenticated administrator before rerunning the workflow.

After a successful run, verify the emitted Pages URL, both languages and all
images. Do not consider local workflow edits evidence of a remote deployment.
