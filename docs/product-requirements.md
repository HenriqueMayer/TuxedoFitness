# Product requirements · Fitness 0.2.0

Approved delivery: rebuild TuxedoFitness as an independent member of the Finance family, pinned to Finance `90cfe53`. The product controls training history, analysis and routine planning. Reuse reviewed synchronization/metric code; a new DB is required, but correct implementations are retained.

## Closed decisions

Independent repositories with documented parity; Django 6/Python 3.12/SQLite WAL/templates/Tailwind/HTMX; encrypted per-user persistent Hevy key; access-triggered synchronization; complete routine create/update batches; saved panel/filter/favorite preferences; optional reusable training profile; immutable prompt history; local reviewed PT-BR exercise vocabulary; bilingual exports/docs/preview and equivalent quality tooling.

Out of scope: nutrition, body measurements, creating/editing completed workouts, integrated chat and automatic LLM requests. Recommendations remain external proposals until explicitly confirmed.

## Acceptance journeys

| Surface | Required behavior |
|---|---|
| Public/auth | Factual introduction, login/signup, account-controlled settings, language and themes |
| Overview | Last 28 days including today, frequency, duration, working sets, eligible volume, recent sessions |
| Analysis | Six topics: frequency/consistency, load/progression, RPE, volume, distribution, duration/modalities |
| History | All active history by default, newest first; search, dates, routine/exercise/set filters, pagination, details and exports |
| Routines | Folder organization, ordered prescription, notes/rest/supersets, original JSON and planning/import actions |
| Exercises | Full account catalogue, original/translated search, equipment/muscle/modality filters, favorites, exercise progression |
| Generate prompt | Comments/profile, exact history selection, context preview, source/size evidence, save |
| Generations | Immutable saved text/context, copy, download, duplicate options using current data, owner-scoped deletion |
| Import JSON | Pure/fenced JSON or file; validate all operations, fetch current versions, compare, confirm once, show individual outcomes |

One connection per user is persistent across logout/restart. A different external identity cannot replace it and mix data. Disconnect removes the credential only. A valid complete first import publishes catalogue, folders, routines and history with original provider payloads. Later reads use 15-minute access cadence for workouts/routines and a 24-hour catalogue cache. Failures preserve last valid data and retry backoff. Manual POST works without JS.

Metric definitions preserve missing data, warmup separation, modality eligibility, exercise identity and equivalent time periods. External-load volume excludes bodyweight/assistance/time/distance. Epley is identified as an estimate and uses eligible normal/failure sets with positive weight and 1–10 integer repetitions. Historical routine adherence is never inferred from a current routine.

Prompt selections include last 28/7 days, a retrospective calendar month, custom inclusive dates and last N workouts (selected newest, presented chronologically). Use exact original routine pages and latest selected workout objects, plus a separate allowed catalogue/profile/provenance. No silent truncation. No history or routines is permitted when explicit; missing valid catalogue blocks ID-based output. The template contract and import validator use shared modality definitions. Every saved generation freezes text, options, version and sources.

Routine batches use schema_version 1 and the literal `{{HEVY_API_KEY}}` placeholder. Create omits routine_id; update requires an owned existing ID. API keys appear only in backend headers, never copied into the JSON body. Proposals expire after 15 minutes, revalidate source versions and run sequentially. Failures/unknown outcomes stop the batch; no automatic rollback or retry. Success with local-refresh failure is explicitly pending. Check Hevy before resolving an unknown operation.

## Verification and delivery

The five delivery layers are foundation; integration; local consultation/analytics; planning; confirmed writes/operations. Validate all-page contracts/aliases/events, encrypted credentials/rotation/isolation, manual metric examples/nulls/timezones, raw prompt fidelity/immutability, write failures/conflicts, responsive/bilingual/theme/keyboard/no-JS paths, clean migrations/backups and compiled assets.

Deliver version 0.2.0 with EN/PT-BR README, canonical English technical docs, changelog, self-contained synthetic preview and Finance-aligned CI. Keep the Fitness 80% line/branch floor. Repeat the 10,000-workout/200,000-set corpus: local list p95 ≤1 s, dashboard/report p95 ≤1.5 s; report network separately. Synthetic write tests are not evidence of live provider writes.


## September 2026 refinement

The product repository excludes archived research and legacy requirements.
The public landing page and bilingual README follow Finance's factual layout
while retaining Fitness branding. Every primary navigation section includes
its detail routes. The reviewed standard catalogue has 451 PT-BR display names
and an offline idempotent refresh command; custom/original records are preserved.
Analysis adds topic-specific period comparisons, dated period records, weekly
sessions versus target and weekly primary-muscle working sets. Charts use lines
or bars according to the data and bounded server-side observation windows.
