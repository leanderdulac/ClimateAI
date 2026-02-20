
import asyncio
import os
import uuid
from datetime import datetime
from dotenv import load_dotenv

# Load .env
load_dotenv()

from config.database import init_db
import config.database as db_config
from models.sqlalchemy_models import User
from services.auth_service import auth_service

async def seed_data():
    print("Initializing database...")
    await init_db()
    
    async with db_config.async_session_maker() as session:
        # Check if user already exists
        email = "leanderdulac@gmail.com"
        print(f"Checking for user: {email}")
        user = await auth_service.get_user_by_email(session, email)
        
        if not user:
            print(f"Creating user: {email}")
            # We use auth_service to ensure password hashing
            # Note: UserCreate expects a pydantic model, but we can call it or just use UserModel
            from models.schemas import UserCreate, UserRole
            
            user_data = UserCreate(
                email=email,
                full_name="User Test Unique",
                password="password123", # I'll use a simple password for testing
                role=UserRole.ADMIN,
                is_active=True
            )
            
            await auth_service.create_user(session, user_data)
            print("User created successfully!")
        else:
            print("User already exists.")
            
    print("Seed process completed.")

if __name__ == "__main__":
    asyncio.run(seed_data())
