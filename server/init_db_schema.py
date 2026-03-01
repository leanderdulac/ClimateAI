import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from models.sqlalchemy_models import Base

async def init_schema():
    print("Initialising SQLite Schema...")
    database_url = "sqlite+aiosqlite:///local_dev.db"
    engine = create_async_engine(database_url, echo=True)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        
    print("Schema initialized successfully.")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init_schema())
