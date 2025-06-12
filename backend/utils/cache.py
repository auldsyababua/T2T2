from __future__ import annotations

import os
import time
from typing import Any, Dict, Tuple

from utils.logging import setup_logger

# Optional dependency – available when `upstash-redis` is installed.
try:
    from upstash_redis import AsyncRedis  # type: ignore
except ImportError:  # pragma: no cover
    AsyncRedis = None  # type: ignore

logger = setup_logger(__name__)

class Cache:
    """Simple async cache wrapper using Upstash Redis with in-memory fallback.

    The implementation purposely keeps the public surface minimal (``get`` and
    ``set``) so we can easily swap the backend in the future without touching
    call-sites.
    """

    _memory_store: Dict[str, Tuple[Any, float]]

    def __init__(self) -> None:
        self._memory_store = {}
        self._redis = None

        # Attempt to create a reusable AsyncRedis client if credentials exist
        if AsyncRedis is not None:
            redis_url = os.getenv("UPSTASH_REDIS_REST_URL") or os.getenv("REDIS_URL")
            redis_token = os.getenv("UPSTASH_REDIS_REST_TOKEN")
            if redis_url and redis_token:
                try:
                    self._redis = AsyncRedis(url=redis_url, token=redis_token)
                    # Test the connection lazily – first command will raise if bad creds
                    logger.debug("Cache: Using Upstash Redis backend")
                except Exception as exc:  # pragma: no cover
                    logger.warning("Cache: Failed to initialise Upstash Redis – falling back to memory. (%s)", exc)
                    self._redis = None
            else:
                logger.debug("Cache: Redis credentials not set – using in-memory store")
        else:
            logger.debug("Cache: upstash-redis package not installed – using in-memory store")

    # ---------------------------------------------------------------------
    # Public helpers
    # ---------------------------------------------------------------------

    async def get(self, key: str) -> Any | None:
        """Return cached value or ``None`` if missing/expired."""
        if self._redis is not None:
            try:
                return await self._redis.get(key)  # type: ignore[arg-type]
            except Exception as exc:  # pragma: no cover
                logger.warning("Cache: Redis get failed – %s", exc)
                # fall back to memory

        return self._get_memory(key)

    async def set(self, key: str, value: Any, ttl: int = 60) -> None:
        """Store *value* under *key* with optional *ttl* (seconds)."""
        if self._redis is not None:
            try:
                await self._redis.set(key, value, ex=ttl)  # type: ignore[arg-type]
                return
            except Exception as exc:  # pragma: no cover
                logger.warning("Cache: Redis set failed – %s", exc)
                # fall back to memory

        self._set_memory(key, value, ttl)

    # ------------------------------------------------------------------
    # Internal helpers – memory backend
    # ------------------------------------------------------------------

    def _get_memory(self, key: str) -> Any | None:
        value_exp = self._memory_store.get(key)
        if value_exp is None:
            return None
        value, exp = value_exp
        if exp < time.time():
            # expired – cleanup
            self._memory_store.pop(key, None)
            return None
        return value

    def _set_memory(self, key: str, value: Any, ttl: int) -> None:
        self._memory_store[key] = (value, time.time() + ttl)


# Singleton instance – importable from anywhere
cache = Cache() 