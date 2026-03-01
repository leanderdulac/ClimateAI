import sys
import asyncio
sys.path.append('.')
from services.atlas_database_service import atlas_db_service
from config.database import get_db_session

async def main():
    async with atlas_db_service.get_session() as session:
        from sqlalchemy import select, func
        from models.sqlalchemy_models import AtlasDisaster
        query = select(func.count()).select_from(AtlasDisaster)
        res = await session.execute(query)
        count = res.scalar()
        print(f"Total AtlasDisaster records: {count}")

if __name__ == '__main__':
    asyncio.run(main())
