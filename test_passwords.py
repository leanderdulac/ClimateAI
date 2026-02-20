import asyncio
import asyncpg

passwords = [
    'brBU04YrEeJiXUne',
    'ClimateAI2025Secure!',
    'climateai123'
]

async def test():
    for pwd in passwords:
        url = f'postgresql://postgres.tyzmywhvpmdfepxdtyes:{pwd}@aws-1-sa-east-1.pooler.supabase.com:6543/postgres'
        print(f'Testing password {pwd[:5]}...')
        try:
            conn = await asyncpg.connect(url, timeout=3.0)
            print(f'SUCCESS with {pwd}!')
            await conn.close()
            return
        except Exception as e:
            print(f'Failed {pwd[:5]}: {e}')

asyncio.run(test())
