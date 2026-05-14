import os
import asyncio, asyncpg

async def main():
    default_url = "postgresql://postgres:postgres@localhost:5432/postgres"
    urls = [
        os.getenv("TEST_DATABASE_URL", default_url),
        os.getenv("TEST_POOLER_URL", default_url),
    ]
    for url in urls:
        print(f"Testing {url} ...")
        try:
            conn = await asyncpg.connect(url, timeout=5)
            print('Connected!')
            await conn.close()
        except Exception as e:
            print(f'Error: {e}')

asyncio.run(main())
