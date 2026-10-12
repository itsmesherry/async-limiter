# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- Calling `release()` more often than `acquire()` raised the concurrent limit
  for the rest of the limiter's life. The extra release is now ignored and
  logged as a warning.
- Setting the system clock back kept callers waiting until the old timestamps
  expired. The limiter now measures time with a monotonic clock.
- A limiter used from a second event loop, such as a module-level limiter and
  two `asyncio.run()` calls or a test suite with one loop per test, raised
  `RuntimeError` as soon as a caller had to wait. This also affected
  module-level limiters on Python 3.9.

### Added

- `py.typed` marker, so type checkers use the package's annotations.
- Python 3.12 and 3.13 are tested and declared as supported.
- `dev` extra with the tools CI runs.

### Changed

- `request_times` holds `time.monotonic()` values, not `time.time()` values.

## [1.1.0] - 2025-03-27

Last version published before this changelog was started. Added the
`conservative` option.

[Unreleased]: https://github.com/itsmesherry/async-limiter/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/itsmesherry/async-limiter/releases/tag/v1.1.0
