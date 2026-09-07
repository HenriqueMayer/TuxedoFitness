# Verification

`uv run coverage run manage.py test` uses synthetic data and mock Hevy transports. Combined line/branch coverage must stay at least 80%; CI requires at least 90% in integrations and analytics. No test applies real provider changes.

Contract tests cover pagination and aliases; incomplete event collection does not advance cursors. Credential tests cover persistent ciphertext, separate sessions/users, logout/disconnect, identity mismatch, missing/wrong key rings and rotation. Metrics use manually calculated fixtures for nulls, warmups, modality eligibility, RPE, Epley, timezones and equal periods.

Planning tests exercise original routine-page/workout-object fidelity, exact date boundaries, last-N chronological ordering, no-history cases, explicit limits, immutable generations, real-key rejection, fenced JSON, whole-batch validation and shared examples. Write tests include duplicate/expired confirmation, external conflicts, partial success, ambiguous timeout, interruption and remote-success/local-failure states.

`npm run test:e2e` runs the real local UI against isolated synthetic storage across desktop/tablet/mobile, EN/PT-BR, light/dark, keyboard navigation, focus preservation and no-JavaScript workflows. `npm run preview:capture` creates a synthetic static screenshot tour. `npm run test:preview` checks explicit filenames and static browser access. These are local tests, not production deployment or live Hevy evidence.

Run `scripts/benchmark_reference_corpus.py` for 10,000 workouts/200,000 sets. Report local p95 and provider latency separately. Never use real owner data for public screenshots or benchmark artifacts.

The current revision adds the complete standard-exercise translation catalogue,
offline update/check idempotence, original-field preservation, all primary
section/detail mappings, 60-observation windows, saved-filter navigation, missing
measurements and explicitly marked partial calendar buckets. See the dated
[repository audit](repository-audit.md) for results.
