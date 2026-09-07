# Frontend

Family baseline: [parity contract](tuxedo-parity.md). Inter 400/500/600/700 is served locally. Light: cream #FAF8F3, forest #1A2E26, caramel #B88A59. Dark: night #101010, surface #1B1B1B, raised #262626, muted #B8B8B8. Chart emphasis is semantic; a higher RPE or load does not imply a better outcome.

Main navigation: Overview, Analysis, History, Routines, Exercises, Generate prompt. Account menu: Settings, Training profile, Hevy connection, Saved prompts. The synchronization status and manual fallback stay available in the authenticated shell.

Templates use shared panel/input/button classes. Controls have labels and errors. Prompt history modes expose relevant controls, clear incompatible values on change, and validate on the server. Without JS all relevant inputs and their labels are available; irrelevant values are cleared during form cleaning.

HTMX uses `show:none`. Same-path updates restore scroll and the equivalent focused control; navigation to another pathname focuses h1. Language uses Django's native cookie, not URL prefixes. Date order, timezone and mass/distance units are independent of language. User-written titles/comments are never translated.

Charts are server-calculated SVGs with title/description and an equivalent table. All marks are painted before focusable hit targets and tooltips. Tooltips have keyboard and pointer access. Tables support horizontal overflow within the card; pages must not overflow horizontally on mobile. No calculation is duplicated in browser code.

Compiled CSS, local fonts, HTMX, JS and gettext MO files are versioned. Build with `npm run build`; compile translations with `manage.py compilemessages -l pt_BR --ignore=.venv`. Validate both languages/themes, desktop/tablet/mobile and no-JS paths with the isolated browser runner.


Primary section selection uses namespaced routes, including detail pages.
Routine imports/proposals belong to Routines; saved prompt generations belong
to Generate prompt. Desktop, mobile and no-JavaScript menus share this mapping.

Charts use line, vertical-bar and horizontal-bar presentations, with dashed
weekly targets. Delegated pointer/focus/click inspection updates a wrapping HTML
readout; values remain accessible in SVG descriptions and equivalent tables
without JavaScript. Measurement series use 60-observation windows. Raw provider
IDs are not displayed as session labels. The factual landing page uses the full
Fitness emblem; navigation retains its compact derivative.

Each chart now has one presentation at every width. Temporal plots stretch only
SVG geometry along x; axis labels remain native-size HTML (at least 12 px).
Category labels and values are HTML rows with SVG tracks. Transparent hit areas
and unfilled lines have explicit SVG presentation attributes, so an unavailable
stylesheet cannot turn interaction rectangles into black panels. Arrow keys,
Home and End navigate observations. Tables retain the same observation window.

Local CSS/JS URLs include a digest of their contents, including in development.
`core/assets.py` caches digests by file metadata; no manual release-version bump
is needed. The page carries a combined frontend revision. On an HTMX GET from
an old or unversioned tab, middleware requests a full navigation to the intended
URL before any body swap. POST requests are never replayed. Restored history is
checked against the loaded revision. This follows the standard
[HTMX response-header contract](https://htmx.org/reference/#response_headers).

The anonymous landing uses Finance's exact grid, spacing, typography, 64 px
navigation and artwork frame, with Fitness copy and its own emblem. At 1920 px,
the two local applications produced identical bounding boxes for the header,
main container, heading, hero frame and feature-section heading.
