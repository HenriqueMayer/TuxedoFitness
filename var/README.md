# Runtime data

`var/private/` is the local boundary for installation-specific runtime data.
It is ignored by Git.

Examples include:

- Hevy snapshots;
- the future SQLite database and journal files;
- private diagnostic payloads;
- generated personal exports;
- local backup staging files.

Do not place source code, fixtures, or required documentation in
`var/private/`. Backups must normally be stored outside the repository.
