"""TTL memory cache to minimize API calls."""

from __future__ import annotations

import time
from typing import Any


class TTLCache:
    """Simple in-memory cache with per-key TTL expiration.

    Usage:
        cache = TTLCache(default_ttl=1800)  # 30 minutes
        cache.set("key", value)
        result = cache.get("key")  # None if expired
    """

    def __init__(self, default_ttl: int = 1800) -> None:
        self._store: dict[str, tuple[Any, float]] = {}
        self._default_ttl = default_ttl

    def get(self, key: str) -> Any | None:
        """Get value if exists and not expired."""
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if time.monotonic() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value with TTL (seconds). Uses default_ttl if not specified."""
        actual_ttl = ttl if ttl is not None else self._default_ttl
        expires_at = time.monotonic() + actual_ttl
        self._store[key] = (value, expires_at)

    def invalidate(self, key: str) -> None:
        """Remove a specific key."""
        self._store.pop(key, None)

    def invalidate_prefix(self, prefix: str) -> None:
        """Remove all keys starting with prefix."""
        keys_to_remove = [k for k in self._store if k.startswith(prefix)]
        for k in keys_to_remove:
            del self._store[k]

    def clear(self) -> None:
        """Remove all entries."""
        self._store.clear()

    def stats(self) -> dict[str, int]:
        """Return cache statistics."""
        now = time.monotonic()
        total = len(self._store)
        alive = sum(1 for _, (__, exp) in self._store.items() if exp > now)
        return {"total": total, "alive": alive, "expired": total - alive}
