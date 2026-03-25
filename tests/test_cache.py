"""Tests for TTL memory cache."""

import time

from archflow.core.cache import TTLCache


class TestTTLCache:
    def test_set_and_get(self):
        cache = TTLCache(default_ttl=60)
        cache.set("key1", {"data": "value"})
        assert cache.get("key1") == {"data": "value"}

    def test_returns_none_for_missing_key(self):
        cache = TTLCache()
        assert cache.get("nonexistent") is None

    def test_ttl_expiration(self):
        cache = TTLCache(default_ttl=1)
        cache.set("key1", "value", ttl=0)
        time.sleep(0.01)
        assert cache.get("key1") is None

    def test_custom_ttl_per_key(self):
        cache = TTLCache(default_ttl=0)
        cache.set("short", "val", ttl=0)
        cache.set("long", "val", ttl=3600)
        time.sleep(0.01)
        assert cache.get("short") is None
        assert cache.get("long") == "val"

    def test_invalidate(self):
        cache = TTLCache()
        cache.set("key1", "value")
        cache.invalidate("key1")
        assert cache.get("key1") is None

    def test_invalidate_prefix(self):
        cache = TTLCache()
        cache.set("jira:issue:KAN-1", "val1")
        cache.set("jira:issue:KAN-2", "val2")
        cache.set("github:pr:1", "val3")
        cache.invalidate_prefix("jira:")
        assert cache.get("jira:issue:KAN-1") is None
        assert cache.get("jira:issue:KAN-2") is None
        assert cache.get("github:pr:1") == "val3"

    def test_clear(self):
        cache = TTLCache()
        cache.set("a", 1)
        cache.set("b", 2)
        cache.clear()
        assert cache.get("a") is None
        assert cache.get("b") is None

    def test_stats(self):
        cache = TTLCache(default_ttl=3600)
        cache.set("alive", "val")
        cache.set("dead", "val", ttl=0)
        time.sleep(0.01)
        stats = cache.stats()
        assert stats["total"] == 2
        assert stats["alive"] == 1
        assert stats["expired"] == 1
