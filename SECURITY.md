# Security policy

## Supported version

Security fixes are applied to the latest released version. This is a personal,
self-hosted application; operators remain responsible for host security,
HTTPS, backups, access controls, and credential rotation.

## Reporting a vulnerability

Use GitHub's private vulnerability reporting for this repository. Do not open
a public issue containing a credential, personal training data, database,
backup, provider payload, exploit details, or an identifying screenshot.

Include the affected version, reproducible steps using synthetic data, impact,
and any suggested mitigation. Never test against another person's installation
or the real Hevy account of another user.

## Scope reminders

Tuxedo Fitness does not store the Hevy API key in SQLite and must never expose
it in HTML, JavaScript, URLs, logs, fixtures, exports, or documentation. The
application does not claim to be suitable for clinical or safety-critical use.
