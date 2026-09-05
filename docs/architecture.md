# Architecture

A local-first Django monolith, independently deployable with SQLite WAL. No Celery, Redis, LLM proxy, remote frontend assets or sibling-checkout dependencies.

| App | Owns |
|---|---|
| core | Settings, environment permissions, database setup, health/readiness |
| pages | Public product page |
| accounts | Native authentication, presentation preferences, verified backup/delete workflows |
| integrations | Hevy credentials/client/DTOs, raw snapshots, sync state, locking, HTTP writes |
| training | Normalized catalogue, folders, routines, workouts and ordered sets |
| analytics | Deterministic metrics and eligibility |
| dashboard | Preferences, filters, report assembly and SVG presentation |
| planning | Training profile, prompt construction/history, routine proposals |

Hevy is authoritative for existing workouts/routines. Only a successful validated collection publishes its normalized entities and corresponding raw payloads in one local transaction. Network requests happen outside that transaction. Deleted records are inactive locally; old prompt generations retain their original context.

Analytics derives from normalized records. Preferences/profile come from the user. LLM output remains a proposal until explicitly confirmed. Views enforce authentication/ownership and coordinate forms; templates never calculate workout metrics. JavaScript enhances language selection, theme, navigation, copying and after-load synchronization.

Credentials are MultiFernet ciphertext on HevyAccount; the encryption keys live outside SQLite in private installation configuration. Logout does not disconnect. Stored raw snapshots, exports and prompts contain no application-injected secret. No provider writes are triggered by GET or by prompt generation.

Synchronization and confirmed writes share an account lock. Full reads validate references before marking missing rows inactive. Incremental reads overlap the prior high-water time, deduplicate events and advance the cursor only after successful persistence. Proposals track each operation before dispatch; interrupted submissions are recovered as unknown rather than assumed successful.
