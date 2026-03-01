import asyncio
import os
import sys
import uuid

# Add the server directory to sys.path
sys.path.append(os.getcwd())

from config.database import get_db_session
from models.sqlalchemy_models import User
from services.auth_service import auth_service

async def create_test_user():
    print("Creating test user...")
    async for db in get_db_session():
        # Check if user already exists
        email = "test@example.com"
        result = await auth_service.get_user_by_email(db, email)
        if result:
            print(f"User {email} already exists.")
            return

        user = User(
            id=str(uuid.uuid4()),
            email=email,
            full_name="Admin User",
            hashed_password=auth_service.get_password_hash("password123"),
            role="admin",
            is_active=True,
            is_superuser=True
        )
        db.add(user)
        await db.commit()
        print(f"User {email} created successfully with password 'password123'.")
        break

if __name__ == "__main__":
    asyncio.run(create_test_user())
