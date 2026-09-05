# Version 0.2.0 verification record

Date: 2026-09-05. Reference family: Finance `90cfe53`. This record covers the local implementation and synthetic verification; it does not claim a production deployment, published release or real Hevy write.

| Verification | Evidence |
|---|---|
| Django suite | 177 passing tests, including original suites and new contracts/planning cases |
| Combined line/branch coverage | 93%; required floor 80% |
| Integration coverage | 93%; required floor 90% |
| Analytics coverage | 97%; required floor 90% |
| Browser journeys | 12 passing Playwright cases across desktop, tablet and mobile; EN/PT-BR; both themes; keyboard, focus/scroll, preferences, prompts and no-JavaScript paths |
| Static preview | 2 passing browser cases using explicit local HTML filenames, one per language |
| Visual inspection | Desktop overview/analysis and mobile dark overview inspected from synthetic screenshots |
| Local performance | 10,000 workouts / 200,000 sets; every surface meets its p95 target; see [results](performance.md) |
| Runtime dependency audit | pip-audit: no known vulnerabilities in locked runtime dependencies |
| Frontend dependency audit | npm audit: zero vulnerabilities |
| Build artifacts | CSS and local fonts reproduced byte-for-byte; committed MO matches msgfmt output |
| Repository checks | Ruff, Django checks, migration drift, version consistency, lockfile, secret/history scan and whitespace checks passed |
| Fresh database | All committed migrations applied to a new, empty 0.2.0 database; integrity and foreign-key checks passed |
| Backup/restore | SQLite online backup verified, then restored into a disposable directory and rechecked |
| Cryptography | Synthetic persistence, isolation, wrong/missing key-ring, rotation and decryptability tests |

## Practical boundaries

Hevy reads and writes in automated tests use synthetic transports. Actual account authentication, the provider's current availability and changes to real routines require the owner's connection. Ambiguous write outcomes are never retried automatically. The benchmark excludes provider/network time.

Backup rehearsal used an explicitly configured temporary directory outside the checkout. An installation must choose its own durable backup destination and preserve the encryption key ring separately. The fresh database contains no migrated legacy users or training data. The previous local installation was preserved before selecting the new data directory.

PT-BR exercise names use the reviewed local vocabulary bound to provider IDs during import. Untranslated standard exercises and custom exercises retain their original names; no provider translation endpoint is assumed. Prompts and imports do not call an LLM, and no secret is inserted into exported context.

## Reproduction

Use the commands in [CONTRIBUTING](../CONTRIBUTING.md), [testing](testing.md), [operations](operations.md) and [preview maintenance](../.github/preview/README.md). Runtime installation uses committed CSS, fonts, HTMX and compiled translations and does not require Node. Node and gettext are development/build tools.
