"""
Caching utilities for Agent Council system.

Provides decorators and utilities for caching expensive operations.
Implements cache invalidation and TTL support.
"""

import hashlib
import json
import time
from functools import wraps
from typing import Any, Callable, Optional

from app.utils.logging import get_logger

logger = get_logger(__name__)


class SimpleCache:
    """
    Simple in-memory cache with TTL support.

    For production, consider replacing with Redis or Memcached.
    Implements Open/Closed Principle: extend for different backends.
    """

    def __init__(self, default_ttl: int = 300):
        """
        Initialize cache.

        Args:
            default_ttl: Default time-to-live in seconds
        """
        self._cache: dict[str, tuple[Any, float]] = {}
        self.default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if expired/not found
        """
        if key not in self._cache:
            return None

        value, expiry = self._cache[key]
        if time.time() > expiry:
            del self._cache[key]
            logger.debug("cache_expired", key=key)
            return None

        logger.debug("cache_hit", key=key)
        return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        ttl = ttl or self.default_ttl
        expiry = time.time() + ttl
        self._cache[key] = (value, expiry)
        logger.debug("cache_set", key=key, ttl=ttl)

    def delete(self, key: str) -> None:
        """
        Delete value from cache.

        Args:
            key: Cache key
        """
        if key in self._cache:
            del self._cache[key]
            logger.debug("cache_deleted", key=key)

    def clear(self) -> None:
        """Clear all cached values."""
        self._cache.clear()
        logger.info("cache_cleared")

    def cleanup_expired(self) -> None:
        """Remove all expired entries from cache."""
        current_time = time.time()
        expired_keys = [
            key for key, (_, expiry) in self._cache.items()
            if current_time > expiry
        ]
        for key in expired_keys:
            del self._cache[key]
        if expired_keys:
            logger.info("cache_cleanup", expired_count=len(expired_keys))


# Global cache instance
_cache: Optional[SimpleCache] = None


def get_cache() -> SimpleCache:
    """
    Get global cache instance.

    Returns:
        SimpleCache singleton
    """
    global _cache
    if _cache is None:
        _cache = SimpleCache()
    return _cache


def generate_cache_key(*args: Any, **kwargs: Any) -> str:
    """
    Generate cache key from function arguments.

    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        Hash-based cache key
    """
    key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
    return hashlib.sha256(key_data.encode()).hexdigest()


def cached(ttl: Optional[int] = None, key_prefix: str = ""):
    """
    Decorator for caching function results.

    Args:
        ttl: Time-to-live in seconds (uses cache default if None)
        key_prefix: Prefix for cache key (typically function name)

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            cache = get_cache()
            cache_key = f"{key_prefix or func.__name__}:{generate_cache_key(*args, **kwargs)}"

            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl=ttl)
            return result

        return wrapper
    return decorator


def invalidate_cache(key_prefix: str = "") -> None:
    """
    Invalidate all cache entries with given prefix.

    Args:
        key_prefix: Prefix to match for invalidation
    """
    cache = get_cache()
    if key_prefix:
        # For now, we don't have prefix matching in SimpleCache
        # In production, use Redis with pattern matching
        logger.warning("cache_prefix_invalidation_not_implemented", prefix=key_prefix)
    else:
        cache.clear()

