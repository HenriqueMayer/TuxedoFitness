[English](README.md) | [Português (Brasil)](README.pt-BR.md)

<p align="center">
  <img src="static/brand/tuxedo-fitness-emblem.png" width="144" alt="Tuxedo Fitness">
</p>
<h1 align="center">Tuxedo Fitness</h1>
<p align="center">
  <a href="https://github.com/HenriqueMayer/TuxedoFitness/actions/workflows/ci.yml"><img src="https://img.shields.io/badge/CI-GitHub%20Actions-1A2E26?style=for-the-badge&amp;labelColor=101E18" alt="View CI runs on GitHub Actions"></a>
  <img src="https://img.shields.io/badge/version-0.2.0-B88A59?style=for-the-badge&amp;labelColor=101E18" alt="Version 0.2.0">
  <img src="https://img.shields.io/badge/Python-3.12-176B52?style=for-the-badge&amp;labelColor=101E18" alt="Python 3.12">
  <img src="https://img.shields.io/badge/Django-6.0-1A2E26?style=for-the-badge&amp;labelColor=101E18" alt="Django 6.0">
  <img src="https://img.shields.io/badge/UI-EN%20%7C%20PT--BR-B88A59?style=for-the-badge&amp;labelColor=101E18" alt="EN / PT-BR">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-PolyForm%20Noncommercial-7C5C13?style=for-the-badge&amp;labelColor=101E18" alt="PolyForm Noncommercial"></a>
</p>

Tuxedo Fitness is a local application for exploring Hevy training history,
reviewing routines, comparing exercise metrics and generating prompts for your
chosen LLM. Records stay in an owner-controlled SQLite database. The application
never sends them to an LLM automatically. Hevy API access requires Hevy Pro.

## Interface preview

<table>
  <tr>
    <td width="96" align="center">
      <a href="https://henriquemayer.github.io/TuxedoFitness/">
        <img src="static/brand/tuxedo-fitness-emblem-128.png" width="72" alt="Open the Tuxedo Fitness interface preview">
      </a>
    </td>
    <td>
      <strong>See Tuxedo Fitness before installing it.</strong><br>
      Explore the bilingual tour across Overview, Analysis, History, Routines,
      Exercises, and Prompt Generation, with light and dark Overview views.<br><br>
      <a href="https://henriquemayer.github.io/TuxedoFitness/"><strong>Open the interface preview →</strong></a>
    </td>
  </tr>
</table>

> The preview uses synthetic data and runs as a static tour. There is no login,
> public backend, or persistence, and nothing is saved.

The [local English tour](preview/index.html) and
[Portuguese tour](preview/pt-br/index.html) also work offline. Hosting requires
the one-time [Pages setup](docs/operations.md#interface-preview-on-github-pages).

## Quick start

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).
For a **new installation**:

```bash
git clone https://github.com/HenriqueMayer/TuxedoFitness.git
cd TuxedoFitness
uv sync --locked
uv run python scripts/init_local.py
uv run python manage.py migrate
uv run python manage.py runserver
```

Open [the application](http://127.0.0.1:8000/), create an account and save your API
key in **Hevy connection**. Synchronization imports your catalogue, routines and
workout history. The key is encrypted per account and survives application restarts.

For an **existing 0.2.0 installation**, back up SQLite and the encryption keys,
keep the existing configuration and database, and update with:

```bash
uv sync --locked
uv run python manage.py migrate
uv run python manage.py translate_exercises
uv run python manage.py runserver
```

This revision does not require a database reset. Only the older **0.1.x → 0.2.0**
transition requires the separate [legacy upgrade procedure](docs/operations.md).
Node is needed only for development; compiled frontend assets are included.

## Features

| Area | Capabilities |
|---|---|
| Overview | Activity, sets, effort distribution and selected-exercise progression. |
| Analysis | Six topics, indicator comparisons, dated exercise records, weekly goals and primary-muscle distribution. |
| History | Full synchronized history, exercise/set filters and CSV/JSON exports. |
| Routines | Folders, prescriptions and reviewed batch creation/update proposals with single-use confirmation. |
| Exercises | Versioned PT-BR names for 451 standard exercises, bilingual search and favorites. Custom names stay original. |
| Prompts | Optional profile, selectable history, original provider data and immutable saved generations. |
| Interface | EN/PT-BR, light/dark themes, keyboard/touch charts and no-JavaScript fallbacks. |
| Preferences | Independent mass/distance units, date format, timezone, panel order and weekly target. |

Graphs describe recorded training. Estimated 1RM is an estimate; assistance, RPE,
volume and different modalities are not treated as interchangeable performance scores.

## Technology

| Layer | Technology |
|---|---|
| Backend | Python, Django, native authentication |
| Frontend | Django templates, Tailwind CSS, HTMX, vanilla JavaScript, server-rendered SVG |
| Storage | SQLite WAL; separately managed encryption key ring |
| Tooling | uv and npm lockfiles, Node 24 for development, isolated Playwright tests |

## Configuration and data ownership

Configuration comes from `.env` or process variables, with process values taking
priority. `SECRET_KEY` and `HEVY_ENCRYPTION_KEYS` protect separate concerns;
`TUXEDO_DATA_DIR` selects the runtime directory. `ALLOW_SIGNUPS=False` closes
registration while preserving login. See [operations](docs/operations.md).

Keep database backups and encryption keys separately. Disconnecting Hevy removes
the credential while retaining local records. Prompt sharing is a deliberate
user action. Translation never rewrites provider payloads or export titles.

## Development

See [CONTRIBUTING](CONTRIBUTING.md) for setup, coverage gates and translation
maintenance. Use Node 24 and the root lockfile:

```bash
npm ci
npm run build
npm run test:e2e
npm run test:preview
```

Browser tests use disposable synthetic databases. The independently installable
Fitness application follows the [Tuxedo family contract](docs/tuxedo-parity.md).

## Documentation

- [Documentation index](docs/README.md) and [product requirements](docs/product-requirements.md)
- [Architecture](docs/architecture.md) and [data model](docs/data-model.md)
- [Analytics](docs/analytics.md) and [frontend](docs/frontend.md)
- [Hevy integration](docs/hevy-integration.md) and [planning](docs/planning.md)
- [Operations](docs/operations.md), [testing](docs/testing.md) and [performance](docs/performance.md)
- [Repository audit](docs/repository-audit.md) and [changelog](CHANGELOG.md)

Code and technical documentation are in English. Update both READMEs together.

## Contributing and license

Read [CONTRIBUTING](CONTRIBUTING.md) before proposing changes.
Copyright © 2026 Henrique Mayer. Licensed under
[PolyForm Noncommercial 1.0.0](LICENSE).
