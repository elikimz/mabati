"""
Redis caching layer for public API endpoints.

Provides a decorator-based caching system that:
- Caches public GET responses in Redis for configurable TTLs
- Falls back gracefully to uncached operation if Redis is unavailable
- Supports automatic cache invalidation by pattern/key
"""
import json
import hashlib
import logging
import os
from functools import wraps
from typing import Any, Callable, Optional

import redis.asyncio as aioredis
from fastapi import Response

logger = logging.getLogger(__name__)

# ── Redis connection ──────────────────────────────────────────────────────────

REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CACHE_TTL_DEFAULT: int = int(os.getenv("CACHE_TTL", "300"))  # 5 minutes default
CACHE_TTL_LONG: int = int(os.getenv("CACHE_TTL_LONG", "900"))  # 15 minutes for stable data

_redis_client: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    """Get or create a Redis client instance (singleton)."""
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)
            await _redis_client.ping()
            logger.info("Redis connected at %s", REDIS_URL)
        except (aioredis.ConnectionError, aioredis.TimeoutError) as exc:
            logger.warning("Redis unavailable (%s) — caching disabled", exc)
            _redis_client = None
    return _redis_client


# ── Cache key helpers ─────────────────────────────────────────────────────────

def _make_cache_key(prefix: str, **kwargs: Any) -> str:
    """Generate a deterministic cache key from prefix + query parameters."""
    # Sort kwargs for deterministic hashing
    sorted_items = sorted(kwargs.items())
    raw = f"{prefix}:{json.dumps(sorted_items, default=str)}"
    return f"mabati:{prefix}:{hashlib.sha256(raw.encode()).hexdigest()[:12]}"


def _get_query_string_key(params: dict) -> str:
    """Hash query parameters into a cache-friendly key."""
    return hashlib.sha256(json.dumps(params, default=str, sort_keys=True).encode()).hexdigest()[:12]


# ── Decorator for caching GET endpoints ───────────────────────────────────────

def cache_response(
    prefix: str,
    ttl: Optional[int] = None,
    key_func: Optional[Callable] = None,
):
    """
    Decorator that caches the JSON response of a GET endpoint in Redis.

    Usage:
        @router.get("/products")
        @cache_response(prefix="products", ttl=300)
        async def list_products(...):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key from function name + query params
            key = f"mabati:{prefix}:{_get_query_string_key(kwargs)}"
            ttl_val = ttl or CACHE_TTL_DEFAULT

            # Try to read from cache
            try:
                client = await get_redis()
                if client:
                    cached = await client.get(key)
                    if cached is not None:
                        logger.debug("Cache HIT: %s", key)
                        return json.loads(cached)
                    logger.debug("Cache MISS: %s", key)
            except Exception as exc:
                logger.warning("Redis read error on %s: %s — falling back to DB", key, exc)

            # Execute the actual function
            result = await func(*args, **kwargs)

            # Write to cache
            try:
                if client and result is not None:
                    serialized = json.dumps(
                        result,
                        default=str,
                        ensure_ascii=False,
                    )
                    await client.setex(key, ttl_val, serialized)
            except Exception as exc:
                logger.warning("Redis write error on %s: %s", key, exc)

            return result
        return wrapper
    return decorator


# ── Cache invalidation ────────────────────────────────────────────────────────

async def invalidate_cache(prefix: Optional[str] = None, key: Optional[str] = None):
    """
    Invalidate cached entries.
    - Pass key to delete a specific cache entry.
    - Pass prefix to delete all entries matching that prefix.
    - Pass neither to flush the entire cache (use with caution).
    """
    try:
        client = await get_redis()
        if not client:
            return

        if key:
            await client.delete(key)
            logger.info("Cache invalidated: %s", key)
        elif prefix:
            pattern = f"mabati:{prefix}:*"
            cursor = 0
            count = 0
            while True:
                cursor, keys = await client.scan(cursor, match=pattern, count=100)
                if keys:
                    count += await client.delete(*keys)
                if cursor == 0:
                    break
            logger.info("Cache invalidated %d keys matching prefix '%s'", count, prefix)
        else:
            await client.flushdb()
            logger.info("Full cache flush completed")

    except Exception as exc:
        logger.warning("Cache invalidation error: %s", exc)


async def invalidate_all_caches():
    """Invalidate all cached public data (products, categories, site content, etc.)."""
    prefixes = ["products", "categories", "site_content", "banners", "gallery", "seo"]
    for prefix in prefixes:
        await invalidate_cache(prefix=prefix)


# ── Startup / shutdown ───────────────────────────────────────────────────────

async def connect_redis():
    """Called at app startup to pre-connect Redis."""
    await get_redis()


async def close_redis():
    """Called at app shutdown to close Redis connection."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
