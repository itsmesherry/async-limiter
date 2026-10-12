# Contributing

Thanks for helping improve `async-limiter`. Bug reports and fixes are welcome.

## Setup

```bash
git clone https://github.com/itsmesherry/async-limiter.git
cd async-limiter
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Before opening a pull request

```bash
ruff format && ruff check . && mypy async_limiter && pytest
```

CI runs the same checks on Python 3.9 to 3.13, so avoid syntax newer than 3.9
(for example, write `Optional[str]`, not `str | None`). The package has no
runtime dependencies; please keep it that way.

A pull request should:

- include a test for any behaviour it adds or fixes
- add a line under `## [Unreleased]` in [CHANGELOG.md](CHANGELOG.md)
- keep existing public names working; see below

## Compatibility

People depend on this package, so within a major version:

- do not remove or rename public methods, attributes or constructor arguments
- new constructor arguments need a default that preserves current behaviour
- a change to how long callers wait or how many get through is a behaviour
  change: call it out in the changelog

## Releasing (maintainers)

1. Open a release pull request that bumps the version in `pyproject.toml`
   (the only place it is defined) and renames `Unreleased` in `CHANGELOG.md` to
   the new version and date (leave a fresh, empty `Unreleased` above it).
2. Merge it once CI is green.
3. Check that the tag `v<version>` does not exist yet (`git ls-remote --tags origin`).
4. Create a GitHub Release on that commit with the tag `v<version>`, for example
   `v1.2.0`, and paste the changelog section as the notes.

Publishing the release runs `.github/workflows/publish.yml`, which builds the
package from the tag and uploads it to PyPI through Trusted Publishing. No API
token is involved, and the workflow refuses to publish if the tag does not match
the version in `pyproject.toml`.
