# Accounts app

`accounts` uses Django's native user, authentication form, login view, and
logout view. It exposes:

| Route | Behavior |
| --- | --- |
| `/conta/entrar/` | Public login. |
| `/conta/cadastro/` | Public native signup only when explicitly enabled; closed by default. |
| `/conta/sair/` | Authenticated POST logout. |
| `/conta/configuracoes/` | Authenticated preference form, export link, and backup-gated deletion. |

`SignupView` creates a native Django user and its `OwnerPreference`, then logs
the user in. New account creation can be disabled with `ALLOW_SIGNUPS=False`
without affecting login. `create_owner <username>` remains an empty-database
bootstrap alternative. Settings edits stay local. Deletion requires the exact `EXCLUIR`
confirmation and a successful SQLite integrity and foreign-key checked backup
outside the source checkout. `backup_database` creates a verified backup and
`check_database` validates any selected SQLite file. Key replacement is an
environment-only operation: update
`HEVY_API_KEY` and restart the application; never submit it through the UI.

`prune_runtime_data` removes expired JSON snapshots only from the ignored
private snapshot directory and prunes old synchronization logs according to
the documented retention floor.
