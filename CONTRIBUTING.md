# Contributing to Tuxedo Fitness

Thank you for improving Tuxedo Fitness. Contributions are provided under the
repository's [PolyForm Noncommercial License](LICENSE) and must preserve its
required copyright and license notices.

## Project boundaries

- Keep the application local-first, self-hosted, read-only toward Hevy, and
  compatible with a single SQLite writer.
- Keep code and technical documentation in English and user-facing text in
  Brazilian Portuguese.
- Never commit credentials, personal exports, SQLite databases, backups, or
  real provider payloads. Tests and examples must be synthetic.
- Preserve server-rendered behavior, accessibility, and no-JavaScript
  fallbacks. Do not add a runtime CDN or weaken the Content Security Policy.
- Keep AI, chat, webhooks, Hevy writes, body measurements, queues, and
  distributed infrastructure outside the current release scope.

## Before proposing a change

Update affected documentation and add a concise entry under `Unreleased` in
[`CHANGELOG.md`](CHANGELOG.md). Run the complete pipeline documented in
[`docs/testing.md`](docs/testing.md), including the browser suite for frontend
changes. Do not remove meaningful tests to make an intermediate build pass.

Release versions and tags follow [`docs/versioning.md`](docs/versioning.md).
