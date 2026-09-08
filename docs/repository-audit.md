# Repository review — 2026-09-07

Reference: TuxedoFinance `90cfe53`. Scope: repository hygiene, documentation,
public landing, navigation, local exercise translations, report presentation,
analytics and CI/Pages. This is an incremental update to the existing 0.2.0
installation, with no database reset or public release.

## Findings and corrections

| Area | Finding | Correction |
|---|---|---|
| Repository | Research datasets/scripts and legacy requirements had no runtime consumers. | Remove tracked research and legacy materials; preserve ignored local files and Git recovery history. Keep product and provider documentation. |
| Documentation | Short READMEs and outdated asset descriptions did not match the family reference. | Matching bilingual README structure; factual capabilities; separate fresh-install and existing-0.2.0 update paths. |
| Landing | Marketing headline and enlarged navigation icon. | Product-name heading, factual feature rows, original full-resolution emblem and family framing. Remove the footer slogan. |
| Navigation | Three primary links lacked active state; detail routes had incomplete section mapping. | A shared namespaced-route map for desktop, mobile and no-JavaScript navigation. |
| Exercises | Only 76 of 451 standard local exercises had PT-BR labels. | Versioned ID/title-bound catalogue with all 451 labels and an idempotent offline refresh/check command. |
| Charts | Bar-only rendering, categorical codes and unbounded observation series. | Lines, horizontal/vertical bars, localized labels, keyboard/touch readouts, matching tables and 60-observation windows. |
| Analytics | Period comparison showed only sessions. | Topic-specific comparisons, dated period records, weekly sessions/target and primary-muscle sets. Canonical calculations remain server-side. |
| Performance | Translating categorical choices once per set inflated distribution time. | Resolve code labels once per request, then count observations. |
| CI | Node 20 development contract and outdated Pages/Python actions. | Node 24; modern checkout/setup/configure/upload/deploy actions. |
| Pages | The site was disabled; the initial review could not inspect repository settings. | Enable GitHub Actions as the publishing source; deploy `main` and verify both languages and referenced assets. See the publication evidence below. |

## Data and compatibility

A private SQLite backup was created before applying local translations. All
451 standard exercise labels were refreshed; the subsequent check reported
zero required updates and zero unknown standard exercises. A before/after digest
of every other persisted exercise field matched. The two custom exercises were
preserved. No synchronization or remote Hevy write was used for this update.

Raw provider payloads, hashes, original titles, snapshots, saved prompts,
credentials and export contracts are unchanged. Existing migration history is
preserved. Research removal does not rewrite Git history. Local `.env`, runtime
databases, backups and ignored research downloads are outside the public tree.

## Verification

The original baseline passed 177 Django tests, 12 browser journeys and two
static-preview checks. The expanded suite passes 193 Django tests with 94%
combined line/branch coverage, 93% integrations and 98% analytics. New cases
cover catalogue preservation/idempotence, section mapping, pagination, missing
measurements, adjacent periods, unit conversions, weekly targets, isolation and
estimated-1RM eligibility.

A full 24-case browser run, a nine-case rerun with mixed synthetic data and
three additional RPE-axis checks passed. They cover 27 distinct scenarios across
desktop, tablet and mobile, including
both languages/themes, section selection and detail navigation, back/forward,
chart keyboard inspection, bounded pagination and no-JavaScript flows.
The refreshed tour contains 12 full-height synthetic screenshots. All four
static-preview checks passed: EN/PT-BR over both file:// and HTTP, without
JavaScript. Rendered landing, progression and distribution captures were visually reviewed;
axes remain readable HTML at all widths and each chart has a single plot.

All browser fixtures/captures are synthetic and isolated from the local owner
database. Python and npm dependency audits, Ruff, migration drift, lockfile,
translation compilation and local secret/reachable-history checks pass.
Rebuilding the compiled CSS produced the same checksum. Private verification
logs and screenshots are retained under `var/private/verification-2026-09-07/`;
they are not public deployment inputs.

The final 10,000-workout / 200,000-set benchmark passed every existing gate.
Report p95 ranged from 0.028–0.094 s and comparison p95 from 0.032–0.116 s;
the largest response was 105.3 KiB, below 1.5 MiB. See the
[complete measurements and method](performance.md#revision-verification--2026-09-07).

## Follow-up visual correction

The first visual checks used fresh browser sessions. They missed the upgrade
path in an already-open tab: CSS/JS still used the fixed `v=020` URL after their
contents changed. The reported screenshots were consistent with old CSS being
used with the new markup: missing landing utilities, both chart variants shown,
and default black fills on interaction rectangles. The running local server
was verified to serve the current checkout CSS.

The correction replaces fixed asset versions with content digests and guards
HTMX GET navigation across frontend revisions. Old tabs perform a full
navigation to their intended URL; submitted forms are never replayed. Regression
checks reproduce stale styles and a completely unavailable stylesheet.

The anonymous homepage was compared directly with the running Finance app at
1920 × 1080. Header height (65 px including border), main width (1280 px),
heading position/size, hero frame and feature-heading position matched exactly.
Fitness retains its own text and emblem. Public navigation now matches the
reference's height, typography and action-button treatment.

Charts now render once per card. Temporal geometry stays in SVG while native
HTML labels retain at least 12 px. Category bars have full labels and values;
interaction rectangles have an explicit transparent fill, independent of CSS.
Bar widths are capped, scales use rounded steps, every RPE category has an
axis label, distribution ranks descend by count, missing values remain gaps,
and keyboard arrows/Home/End inspect observations. Exact-load repetition trends
require repeated sessions, avoiding extra charts containing a single point.
Overview duration is displayed in hours/minutes/seconds.

The expanded visual matrix covers the anonymous home, overview and all six
analysis topics, both languages/themes, desktop/tablet/mobile, cached CSS,
missing CSS, keyboard inspection and page history. Synthetic capture data now
contains multiple set types, varying RPE and absent values. Verification files
are retained locally under `var/private/verification-correction/`.

## Remote publication — verified 2026-09-07

The initial review could not inspect the repository through the available
connector or unauthenticated browser. After administrator sign-in, the Pages
settings confirmed that the site was disabled: the source was **Deploy from a
branch**, with no branch selected. The repository is private.

The publishing source was changed to **GitHub Actions** and the existing
workflow was dispatched from `main` at `468e077`. Repository visibility was
preserved; only the synthetic `preview/` artifact was published.
[Deployment #3](https://github.com/HenriqueMayer/TuxedoFitness/actions/runs/34171846131)
completed successfully. The [English preview](https://henriquemayer.github.io/TuxedoFitness/)
and [Portuguese preview](https://henriquemayer.github.io/TuxedoFitness/pt-br/)
returned HTTP 200, as did all 15 referenced assets.

[CI #25](https://github.com/HenriqueMayer/TuxedoFitness/actions/runs/34170556293)
also passed for the same `main` commit. The external badge could not query this
private repository, so the README now links directly to workflow runs without
embedding credentials or a static pass/fail claim. See
[the setup procedure](operations.md#interface-preview-on-github-pages).
