import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock
from lib.redis_cache import RedisCache

@pytest.mark.asyncio
async def test_cache_stampede_protection():
    # Setup
    cache = RedisCache(enabled=True)
    cache._client = AsyncMock()
    cache._client.get.return_value = None  # Cache miss
    cache._client.setex.return_value = True

    # Mock factory that is slow and tracks calls
    factory_call_count = 0
    
    async def slow_factory():
        nonlocal factory_call_count
        factory_call_count += 1
        await asyncio.sleep(0.5)  # Simulate slow backend
        return "data"

    # Execute concurrent requests
    tasks = [
        cache.get_stale_fallback("test_key", slow_factory, ttl=60)
        for _ in range(5)
    ]
    
    print("Starting 5 concurrent requests...")
    results = await asyncio.gather(*tasks)
    
    # Verify
    print(f"Factory called {factory_call_count} times")
    assert factory_call_count == 1, f"Expected 1 factory call, got {factory_call_count}. Stampede protection failed."
    
    for res, is_stale in results:
        assert res == "data"
        assert is_stale is False

if __name__ == "__main__":
    asyncio.run(test_cache_stampede_protection())
