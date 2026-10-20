from __future__ import annotations

import asyncio
import math
import time

from collections import deque
from dataclasses import dataclass

from fastapi import (
    HTTPException,
    Request,
    status,
)


@dataclass(frozen=True)
class RateLimitResult:
    """
    Result of one rate-limit check.
    """

    allowed: bool
    limit: int
    remaining: int
    retry_after_seconds: int


class InMemoryRateLimiter:
    """
    Sliding-window rate limiter stored in application memory.

    State is local to the current Python process and resets when
    the application restarts.
    """

    def __init__(
        self,
        *,
        limit: int,
        window_seconds: int,
    ) -> None:

        if limit <= 0:
            raise ValueError(
                "Rate-limit request count must be positive."
            )

        if window_seconds <= 0:
            raise ValueError(
                "Rate-limit window must be positive."
            )

        self.limit = limit
        self.window_seconds = window_seconds

        self._requests: dict[
            str,
            deque[float],
        ] = {}

        self._lock = asyncio.Lock()

    async def check(
        self,
        key: str,
    ) -> RateLimitResult:
        """
        Check and record one request for the supplied client key.
        """

        now = time.monotonic()

        cutoff = (
            now
            - self.window_seconds
        )

        async with self._lock:

            timestamps = (
                self._requests.setdefault(
                    key,
                    deque(),
                )
            )

            while (
                timestamps
                and timestamps[0] <= cutoff
            ):
                timestamps.popleft()

            if (
                len(timestamps)
                >= self.limit
            ):
                oldest = timestamps[0]

                retry_after = max(
                    1,
                    math.ceil(
                        self.window_seconds
                        - (
                            now
                            - oldest
                        )
                    ),
                )

                return RateLimitResult(
                    allowed=False,
                    limit=self.limit,
                    remaining=0,
                    retry_after_seconds=retry_after,
                )

            timestamps.append(
                now
            )

            remaining = max(
                0,
                self.limit
                - len(timestamps),
            )

            return RateLimitResult(
                allowed=True,
                limit=self.limit,
                remaining=remaining,
                retry_after_seconds=0,
            )

    async def clear(self) -> None:
        """
        Clear all stored counters.

        Primarily useful for automated tests.
        """

        async with self._lock:
            self._requests.clear()


def client_identifier(
    request: Request,
) -> str:
    """
    Determine the current direct network client.

    X-Forwarded-For is deliberately not trusted here because proxy
    trust configuration is deployment-specific and accepting an
    arbitrary forwarded header would allow clients to spoof their
    rate-limit identity.
    """

    if request.client is None:
        return "unknown"

    host = (
        request.client.host
        or ""
    ).strip()

    return (
        host
        or "unknown"
    )


async def enforce_rate_limit(
    *,
    request: Request,
    limiter: InMemoryRateLimiter,
    scope: str,
) -> None:
    """
    Enforce one configured API rate limit.

    The scope keeps counters for different endpoints independent
    even when the same client accesses both endpoints.
    """

    client_key = (
        f"{scope}:"
        f"{client_identifier(request)}"
    )

    result = await limiter.check(
        client_key
    )

    if result.allowed:
        return

    raise HTTPException(
        status_code=(
            status.HTTP_429_TOO_MANY_REQUESTS
        ),
        detail=(
            "Too many requests. "
            "Please try again shortly."
        ),
        headers={
            "Retry-After": str(
                result.retry_after_seconds
            ),
        },
    )