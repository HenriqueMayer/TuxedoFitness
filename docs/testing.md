# Testing and release verification

All tests use synthetic users, credentials, provider payloads, and isolated
SQLite databases. No automated test calls Hevy.

## Python and coverage

```bash
uv lock --check
uv run python scripts/check_version.py
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
uv run coverage erase
uv run coverage run manage.py test
uv run coverage report --fail-under=80
uv run coverage report --include='integrations/*' --fail-under=90
uv run coverage report --include='analytics/*' --fail-under=90
uv run ruff check .
```

## Security and dependencies

```bash
uv run python scripts/security/scan_secrets.py
uv run python scripts/security/scan_secrets.py --history
uv export --locked --no-dev --format requirements-txt > /tmp/tuxedo-fitness-requirements.txt
uvx --from 'pip-audit>=2.7,<3' pip-audit --strict -r /tmp/tuxedo-fitness-requirements.txt
npm audit --audit-level=high
```

The history scan reports object IDs and paths but never prints suspected secret
values. It rejects environment files, private runtime paths, SQLite, old Hevy
exports, credential-like assignments, and personal fixture paths.

## Frontend and browser

```bash
npm ci
npm run build
git diff --exit-code -- static/css/app.css static/fonts/
node --check static/js/navigation.js
npm run test:e2e
```

Playwright runs serially against a unique disposable database and three
viewports: 1440×900, 768×1024, and 390×844. Console/CSP monitoring starts before
the first login navigation. Tests cover default signup visibility, the explicit
disabled-signup override, boosted
navigation continuity, SVG/table accessibility, idle/busy state, theme, mobile
focus/Escape, filters with and without JavaScript, empty periods, URL history,
and horizontal overflow.

## Release-only remote verification

After the sanitized history is pushed while the repository remains private,
clone the remote as a fresh mirror and rerun the history scanner. Confirm old
personal paths and object IDs are unavailable before changing repository
visibility. Any reachable old object blocks publication.
