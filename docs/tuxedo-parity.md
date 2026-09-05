# Tuxedo family parity contract

Reference: **TuxedoFinance `90cfe53`**, reviewed 2026-09-05. Sources: root README, docs/README, docs/design-system.html, docs/frontend.md, CONTRIBUTING, root build manifests and isolated preview/browser tooling at that revision.

Both repositories install independently. Never import, symlink or read sibling files at runtime. A reference update is a reviewed change to this contract, component assets and their verification evidence.

| Shared contract | Fitness implementation |
|---|---|
| Python 3.12, Django 6.0, SQLite WAL | `core`, domain apps, committed migrations |
| Views coordinate; services own rules | integration, analytics, planning services |
| Django templates, compiled Tailwind, HTMX, small local JS | root build manifests, assets/css, static |
| Inter; cream/forest/caramel; dark night palette | local fonts, tailwind.config.js |
| Responsive shell, mobile modal, native account menu | shared partials with Fitness navigation |
| Rounded panels, forms, messages, tables, pagination | shared CSS component classes and template partials |
| Native EN/PT-BR language cookie; English URL paths | LocaleMiddleware, gettext PO/MO, set_language |
| Independent presentation preferences | timezone, dates, mass/distance units |
| Same-path focus/scroll; pathname h1 navigation | static/js/navigation.js |
| Progressive disclosure and server-side validation | prompt history modes, errors retained, irrelevant values cleared |
| Server SVG and equivalent data tables | dashboard presenter; last interaction layer |
| Isolated synthetic E2E/capture | scripts/run_e2e.py and .github/preview |
| Version/checks, changelog, canonical docs | 0.2.0; root scripts and CI |

Differences are intentional: Fitness keeps its local-only fonts/scripts and strict CSP; Hevy secrets are encrypted with a separate installation key; fitness chart values carry no automatic positive/negative evaluation; no banking, currencies, tax or financial ledger features are copied. Fitness retains its 80% combined line/branch coverage floor. Local original API payloads are needed for faithful prompt exports.

Revalidate desktop/tablet/mobile, both languages/themes, keyboard and JavaScript-disabled paths whenever adopting a new family component. The copied design-system artifact documents family components; Fitness labels and metric colors are domain-specific.
