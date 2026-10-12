<h1 align="center">async-limiter</h1>

<p align="center">
  An asyncio rate limiter that enforces two limits at once:<br>
  how many requests run at the same time, and how many start per time period.
</p>

<p align="center">
  <a href="https://pypi.org/project/async-limiter/"><img alt="PyPI" src="https://img.shields.io/pypi/v/async-limiter"></a>
  <a href="https://github.com/itsmesherry/async-limiter/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/itsmesherry/async-limiter/actions/workflows/ci.yml/badge.svg"></a>
  <a href="https://pypi.org/project/async-limiter/"><img alt="Python" src="https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue"></a>
  <a href="https://pypi.org/project/async-limiter/"><img alt="Downloads" src="https://img.shields.io/pypi/dm/async-limiter"></a>
  <a href="https://github.com/itsmesherry/async-limiter/blob/main/LICENSE"><img alt="License" src="https://img.shields.io/badge/license-MIT-blue"></a>
</p>

Many APIs publish both kinds of limit, for example "at most 5 requests in
flight and at most 100 per minute". `DualRateLimiter` holds a caller back until
both allow it. It has no dependencies.

```bash
pip install async-limiter
```

```python
import asyncio
from async_limiter import DualRateLimiter

limiter = DualRateLimiter(max_concurrent=5, max_requests=100, time_period=60)


async def fetch(i):
    async with limiter:  # waits here until both limits allow the call
        await asyncio.sleep(0.1)  # your API call
        return i


async def main():
    results = await asyncio.gather(*[fetch(i) for i in range(20)])
    print(results)


asyncio.run(main())
```

## Three ways to use it

```python
# As a context manager
async with limiter:
    await call_api()

# As a decorator
@limiter.limit()
async def call_api_limited():
    return await call_api()

# With explicit acquire and release
await limiter.acquire()
try:
    await call_api()
finally:
    limiter.release()
```

A limiter can be created at module level and shared by every task that calls
the same API. Use one limiter per API.

## Options

| Argument         | Default | Meaning                                                    |
| ---------------- | ------- | ---------------------------------------------------------- |
| `max_concurrent` |         | Most requests allowed in flight at once                    |
| `max_requests`   |         | Most requests allowed to start within `time_period`        |
| `time_period`    |         | Length of the window, in seconds                           |
| `conservative`   | True    | Allow one request fewer than `max_requests` per window     |
| `name`           | None    | Label used in log messages                                 |
| `wait_margin`    | 0.1     | Extra seconds to sleep past the moment a slot opens        |

## How the limits behave

- **The window slides.** A request may start when fewer than `max_requests`
  have started in the last `time_period` seconds, counted from each request's
  start.
- **`conservative` is on by default.** With `max_requests=100` the limiter lets
  99 through per window, to leave a margin for clock differences with the
  server. Pass `conservative=False` to use the full limit.
- **Waiting adds a small margin.** A caller that has to wait for the window
  sleeps `wait_margin` seconds (0.1 by default) past the moment a slot opens.
  On windows of a second or less this lowers throughput noticeably.
- **A waiting caller holds a concurrency slot.** The concurrency limit is taken
  first, so callers queued on the time limit count as in flight.
- **Cancellation is safe.** A caller cancelled while waiting, for example by
  `asyncio.wait_for`, gives its slot back.
- **One process, one event loop at a time.** The limiter is not shared between
  processes or threads. It can be reused by successive `asyncio.run()` calls,
  and the request history carries over between them.

## Using the full limit

Both safety margins are on by default. To get exactly the numbers you pass in:

```python
limiter = DualRateLimiter(
    max_concurrent=5,
    max_requests=100,
    time_period=60,
    conservative=False,  # allow 100 per window, not 99
    wait_margin=0,       # start as soon as a slot opens
)
```

Keep the margins when the limit is enforced by a server whose clock and
counting you cannot see; drop them when you control both sides.

## Metrics

```python
limiter.get_metrics()
```

```python
{
    "total_requests": 100,          # requests let through
    "current_requests": 2,          # holding a concurrency slot right now
    "rate_limit_delays": 5,         # requests that had to wait for the window
    "total_delay_time": 12.5,       # seconds spent in those waits
    "errors": 0,
    "current_queue_size": 3,        # requests started within the current window
    "max_concurrent": 5,
    "max_requests_per_period": 99,  # after the conservative adjustment
    "time_period": 60,
}
```

`limiter.reset_metrics()` zeroes the counters.

## Logging

The limiter logs to the `rate_limiter` logger: a line at `INFO` when it is
created and each time a caller has to wait, and details at `DEBUG`.

```python
import logging

logging.getLogger("rate_limiter").setLevel(logging.WARNING)  # quiet it down
```

## Example

[`examples/api_client.py`](https://github.com/itsmesherry/async-limiter/blob/main/examples/api_client.py)
wraps an `aiohttp` client with a limiter and prints its metrics.

## Project

[Changelog](https://github.com/itsmesherry/async-limiter/blob/main/CHANGELOG.md) · [Contributing](https://github.com/itsmesherry/async-limiter/blob/main/CONTRIBUTING.md) · [Roadmap](https://github.com/itsmesherry/async-limiter/blob/main/TODO.md) · [MIT License](https://github.com/itsmesherry/async-limiter/blob/main/LICENSE)
