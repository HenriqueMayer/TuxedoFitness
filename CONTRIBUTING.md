# Contributing

Code and technical documentation use English; interface copy is EN/PT-BR gettext. Follow the [Tuxedo parity contract](docs/tuxedo-parity.md), view/service/template boundaries and owner-scoped queries. Use synthetic data and mocked providers in tests. A passing mocked write test is never evidence of a real Hevy write.

## Setup and checks

```bash
uv sync --locked
uv run python scripts/init_local.py  # new configuration only
uv run python manage.py migrate
npm ci
npm run build
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
uv run ruff check .
uv run coverage run manage.py test
uv run coverage report --fail-under=80
uv run python scripts/check_version.py
uv run python scripts/security/scan_secrets.py --history
git diff --check
```

Python tests live alongside apps; browser tests in tests/e2e; static preview tests in tests/preview. Coverage includes branches. Keep focused contract cases for incomplete pagination, credentials, raw-data fidelity, null/units, immutable prompts, expired/duplicate confirmation, conflicts, partial/unknown outcomes and local-refresh failure.

## Frontend and isolated browsers

Node 20 builds the versioned CSS and local fonts; runtime installation requires neither npm nor Node. `npm ci` uses the root lockfile. Rebuild assets after template/class changes. Do not use inline scripts or remote fonts/libraries.

```bash
npx playwright install --with-deps chrome
npm run test:e2e
npm run preview:capture
npm run test:preview
```

The application runner creates private temporary configuration/database, random ephemeral credentials, an unused loopback port and a synthetic account. It cleans up child processes and data even after failure. It never uses the workspace DB. Do not weaken these guards. Capture stages all images before publishing them into preview; no real training records enter the static tour.

## Translations

```bash
uv run python manage.py makemessages -l pt_BR --no-wrap --ignore=node_modules --ignore=.venv --ignore=var --ignore=preview
uv run python manage.py compilemessages -l pt_BR --ignore=.venv
```

Review PO entries and commit both PO and MO. Exercise translations are display-only, reviewed separately, and bound to provider IDs during import. Preserve original user-authored strings. URLs remain English; language is the native Django cookie.

## Dependencies and release

Use lockfiles. Audit Python with pip-audit against `uv export --locked --no-dev`; run `npm audit --audit-level=high`. Re-run local corpus performance after query/presenter changes. Update READMEs, changelog, docs and parity reference together. Version 0.2.0 requires a fresh database; do not imply compatibility with legacy data. Publishing a release or real provider changes requires an explicit task instruction.
