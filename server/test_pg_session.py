import asyncio, asyncpg

async def main():
    urls = [
        'postgresql://postgres.tyzmywhvpmdfepxdtyes:brBU04YrEeJiXUne@aws-0-sa-east-1.pooler.supabase.com:5432/postgres',
        'postgresql://postgres:brBU04YrEeJiXUne@aws-0-sa-east-1.pooler.supabase.com:5432/postgres'
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
