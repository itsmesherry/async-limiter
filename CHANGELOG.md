# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.2.0] - 2026-10-13

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
- On Python 3.9, creating a limiter after an earlier `asyncio.run()` had
  finished raised `RuntimeError`.

### Added

- `wait_margin` argument: the extra time a waiting caller sleeps past the moment
  a slot opens. It defaults to 0.1 seconds, the value that was hardcoded before;
  `wait_margin=0` gives the full allowed throughput.
- `py.typed` marker, so type checkers use the package's annotations.
- Python 3.12 and 3.13 are tested and declared as supported.
- `dev` extra with the tools CI runs.

### Changed

- An unexpected error inside `acquire()` is no longer re-raised as
  `RuntimeError`; the original exception propagates. No such error is known to
  occur, and the `errors` metric stays in `get_metrics()` with a value of 0.
- The limiter no longer logs a warning when a waiting caller is cancelled, or a
  debug line each time old requests leave the window.
- Using one limiter from two event loops that run at the same time (two
  threads) raises `RuntimeError` on `acquire()`.
- The `test` extra no longer installs `aiohttp`, which only the example uses.
- The package is classified as Beta, not Production/Stable.
- `request_times` holds `time.monotonic()` values, not `time.time()` values.

## [1.1.0] - 2025-03-27

Last version published before this changelog was started. Added the
`conservative` option.

[Unreleased]: https://github.com/itsmesherry/async-limiter/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/itsmesherry/async-limiter/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/itsmesherry/async-limiter/releases/tag/v1.1.0
