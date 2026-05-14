import os
import asyncio, asyncpg
async def main():
    try:
        conn = await asyncpg.connect(
            os.getenv(
                "TEST_POOLER_OPTIONS_URL",
                "postgresql://postgres:postgres@localhost:5432/postgres?options=project%3Dlocal",
            )
        )
        print('Connected via options!')
        await conn.close()
    except Exception as e:
        print(f'Error via options: {e}')
    
    try:
        conn = await asyncpg.connect(
            os.getenv(
                "TEST_POOLER_USERNAME_URL",
                "postgresql://postgres:postgres@localhost:5432/postgres",
            )
        )
        print('Connected via username!')
        await conn.close()
    except Exception as e:
        print(f'Error via username: {e}')
asyncio.run(main())
