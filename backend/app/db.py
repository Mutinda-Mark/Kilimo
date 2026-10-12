from __future__ import annotations

import asyncio
from typing import Optional

import asyncpg
from pgvector.asyncpg import register_vector

from app.config import settings


_pool: Optional[asyncpg.Pool] = None
_pool_loop: Optional[asyncio.AbstractEventLoop] = None


async def _init_connection(
    conn: asyncpg.Connection,
) -> None:
    """Initialize each PostgreSQL connection."""

    await register_vector(conn)


async def get_pool() -> asyncpg.Pool:
    """
    Return a PostgreSQL connection pool for the current event loop.

    pytest-asyncio may create a different event loop for each test.
    asyncpg pools cannot safely be reused across different event loops,
    so a new pool is created when the current loop changes.
    """

    global _pool
    global _pool_loop

    current_loop = asyncio.get_running_loop()

    # No pool exists yet.
    if _pool is None:
        _pool = await asyncpg.create_pool(
            dsn=settings.database_url,
            min_size=1,
            max_size=5,
            init=_init_connection,
        )

        _pool_loop = current_loop

        return _pool

    # The existing pool belongs to the current event loop.
    if _pool_loop is current_loop:
        return _pool

    # The existing pool belongs to a different event loop.
    #
    # This commonly happens during pytest-asyncio tests because
    # each test may receive a fresh event loop.
    old_pool = _pool
    old_loop = _pool_loop

    _pool = None
    _pool_loop = None

    # If the old loop is still running, we can safely terminate
    # the old pool.
    #
    # If the old loop has already been closed, attempting to call
    # old_pool.terminate() can itself raise:
    #
    # RuntimeError: Event loop is closed
    #
    # In that situation the old loop has already released control
    # of the application, so we simply discard the stale pool.
    if old_loop is not None and not old_loop.is_closed():
        try:
            old_pool.terminate()
        except RuntimeError as exc:
            if "Event loop is closed" not in str(exc):
                raise

    # Create a new pool for the current event loop.
    _pool = await asyncpg.create_pool(
        dsn=settings.database_url,
        min_size=1,
        max_size=5,
        init=_init_connection,
    )

    _pool_loop = current_loop

    return _pool


async def close_pool() -> None:
    """
    Close the active PostgreSQL pool.

    This is used during FastAPI shutdown and can also safely be
    called when no pool exists.
    """

    global _pool
    global _pool_loop

    if _pool is None:
        return

    pool = _pool
    pool_loop = _pool_loop

    _pool = None
    _pool_loop = None

    current_loop = asyncio.get_running_loop()

    # Only perform an async close if the pool belongs to the
    # currently running event loop.
    if pool_loop is current_loop:
        try:
            await pool.close()
        except RuntimeError as exc:
            if "Event loop is closed" not in str(exc):
                raise
        return

    # The pool belongs to another event loop.
    #
    # If that loop is already closed, we cannot safely perform
    # asyncpg cleanup through it. Simply discard the stale pool.
    if pool_loop is None or pool_loop.is_closed():
        return

    # The other loop still exists, but it is not the current loop.
    # Avoid trying to await operations on a different event loop.
    try:
        pool.terminate()
    except RuntimeError as exc:
        if "Event loop is closed" not in str(exc):
            raise