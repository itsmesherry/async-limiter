# TODO

Planned work, roughly in priority order. Open an issue or pull request if you
want to pick one up.

- [ ] Make the 0.1 second wait margin configurable; on short windows it keeps
      throughput well below the limit (30 requests at 10 per 0.5 s take 1.2 s
      where 1.0 s is possible)
- [ ] Decide whether callers waiting on the time limit should hold a
      concurrency slot
- [ ] Serve waiting callers in arrival order
- [ ] Log under the package's own name; the logger is called `rate_limiter`
