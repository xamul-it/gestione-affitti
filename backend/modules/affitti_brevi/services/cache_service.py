"""
Cache Service

Simple in-memory caching for frequently accessed data.
Uses TTL (time-to-live) to automatically expire stale data.

For production, consider using Redis or Memcached.
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Dict
import threading
import logging

logger = logging.getLogger(__name__)


class CacheService:
    """
    Simple in-memory cache with TTL support

    Thread-safe implementation for multi-worker environments.
    """

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found or expired
        """
        with self._lock:
            if key not in self._cache:
                return None

            entry = self._cache[key]
            expires_at = entry['expires_at']

            # Check if expired
            if datetime.now(timezone.utc) > expires_at:
                del self._cache[key]
                logger.debug(f"Cache expired: {key}")
                return None

            logger.debug(f"Cache hit: {key}")
            return entry['value']

    def set(self, key: str, value: Any, ttl_seconds: int = 3600):
        """
        Set value in cache with TTL

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds (default: 1 hour)
        """
        with self._lock:
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
            self._cache[key] = {
                'value': value,
                'expires_at': expires_at
            }
            logger.debug(f"Cache set: {key} (TTL: {ttl_seconds}s)")

    def delete(self, key: str):
        """
        Delete value from cache

        Args:
            key: Cache key
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Cache deleted: {key}")

    def clear(self):
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
            logger.info("Cache cleared")

    def clear_expired(self):
        """
        Remove expired entries from cache

        Call this periodically to prevent memory buildup.
        """
        with self._lock:
            now = datetime.now(timezone.utc)
            expired_keys = [
                key for key, entry in self._cache.items()
                if now > entry['expires_at']
            ]

            for key in expired_keys:
                del self._cache[key]

            if expired_keys:
                logger.info(f"Cleared {len(expired_keys)} expired cache entries")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dict with cache stats
        """
        with self._lock:
            now = datetime.now(timezone.utc)
            active_entries = sum(
                1 for entry in self._cache.values()
                if now <= entry['expires_at']
            )
            expired_entries = len(self._cache) - active_entries

            return {
                'total_entries': len(self._cache),
                'active_entries': active_entries,
                'expired_entries': expired_entries
            }


# Global cache instance
_cache = CacheService()


def get_cache() -> CacheService:
    """Get global cache instance"""
    return _cache


# Helper functions for common cache patterns

def cache_key(*parts) -> str:
    """
    Generate cache key from parts

    Args:
        *parts: Key components

    Returns:
        Cache key string

    Example:
        cache_key('calendario', 'overview', tenant_id, '2025-01-01')
        -> 'calendario:overview:tenant_123:2025-01-01'
    """
    return ':'.join(str(p) for p in parts)


def cached(ttl_seconds: int = 3600):
    """
    Decorator for caching function results

    Args:
        ttl_seconds: Time to live in seconds

    Example:
        @cached(ttl_seconds=1800)
        def expensive_query(tenant_id, date):
            # ... expensive operation
            return result
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and args
            key_parts = [func.__name__] + list(args) + [f"{k}={v}" for k, v in sorted(kwargs.items())]
            key = cache_key(*key_parts)

            # Try to get from cache
            cache = get_cache()
            cached_value = cache.get(key)
            if cached_value is not None:
                return cached_value

            # Call function and cache result
            result = func(*args, **kwargs)
            cache.set(key, result, ttl_seconds)
            return result

        return wrapper
    return decorator
