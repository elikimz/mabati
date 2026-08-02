"""
Simple in-memory caching layer for public API endpoints.

Zero-cost, zero-configuration cache that stores results in memory.
No external service needed — works immediately out of the box.
"""
import json
import hashlib
import logging
import time
from functools import wraps
from typing import Any, Callable, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# ── In-memory store ──────────────────────────────────────────────────────────

_cache_store: Dict[str, Tuple[Any, float]] = {}  # key -> (value, expiry_timestamp)


def _is_expired(key: str) -> bool:
    """Check if a cached entry has expired."""
    if key not in _cache_store:
        return True
    _, expiry = _cache_store[key]
    return time.time() > expiry


def _get_query_string_key(params: dict) -> str:
    """Hash query parameters into a cache-friendly key."""
    raw = json.dumps(params, default=str, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


# ── Decorator for caching GET endpoints ───────────────────────────────────────

def cache_response(prefix: str, ttl: int = 300):
    """
    Decorator that caches the response of a GET endpoint in memory.

    Usage:
        @router.get("/products")
        @cache_response(prefix="products", ttl=300)
        async def list_products(...):
            ...

    Args:
        prefix: Cache namespace (e.g. "products", "categories")
        ttl: Time-to-live in seconds (default: 5 minutes)
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key from prefix + function name + params
            key = f"{prefix}:{func.__name__}:{_get_query_string_key(kwargs)}"

            # Try to read from cache
            if not _is_expired(key):
                cached_value, _ = _cache_store[key]
                logger.debug("Cache HIT: %s", key)
                return cached_value

            # Cache miss — execute the actual function
            logger.debug("Cache MISS: %s", key)
            result = await func(*args, **kwargs)

            # Store in cache
            if result is not None:
                _cache_store[key] = (result, time.time() + ttl)

            return result
        return wrapper
    return decorator


# ── Cache invalidation ────────────────────────────────────────────────────────

def invalidate_cache(prefix: Optional[str] = None, key: Optional[str] = None):
    """
    Invalidate cached entries.
    - Pass key to delete a specific cache entry.
    - Pass prefix to delete all entries matching that prefix.
    """
    if key:
        _cache_store.pop(key, None)
        logger.info("Cache invalidated: %s", key)
    elif prefix:
        removed = 0
        keys_to_delete = [k for k in _cache_store if k.startswith(f"{prefix}:")]
        for k in keys_to_delete:
            del _cache_store[k]
            removed += 1
        logger.info("Cache invalidated %d keys matching prefix '%s'", removed, prefix)


def invalidate_all_caches():
    """Invalidate the entire cache."""
    _cache_store.clear()
    logger.info("Full cache flush completed")


# ── Startup / shutdown (no-op for in-memory) ─────────────────────────────────

async def connect_redis():
    """No-op — in-memory cache needs no connection."""
    logger.info("In-memory cache initialized (no external service required)")


async def close_redis():
    """Clear cache on shutdown."""
    _cache_store.clear()
