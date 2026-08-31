<p align="center">
  <img src="static/brand/tuxedo-fitness-emblem-128.png" width="96" height="96" alt="Tuxedo Fitness emblem">
</p>

<h1 align="center">Tuxedo Fitness</h1>

<p align="center">Local-first, self-hosted training analytics with an owner-controlled SQLite record.</p>

<p align="center">
  <img alt="Version 0.1.0" src="https://img.shields.io/badge/version-0.1.0-B88A59">
  <img alt="Python 3.12+" src="https://img.shields.io/badge/python-3.12%2B-1A2E26">
  <img alt="License PolyForm Noncommercial" src="https://img.shields.io/badge/license-PolyForm%20Noncommercial-8A5A2F">
</p>

Tuxedo Fitness imports Hevy data through a backend-only, read-only adapter,
normalizes it locally, and calculates deterministic training metrics. The web
application is server-rendered Django with progressive HTMX navigation,
accessible SVG charts, equivalent tables, and no runtime CDN.

This is a personal application, not a hosted service, public API, medical
product, or official Hevy product.

## Current capabilities

- Native Django login and explicitly controlled local signup.
- Full, plan-only, and incremental workout synchronization with audit runs,
  cursor safety, retries, and rollback on invalid provider data.
- Workout history, exercise and routine views, period filters, compatible
  volume/RPE/record/e1RM analytics, and set-level CSV export.
- Local preferences, retention cleanup, verified SQLite backup, integrity
  checks, and isolated restore rehearsal.
- Strict same-origin CSP, backend-only credentials, synthetic tests, dependency
  audits, and desktop/tablet/mobile browser coverage.

Advanced overview, exercise-history, and modality presentation is planned for
v0.2.0. The exact implemented/planned split is recorded in the
[Product Requirements Document](docs/ProductRequirementsDocument.md).

## Quick start

Requirements: Python 3.12, [uv](https://docs.astral.sh/uv/), Node.js 20, npm,
and a Hevy Pro API credential for synchronization.

```bash
git clone git@github.com:HenriqueMayer/TuxedoFitness.git
cd TuxedoFitness
uv sync --locked
npm ci
npm run build
install -m 600 .env.example .env
```

Generate a Django key and place it in `SECRET_KEY` in `.env` using a local
editor. Never source the file or paste secrets into commands, issues, or logs.

```bash
uv run python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
uv run python manage.py migrate
uv run python manage.py create_owner your-username
uv run python manage.py runserver 127.0.0.1:8000
```

Open `http://127.0.0.1:8000/`. Signup is closed by default. Set
`ALLOW_SIGNUPS=True` only while intentionally accepting another local account;
existing login remains available when signup is disabled.

Set `HEVY_API_KEY` only in the backend environment, then validate and perform
the first confirmed import:

```bash
uv run python manage.py sync_hevy --validate-only --username your-username
uv run python manage.py sync_hevy --mode=full --confirm-full-refresh --username your-username
```

See [operations](docs/operations.md) for incremental sync, scheduling, backups,
restore, HTTPS, and supported single-instance deployment.

## Privacy and architecture

- `.env`, SQLite, backups, exports, diagnostics, and private provider snapshots
  are excluded from Git and must remain owner-readable only.
- Browser requests never contact Hevy and no credential is persisted in the
  database, HTML, JavaScript, URL, log, fixture, or export.
- SQLite supports one application writer. Shared-network SQLite, multiple
  replicas, queues, and distributed infrastructure are unsupported.
- Research under `research/` is provenance for a future phase and is not loaded
  by the MVP runtime.

## Development

The complete quality pipeline is in [testing](docs/testing.md). The short path
is:

```bash
uv lock --check
uv run python scripts/check_version.py
uv run python manage.py check
uv run python manage.py test
uv run ruff check .
uv run python scripts/security/scan_secrets.py
npm ci
npm run build
npm run test:e2e
```

Contributions must use synthetic data and preserve the product boundaries in
[CONTRIBUTING.md](CONTRIBUTING.md). Security reports belong in GitHub private
vulnerability reporting, not public issues.

## License

Copyright 2026 Henrique Mayer. Licensed under the
[PolyForm Noncommercial License 1.0.0](LICENSE). Personal and noncommercial use
is permitted; commercial use is not. Bundled dependencies retain the licenses
listed in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
