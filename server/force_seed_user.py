import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from models.sqlalchemy_models import User
import uuid
from datetime import datetime

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def force_seed():
    print("Force seeding local_dev.db...")
    engine = create_async_engine("sqlite+aiosqlite:///local_dev.db")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Check if user exists
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.email == "leanderdulac@gmail.com"))
        user = result.scalars().first()
        
        if not user:
            print("Creating test user leanderdulac@gmail.com")
            hashed_password = pwd_context.hash("password123")
            new_user = User(
                id=str(uuid.uuid4()),
                email="leanderdulac@gmail.com",
                full_name="User Test Local",
                hashed_password=hashed_password,
                is_active=True,
                role="admin",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(new_user)
            await session.commit()
            print("User created successfully!")
        else:
            print("User already exists. Updating password to password123.")
            user.hashed_password = pwd_context.hash("password123")
            await session.commit()
            print("Password updated!")
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(force_seed())
