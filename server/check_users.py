
import asyncio
import os
from sqlalchemy import text
from config.database import _create_engine_and_session_maker, async_session_maker

async def check_users():
    database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
    print(f"Checking database at {database_url}")
    import config.database as db_config
    db_config._create_engine_and_session_maker(database_url)
    
    async with db_config.async_session_maker() as session:
        result = await session.execute(text("SELECT email FROM users"))
        users = result.fetchall()
        print(f"Total users: {len(users)}")
        for user in users:
            print(f"User: {user[0]}")

if __name__ == "__main__":
    asyncio.run(check_users())
