"""
Async Dual Rate Limiter

A production-ready asyncio-based rate limiter for Python that enforces
both concurrent and time-based rate limits.
"""

from importlib.metadata import PackageNotFoundError, version

from .async_limiter import DualRateLimiter

# The version lives in pyproject.toml only
try:
    __version__ = version("async-limiter")
except PackageNotFoundError:  # source tree that has not been installed
    __version__ = "0.0.0"

__all__ = ["DualRateLimiter"]
