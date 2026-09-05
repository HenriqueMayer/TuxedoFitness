# Frontend

Family baseline: [parity contract](tuxedo-parity.md). Inter 400/500/600/700 is served locally. Light: cream #FAF8F3, forest #1A2E26, caramel #B88A59. Dark: night #101010, surface #1B1B1B, raised #262626, muted #B8B8B8. Chart emphasis is semantic; a higher RPE or load does not imply a better outcome.

Main navigation: Overview, Analysis, History, Routines, Exercises, Generate prompt. Account menu: Settings, Training profile, Hevy connection, Saved prompts. The synchronization status and manual fallback stay available in the authenticated shell.

Templates use shared panel/input/button classes. Controls have labels and errors. Prompt history modes expose relevant controls, clear incompatible values on change, and validate on the server. Without JS all relevant inputs and their labels are available; irrelevant values are cleared during form cleaning.

HTMX uses `show:none`. Same-path updates restore scroll and the equivalent focused control; navigation to another pathname focuses h1. Language uses Django's native cookie, not URL prefixes. Date order, timezone and mass/distance units are independent of language. User-written titles/comments are never translated.

Charts are server-calculated SVGs with title/description and an equivalent table. All marks are painted before focusable hit targets and tooltips. Tooltips have keyboard and pointer access. Tables support horizontal overflow within the card; pages must not overflow horizontally on mobile. No calculation is duplicated in browser code.

Compiled CSS, local fonts, HTMX, JS and gettext MO files are versioned. Build with `npm run build`; compile translations with `manage.py compilemessages -l pt_BR --ignore=.venv`. Validate both languages/themes, desktop/tablet/mobile and no-JS paths with the isolated browser runner.
