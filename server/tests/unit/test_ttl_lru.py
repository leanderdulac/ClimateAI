"""In-memory TTL LRU used by the quote overlay caches."""

from time import sleep

import pytest

from lib.ttl_lru import TtlLruCache


@pytest.mark.unit
def test_ttl_lru_get_set_and_lru_eviction():
    cache = TtlLruCache(maxsize=2, ttl_seconds=60)
    cache.set("a", 1)
    cache.set("b", 2)
    assert cache.get("a") == 1
    cache.set("c", 3)
    assert cache.get("b") is None
    assert cache.get("a") == 1
    assert cache.get("c") == 3
    assert len(cache) == 2


@pytest.mark.unit
def test_ttl_lru_expires():
    cache = TtlLruCache(maxsize=4, ttl_seconds=0.05)
    cache.set("k", "v")
    assert cache.get("k") == "v"
    sleep(0.08)
    assert cache.get("k") is None
