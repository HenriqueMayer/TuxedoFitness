# Tuxedo Fitness

<img alt="Version 0.2.0" src="https://img.shields.io/badge/version-0.2.0-B88A59">

[Português (Brasil)](README.pt-BR.md) · [Documentation](docs/README.md) · [Interface tour](preview/index.html)

A local-first training dashboard in the Tuxedo family. Connect Hevy once, explore your history and exercise catalogue, analyze training, and generate complete prompts for the LLM you choose. Review a JSON proposal before creating or updating routines in Hevy.

- Encrypted, account-scoped Hevy credentials stored across sessions and restarts.
- Full training history, routine folders, bilingual exercise search and CSV/JSON exports.
- Six configurable analysis topics: frequency, progression, effort, volume, distribution and duration.
- Optional training profile and immutable, downloadable prompt generations using original Hevy data.
- Batch routine creation/update with validation, remote comparison, single-use confirmation and per-operation results.
- English and Brazilian Portuguese, independent units/timezone/date preferences, light/dark themes and server-rendered fallbacks.

Nutrition, body measurements, editing completed workouts and an integrated LLM chat are outside this release. The application never sends your data to an LLM automatically. Hevy API access requires Hevy Pro.

## Install

Python 3.12+ and [uv](https://docs.astral.sh/uv/) are required. Node is only needed to rebuild assets or run browser tests. CSS, fonts, HTMX and compiled translations are versioned.

```bash
uv sync --locked
uv run python scripts/init_local.py
uv run python manage.py migrate
uv run python manage.py runserver
```

Open <http://127.0.0.1:8000/>, create an account, and save your Hevy key in **Hevy connection**. The first access-triggered synchronization imports all pages; the header also offers a manual button. Local pages remain usable during provider failures.

**0.2.0 starts with a new database.** There is no supported data migration from 0.1.x. Do not point the new installation at the old database; preserve the old installation and follow [the reset procedure](docs/operations.md). The default data directory is `var/private/v020`.

Back up both SQLite and the installation encryption keys, stored separately. Losing the encryption keys prevents decrypting stored Hevy credentials. See [backup, restore and rotation](docs/operations.md).

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for checks, isolated browser tests, synthetic capture and translation maintenance. Finance commit `90cfe53` is the family reference; [the parity contract](docs/tuxedo-parity.md) records shared patterns and deliberate domain differences.

This repository is independently installable and never imports the Finance checkout at runtime. Technical documentation and code use English; the interface supports EN/PT-BR. [PolyForm Noncommercial 1.0.0](LICENSE).
