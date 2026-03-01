import sys
import asyncio
sys.path.append('.')
from config.database import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from models.sqlalchemy_models import OracleEvent, BlockchainTransaction

async def main():
    async for db in get_db_session():
        from sqlalchemy import delete
        try:
            await db.execute(delete(BlockchainTransaction))
            await db.execute(delete(OracleEvent))
            await db.commit()
            print("Cleared simulated OracleEvents and Txns from DB")
        except Exception as e:
            await db.rollback()
            print(f"Error: {e}")

if __name__ == '__main__':
    asyncio.run(main())
