# Versioning and releases

Tuxedo Fitness uses Semantic Versioning in the form `MAJOR.MINOR.PATCH`.
Before `1.0.0`, a minor release may contain a clearly documented compatibility
change.

## Source of truth

The canonical application version is `[project].version` in
[`pyproject.toml`](../pyproject.toml). The matching project entry in `uv.lock`,
the README badge, changelog, and release tag are validated by
`scripts/check_version.py`. `package.json` contains development tools only.

Release tags use the canonical version prefixed with `v`, for example
`v0.2.0`.

## Release workflow

1. Accumulate user-visible changes under `Unreleased` in `CHANGELOG.md`.
2. Choose the version and update `pyproject.toml`.
3. Run `uv lock` and add a dated changelog section.
4. Run `uv run python scripts/check_version.py` and the complete pipeline in
   [`testing.md`](testing.md).
5. Merge the release through a protected pull request from `develop` to
   `main` after CI succeeds.
6. Create an annotated `vMAJOR.MINOR.PATCH` tag on the release commit and use
   the matching changelog section as the GitHub release notes.

Published release sections and tags are immutable. Hotfixes start from the
released branch and receive a new patch version.
