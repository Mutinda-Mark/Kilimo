import pytest

from app.security.rate_limit import (
    InMemoryRateLimiter,
)


@pytest.mark.asyncio
async def test_rate_limiter_allows_requests_below_limit():

    limiter = InMemoryRateLimiter(
        limit=3,
        window_seconds=60,
    )

    first = await limiter.check(
        "client-1"
    )

    second = await limiter.check(
        "client-1"
    )

    assert first.allowed is True
    assert second.allowed is True

    assert (
        second.remaining
        == 1
    )


@pytest.mark.asyncio
async def test_rate_limiter_blocks_request_above_limit():

    limiter = InMemoryRateLimiter(
        limit=2,
        window_seconds=60,
    )

    first = await limiter.check(
        "client-1"
    )

    second = await limiter.check(
        "client-1"
    )

    third = await limiter.check(
        "client-1"
    )

    assert first.allowed is True
    assert second.allowed is True

    assert third.allowed is False

    assert (
        third.remaining
        == 0
    )

    assert (
        third.retry_after_seconds
        >= 1
    )


@pytest.mark.asyncio
async def test_rate_limiter_tracks_clients_independently():

    limiter = InMemoryRateLimiter(
        limit=1,
        window_seconds=60,
    )

    client_one = (
        await limiter.check(
            "client-1"
        )
    )

    client_two = (
        await limiter.check(
            "client-2"
        )
    )

    assert client_one.allowed is True
    assert client_two.allowed is True


@pytest.mark.asyncio
async def test_rate_limiter_clear_resets_counters():

    limiter = InMemoryRateLimiter(
        limit=1,
        window_seconds=60,
    )

    first = await limiter.check(
        "client-1"
    )

    blocked = await limiter.check(
        "client-1"
    )

    assert first.allowed is True
    assert blocked.allowed is False

    await limiter.clear()

    after_clear = (
        await limiter.check(
            "client-1"
        )
    )

    assert (
        after_clear.allowed
        is True
    )


def test_rate_limiter_rejects_invalid_limit():

    with pytest.raises(
        ValueError
    ):
        InMemoryRateLimiter(
            limit=0,
            window_seconds=60,
        )


def test_rate_limiter_rejects_invalid_window():

    with pytest.raises(
        ValueError
    ):
        InMemoryRateLimiter(
            limit=10,
            window_seconds=0,
        )
        