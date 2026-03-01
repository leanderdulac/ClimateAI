import asyncio, asyncpg

async def main():
    urls = [
        os.getenv("TEST_AWS1_POOLER_URL", "postgresql://postgres:postgres@localhost:5432/postgres")
    ]
    for url in urls:
        print(f"Testing {url} ...")
        try:
            conn = await asyncpg.connect(url, timeout=5)
            print('Connected successfully!')
            await conn.close()
        except Exception as e:
            print(f'Error: {e}')

asyncio.run(main())
