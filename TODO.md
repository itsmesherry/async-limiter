# TODO

Planned work, roughly in priority order. Open an issue or pull request if you
want to pick one up.

- [ ] In the next major version, consider turning both safety margins off by
      default (`conservative=False`, `wait_margin=0`), so that the limiter
      enforces exactly the numbers it is given
- [ ] In the next major version, remove the unused `lock` attribute and the
      `errors` metric, which is always 0
- [ ] Decide whether callers waiting on the time limit should hold a
      concurrency slot
- [ ] Serve waiting callers in arrival order
- [ ] Log under the package's own name; the logger is called `rate_limiter`
