import asyncio, asyncpg
async def main():
    try:
        conn = await asyncpg.connect('postgresql://postgres:brBU04YrEeJiXUne@aws-0-sa-east-1.pooler.supabase.com:6543/postgres?options=project%3Dtyzmywhvpmdfepxdtyes')
        print('Connected via options!')
        await conn.close()
    except Exception as e:
        print(f'Error via options: {e}')
    
    try:
        conn = await asyncpg.connect('postgresql://postgres.tyzmywhvpmdfepxdtyes:brBU04YrEeJiXUne@aws-0-sa-east-1.pooler.supabase.com:6543/postgres')
        print('Connected via username!')
        await conn.close()
    except Exception as e:
        print(f'Error via username: {e}')
asyncio.run(main())
