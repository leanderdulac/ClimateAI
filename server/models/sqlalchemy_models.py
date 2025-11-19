from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    role = Column(String, default="user")  # Assuming role is a string for simplicity

    # Add any other fields that might be expected by the Pydantic User model
    # For example, if 'organization' is expected in the Pydantic model, add it here
    organization = Column(String, nullable=True)

    def __repr__(self):
        return f"<User(id='{self.id}', email='{self.email}')>"
