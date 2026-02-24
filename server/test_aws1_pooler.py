import asyncio, asyncpg

async def main():
    urls = [
        'postgresql://postgres.tyzmywhvpmdfepxdtyes:brBU04YrEeJiXUne@aws-1-sa-east-1.pooler.supabase.com:6543/postgres'
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
