# Static preview maintenance

Aligned with Finance's isolated screenshot-tour workflow at 90cfe53. `npm run preview:capture` delegates to the guarded disposable application runner, populates only synthetic records, captures all six primary surfaces in both languages, stages every image and publishes files only after all captures succeed. Temporary credentials/database/processes are removed on exit. No real user data is read.

`preview/index.html` and `preview/pt-br/index.html` are explicit entrypoints for file:// or static HTTP access. The language links include filenames and work without JS. `npm run test:preview` verifies the actual file:// access mode in a local test browser. `python3 -m http.server 4173 --bind 127.0.0.1 --directory preview` serves the same files for HTTP access. Only preview/ belongs in a Pages artifact; no runtime DB or seeding code is published.

Screenshots are static, synthetic examples of the real UI. Theme toggling affects the tour shell; captured application screenshots retain the capture theme. Recapture after material UI changes. Do not weaken guards to point the runner at a workspace database or owner backup.
