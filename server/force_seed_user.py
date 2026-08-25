import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from models.sqlalchemy_models import User
import os
import uuid
from datetime import datetime

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def force_seed():
    print("Force seeding local_dev.db...")
    engine = create_async_engine("sqlite+aiosqlite:///local_dev.db")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        from models.sqlalchemy_models import Base
        await conn.run_sync(Base.metadata.create_all)
        
    async with async_session() as session:
        # Check if user exists
        from sqlalchemy import select
        email = os.getenv("BOOTSTRAP_ADMIN_EMAIL")
        password = os.getenv("BOOTSTRAP_ADMIN_PASSWORD")
        if not email or not password:
            print("Skipping seed: BOOTSTRAP_ADMIN_EMAIL / BOOTSTRAP_ADMIN_PASSWORD not set")
            return
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalars().first()
        
        if not user:
            print(f"Creating test user {email}")
            hashed_password = pwd_context.hash(password)
            new_user = User(
                id=str(uuid.uuid4()),
                email=email,
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
            print("User already exists. Updating password from env.")
            user.hashed_password = pwd_context.hash(password)
            await session.commit()
            print("Password updated!")
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(force_seed())
