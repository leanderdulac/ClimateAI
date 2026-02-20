import asyncio
import asyncpg
import redis.asyncio as redis
import os
import sys
from dotenv import load_dotenv

load_dotenv()

async def test_db():
    print("Testing Database connection...")
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not set in environment")
        return False

    print(f"Connecting to: {db_url.split('@')[-1]}") # Log only host/db part for security
    
    # Fix DSN for asyncpg
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    
    print(f"Connecting to: {db_url.split('@')[-1]}") # Log only host/db part for security
    
    try:
        # Using localhost because containers are mapped to host ports
        # If env is IPv6 only or prefers it, asyncpg should handle it.
        # But if we want to be sure, we can Try to connect.
        conn = await asyncpg.connect(db_url, ssl='require')
        print("✅ Successfully connected to PostgreSQL!")
        await conn.close()
        return True
    except Exception as e:
        print(f"❌ Failed to connect to PostgreSQL: {e}")
        # Detailed diagnostic
        import socket
        from urllib.parse import urlparse
        try:
            parsed = urlparse(db_url)
            host = parsed.hostname
            infos = socket.getaddrinfo(host, parsed.port or 5432)
            print(f"DNS Info for {host}:")
            for info in infos:
                print(f"  - {info[4][0]} ({info[0].name})")
        except Exception as dns_e:
            print(f"DNS Resolution failed during diagnostic: {dns_e}")
            
        return False

async def test_redis():
    print("Testing Redis connection...")
    try:
        r = redis.from_url("redis://127.0.0.1:6379")
        ping = await r.ping()
        if ping:
            print("✅ Successfully connected to Redis!")
            await r.aclose()
            return True
        else:
            print("❌ Redis ping failed.")
            return False
    except Exception as e:
        print(f"❌ Failed to connect to Redis: {e}")
        return False

async def main():
    db_ok = await test_db()
    
    # Redis is optional for now if not running locally
    redis_ok = await test_redis()
    
    if db_ok:
        print("\nEssential connections verified successfully!")
        sys.exit(0)
    else:
        print("\nDatabase connection failed.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
