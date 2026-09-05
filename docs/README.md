# Tuxedo Fitness documentation

Current 0.2.0 product and implementation documentation. English technical documentation; bilingual root READMEs and interface. Finance reference: `90cfe53`.

| Document | Responsibility |
|---|---|
| [Product requirements](product-requirements.md) | Scope, journeys, delivery contract and exclusions |
| [Family parity](tuxedo-parity.md) | Reference commit, shared architecture/design and exceptions |
| [Architecture](architecture.md) | Boundaries, sources of truth and transactions |
| [Data model](data-model.md) | Ownership, snapshots, profiles and write lifecycle |
| [Frontend](frontend.md) | Tokens, progressive disclosure, navigation and accessibility |
| [Design system](design-system.html) | Family token/component reference |
| [Hevy integration](hevy-integration.md) | Read aliases, synchronization and confirmed writes |
| [Analytics](analytics.md) | Definitions, eligibility and comparison rules |
| [Planning](planning.md) | Prompt fidelity, dates, envelope and proposal contract |
| [Operations](operations.md) | Fresh installation, encryption, backup, restore and rotation |
| [0.2.0 verification](verification-0.2.0.md) | Dated test, audit, operational and performance evidence |
| [Testing](testing.md) | Synthetic tests, coverage and browser isolation |
| [Performance](performance.md) | Reproducible 10,000-workout corpus |
| [Versioning](versioning.md) | Release/check contract |
| [Contributing](../CONTRIBUTING.md) | Canonical development commands |
| [Preview maintenance](../.github/preview/README.md) | Disposable synthetic screenshot capture |

Domain reference: [apps](apps/README.md). Provider research: [Hevy](Hevy/README.md). Material in `legacy/` records previous requirements and must not be treated as the current product contract. Research data has no runtime dependency.

Runtime code lives in domain apps; shared build configurations remain at the repository root. `assets/` contains source CSS; `static/` contains compiled assets and local libraries; `locale/` contains PO/MO translations; `tests/` contains browser tests. `preview/` is self-contained, and `.github/preview/` holds its isolated capture tooling.
