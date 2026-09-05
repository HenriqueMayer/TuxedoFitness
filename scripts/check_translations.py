#!/usr/bin/env python3
"""Verify the committed MO matches the reviewed PO; gettext is developer-only."""

import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    base = ROOT / "locale/pt_BR/LC_MESSAGES"
    with tempfile.TemporaryDirectory(prefix="fitness-gettext-") as directory:
        output = Path(directory) / "django.mo"
        subprocess.run(
            ["msgfmt", "--check", "-o", str(output), str(base / "django.po")],
            check=True,
        )
        if output.read_bytes() != (base / "django.mo").read_bytes():
            raise SystemExit(
                "Compiled translations are stale. Compile and commit the MO file."
            )
    print("Compiled PT-BR translation catalogue is current.")


if __name__ == "__main__":
    main()
