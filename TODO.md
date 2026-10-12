# TODO

Planned work, roughly in priority order. Open an issue or pull request if you
want to pick one up.

- [ ] In the next major version, consider turning both safety margins off by
      default (`conservative=False`, `wait_margin=0`), so that the limiter
      enforces exactly the numbers it is given
- [ ] Decide whether callers waiting on the time limit should hold a
      concurrency slot
- [ ] Serve waiting callers in arrival order
- [ ] Log under the package's own name; the logger is called `rate_limiter`
