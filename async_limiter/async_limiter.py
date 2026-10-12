import asyncio
import functools
import logging
import time
from collections import deque
from typing import Any, Deque, Dict, Optional

logger = logging.getLogger("rate_limiter")


class DualRateLimiter:
    """
    A custom rate limiter that enforces both:
    1. Maximum concurrent requests at any given time
    2. Maximum number of requests within a time period

    This is useful for APIs that have both types of rate limits.

    Usage:
        # Create a rate limiter with 5 concurrent requests and 100 requests per minute
        limiter = DualRateLimiter(max_concurrent=5, max_requests=100, time_period=60)

        # Use as a context manager
        async with limiter:
            await api_call()

        # Or use acquire/release manually
        await limiter.acquire()
        try:
            await api_call()
        finally:
            limiter.release()

        # Or use as a decorator
        @limiter.limit()
        async def my_function():
            await api_call()
    """

    def __init__(
        self,
        max_concurrent: int,
        max_requests: int,
        time_period: float,
        conservative: bool = True,
        name: Optional[str] = None,
        wait_margin: float = 0.1,
    ):
        """
        Initialize the rate limiter.

        Args:
            max_concurrent: Maximum number of concurrent requests allowed
            max_requests: Maximum number of requests allowed in the time period
            time_period: Time period in seconds for the request limit
            conservative: If True, use a more conservative limit to avoid edge cases
            name: Optional name for this rate limiter instance (useful for logging)
            wait_margin: Extra seconds a caller sleeps past the moment a slot in the
                time window opens. A safety margin against clock differences with
                the server; 0 gives the full allowed throughput
        """
        if max_concurrent <= 0:
            raise ValueError("max_concurrent must be greater than 0")
        if max_requests <= 0:
            raise ValueError("max_requests must be greater than 0")
        if time_period <= 0:
            raise ValueError("time_period must be greater than 0")
        if wait_margin < 0:
            raise ValueError("wait_margin must not be negative")

        self.max_concurrent = max_concurrent
        self.max_requests = max_requests
        self.time_period = time_period
        self.name = name or "default"
        self.wait_margin = wait_margin

        # Leave a margin of one request: if the API allows 5 per minute, allow 4
        self._effective_max_requests = (
            max(1, max_requests - 1) if conservative else max_requests
        )

        # Created on first use, inside the running event loop: on Python 3.9
        # asyncio primitives cannot be created without one
        self._semaphore: Optional[asyncio.BoundedSemaphore] = None
        self._lock: Optional[asyncio.Lock] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

        # Start times of recent requests, from time.monotonic() so that changes
        # to the system clock cannot stall or loosen the limit
        self.request_times: Deque[float] = deque()

        self._metrics: Dict[str, Any] = {
            "total_requests": 0,
            "current_requests": 0,
            "rate_limit_delays": 0,
            "total_delay_time": 0.0,
            "errors": 0,  # always 0; kept so that get_metrics() keeps its keys
        }

        logger.info(
            f"DualRateLimiter '{self.name}' initialized with: concurrent={max_concurrent}, "
            f"requests={self._effective_max_requests}/{time_period}s"
        )

    @property
    def semaphore(self) -> asyncio.BoundedSemaphore:
        """Semaphore limiting concurrent requests. Bounded, so that releasing
        more often than acquiring cannot raise the limit."""
        if self._semaphore is None:
            self._semaphore = asyncio.BoundedSemaphore(self.max_concurrent)
        return self._semaphore

    @semaphore.setter
    def semaphore(self, value: asyncio.BoundedSemaphore) -> None:
        self._semaphore = value

    @property
    def lock(self) -> asyncio.Lock:
        """Unused: nothing in the limiter awaits while it updates its state.
        Kept because it has been a public attribute since 1.0."""
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    @lock.setter
    def lock(self, value: asyncio.Lock) -> None:
        self._lock = value

    def _bind_to_running_loop(self) -> None:
        """
        Start with a fresh semaphore when the event loop has changed.

        asyncio primitives belong to the loop they first waited in, so a limiter
        created at module level and used from a second asyncio.run() would fail.
        The request history is kept: the time-based limit spans event loops.

        Raises:
            RuntimeError: If the previous loop is still running, which means two
                threads are using the limiter at the same time
        """
        loop = asyncio.get_running_loop()
        if loop is not self._loop:
            if self._loop is not None and self._loop.is_running():
                raise RuntimeError(
                    f"DualRateLimiter '{self.name}' is in use by another running "
                    "event loop; it cannot be shared between event loops that "
                    "run at the same time"
                )
            self._loop = loop
            self._semaphore = asyncio.BoundedSemaphore(self.max_concurrent)
            self._lock = None
            self._metrics["current_requests"] = 0

    def _clean_old_requests(self, now: float) -> None:
        """Remove request timestamps that are outside the time period."""
        cutoff_time = now - self.time_period
        while self.request_times and self.request_times[0] <= cutoff_time:
            self.request_times.popleft()

    async def acquire(self) -> None:
        """
        Acquire permission to make a request.
        This blocks until both rate limits allow the request.
        """
        self._bind_to_running_loop()

        # Concurrent limit first: a caller waiting on the time limit holds a slot
        await self.semaphore.acquire()
        self._metrics["current_requests"] += 1

        try:
            delay_start = None
            while True:
                now = time.monotonic()
                self._clean_old_requests(now)
                current_count = len(self.request_times)

                if current_count < self._effective_max_requests:
                    self.request_times.append(now)
                    self._metrics["total_requests"] += 1
                    if delay_start is not None:
                        delay_time = now - delay_start
                        self._metrics["total_delay_time"] += delay_time
                        logger.debug(
                            f"[{self.name}] Request allowed after waiting {delay_time:.2f}s"
                        )
                    return

                if delay_start is None:
                    delay_start = now
                    self._metrics["rate_limit_delays"] += 1

                # Sleep until the oldest request leaves the window, plus the margin
                wait_time = (
                    self.request_times[0] + self.time_period - now + self.wait_margin
                )
                logger.info(
                    f"[{self.name}] Rate limit reached ({current_count}/{self._effective_max_requests}), "
                    f"waiting {wait_time:.2f}s for a slot to open"
                )
                await asyncio.sleep(wait_time)
        except BaseException:
            # Cancelled while waiting: give the concurrency slot back
            self.release()
            raise

    def release(self) -> None:
        """Release the semaphore to allow another concurrent request."""
        try:
            if self._semaphore is None:
                raise ValueError("release() called before any acquire()")
            self._semaphore.release()
            self._metrics["current_requests"] = max(
                0, self._metrics["current_requests"] - 1
            )
        except ValueError:
            # This means we're releasing more than we acquired
            logger.warning(
                f"[{self.name}] Attempted to release rate limiter that wasn't acquired"
            )

    async def __aenter__(self) -> "DualRateLimiter":
        """Context manager entry - acquires permission to make a request."""
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - releases the semaphore."""
        self.release()

    def limit(self):
        """
        Decorator for rate limiting async functions.

        Usage:
            @rate_limiter.limit()
            async def my_function():
                pass
        """

        def decorator(func):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                async with self:
                    return await func(*args, **kwargs)

            return wrapper

        return decorator

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current metrics for this rate limiter.

        Returns:
            Dictionary with metrics including total requests, current concurrent
            requests, rate limit delays, etc.
        """
        return {
            **self._metrics,
            "current_queue_size": len(self.request_times),
            "max_concurrent": self.max_concurrent,
            "max_requests_per_period": self._effective_max_requests,
            "time_period": self.time_period,
        }

    def reset_metrics(self) -> None:
        """Reset all metrics counters except for current state values."""
        self._metrics.update(
            total_requests=0, rate_limit_delays=0, total_delay_time=0.0, errors=0
        )
