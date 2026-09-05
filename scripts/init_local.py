#!/usr/bin/env python3
"""Create a private installation environment without printing credentials."""

import os
import secrets
from pathlib import Path

from cryptography.fernet import Fernet


def main():
    target = Path(
        os.environ.get(
            "TUXEDO_ENV_FILE", Path(__file__).resolve().parent.parent / ".env"
        )
    )
    if target.exists():
        raise SystemExit(
            "Environment already exists. Preserve it and follow docs/operations.md for reset or rotation."
        )
    text = "\n".join(
        [
            "SECRET_KEY=" + secrets.token_urlsafe(48),
            "HEVY_ENCRYPTION_KEYS=" + Fernet.generate_key().decode(),
            "DEBUG=True",
            "ALLOW_SIGNUPS=True",
            "ALLOWED_HOSTS=localhost,127.0.0.1,testserver",
            "TUXEDO_DATA_DIR=var/private/v020",
            "",
        ]
    )
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as stream:
        stream.write(text)
    print("Created private installation configuration. Run manage.py migrate next.")


if __name__ == "__main__":
    main()
