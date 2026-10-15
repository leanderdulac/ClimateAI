"""Small in-memory LRU with TTL. Not process-safe; quote-path only."""

from __future__ import annotations

from collections import OrderedDict
from time import monotonic
from typing import Generic, Hashable, Optional, TypeVar

T = TypeVar("T")


class TtlLruCache(Generic[T]):
    def __init__(self, maxsize: int = 32, ttl_seconds: float = 86400.0) -> None:
        self.maxsize = maxsize
        self.ttl_seconds = ttl_seconds
        self._data: OrderedDict[Hashable, tuple[float, T]] = OrderedDict()

    def get(self, key: Hashable) -> Optional[T]:
        item = self._data.get(key)
        if item is None:
            return None
        expires_at, value = item
        if monotonic() > expires_at:
            self._data.pop(key, None)
            return None
        self._data.move_to_end(key)
        return value

    def set(self, key: Hashable, value: T) -> T:
        self._data[key] = (monotonic() + self.ttl_seconds, value)
        self._data.move_to_end(key)
        while len(self._data) > self.maxsize:
            self._data.popitem(last=False)
        return value

    def __len__(self) -> int:
        return len(self._data)

    def clear(self) -> None:
        self._data.clear()
