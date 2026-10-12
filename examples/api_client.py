#!/usr/bin/env python3
"""
Fetch 20 posts and their comments from the JSONPlaceholder API, at most
5 requests at a time and 10 requests per 5 seconds.

Usage:
    pip install aiohttp
    python api_client.py
"""

import asyncio
import logging
import time

from aiohttp import ClientSession

from async_limiter import DualRateLimiter

BASE_URL = "https://jsonplaceholder.typicode.com"

# One limiter for the whole API, shared by every request
limiter = DualRateLimiter(
    max_concurrent=5, max_requests=10, time_period=5.0, name="jsonplaceholder"
)


async def get(session: ClientSession, path: str):
    """Make a rate-limited GET request and return the decoded JSON."""
    async with limiter:
        async with session.get(f"{BASE_URL}/{path}") as response:
            response.raise_for_status()
            return await response.json()


async def main():
    # Show the limiter's own log lines, including each wait
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

    paths = []
    for post_id in range(1, 21):
        paths += [f"posts/{post_id}", f"posts/{post_id}/comments"]

    start = time.monotonic()
    async with ClientSession() as session:
        # Started all at once; the limiter spaces them out
        results = await asyncio.gather(*[get(session, path) for path in paths])

    print(f"Fetched {len(results)} resources in {time.monotonic() - start:.1f}s")
    print(limiter.get_metrics())


if __name__ == "__main__":
    asyncio.run(main())
