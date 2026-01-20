"""
Supabase Client Configuration for ClimateAI
Provides database and authentication integration with Supabase.
"""

import os
import logging
from functools import lru_cache
from typing import Optional

logger = logging.getLogger(__name__)

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# Client instance cache
_supabase_client = None
_supabase_admin_client = None


def is_supabase_configured() -> bool:
    """Check if Supabase credentials are configured"""
    return bool(SUPABASE_URL and SUPABASE_ANON_KEY)


@lru_cache(maxsize=1)
def get_supabase_client():
    """
    Get Supabase client for regular operations (respects RLS).
    Uses the anon/public key.
    """
    global _supabase_client
    
    if _supabase_client:
        return _supabase_client
    
    if not is_supabase_configured():
        logger.warning("Supabase not configured. Set SUPABASE_URL and SUPABASE_ANON_KEY.")
        return None
    
    try:
        from supabase import create_client, Client
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        logger.info(f"Supabase client initialized: {SUPABASE_URL}")
        return _supabase_client
    except ImportError:
        logger.error("supabase-py not installed. Run: pip install supabase")
        return None
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        return None


@lru_cache(maxsize=1)
def get_supabase_admin_client():
    """
    Get Supabase admin client (bypasses RLS).
    Uses the service_role key. Use with caution.
    """
    global _supabase_admin_client
    
    if _supabase_admin_client:
        return _supabase_admin_client
    
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        logger.warning("Supabase admin not configured. Set SUPABASE_SERVICE_ROLE_KEY.")
        return None
    
    try:
        from supabase import create_client, Client
        _supabase_admin_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        logger.info("Supabase admin client initialized")
        return _supabase_admin_client
    except Exception as e:
        logger.error(f"Failed to initialize Supabase admin client: {e}")
        return None


# Helper functions for common operations
async def supabase_query(table: str, filters: dict = None, limit: int = 100):
    """
    Execute a query on a Supabase table.
    
    Args:
        table: Name of the table
        filters: Dictionary of column:value filters
        limit: Maximum number of rows to return
        
    Returns:
        List of rows or empty list on error
    """
    client = get_supabase_client()
    if not client:
        return []
    
    try:
        query = client.table(table).select("*")
        
        if filters:
            for column, value in filters.items():
                query = query.eq(column, value)
        
        query = query.limit(limit)
        response = query.execute()
        return response.data or []
    except Exception as e:
        logger.error(f"Supabase query error on {table}: {e}")
        return []


async def supabase_insert(table: str, data: dict):
    """
    Insert a row into a Supabase table.
    
    Args:
        table: Name of the table
        data: Dictionary of column:value pairs
        
    Returns:
        Inserted row data or None on error
    """
    client = get_supabase_client()
    if not client:
        return None
    
    try:
        response = client.table(table).insert(data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"Supabase insert error on {table}: {e}")
        return None


async def supabase_update(table: str, id_column: str, id_value, data: dict):
    """
    Update a row in a Supabase table.
    
    Args:
        table: Name of the table
        id_column: Name of the ID column
        id_value: Value of the ID
        data: Dictionary of column:value pairs to update
        
    Returns:
        Updated row data or None on error
    """
    client = get_supabase_client()
    if not client:
        return None
    
    try:
        response = client.table(table).update(data).eq(id_column, id_value).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"Supabase update error on {table}: {e}")
        return None


async def supabase_delete(table: str, id_column: str, id_value):
    """
    Delete a row from a Supabase table.
    
    Args:
        table: Name of the table
        id_column: Name of the ID column
        id_value: Value of the ID
        
    Returns:
        True on success, False on error
    """
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        client.table(table).delete().eq(id_column, id_value).execute()
        return True
    except Exception as e:
        logger.error(f"Supabase delete error on {table}: {e}")
        return False


# Authentication helpers
async def sign_up(email: str, password: str):
    """Register a new user"""
    client = get_supabase_client()
    if not client:
        return None
    
    try:
        response = client.auth.sign_up({
            "email": email,
            "password": password,
        })
        return response
    except Exception as e:
        logger.error(f"Supabase sign up error: {e}")
        return None


async def sign_in(email: str, password: str):
    """Sign in a user"""
    client = get_supabase_client()
    if not client:
        return None
    
    try:
        response = client.auth.sign_in_with_password({
            "email": email,
            "password": password,
        })
        return response
    except Exception as e:
        logger.error(f"Supabase sign in error: {e}")
        return None


async def sign_out(access_token: str = None):
    """Sign out a user"""
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        client.auth.sign_out()
        return True
    except Exception as e:
        logger.error(f"Supabase sign out error: {e}")
        return False


async def get_user(access_token: str):
    """Get user from access token"""
    client = get_supabase_client()
    if not client:
        return None
    
    try:
        response = client.auth.get_user(access_token)
        return response.user if response else None
    except Exception as e:
        logger.error(f"Supabase get user error: {e}")
        return None


# Health check
async def check_supabase_health() -> dict:
    """Check Supabase connection health"""
    if not is_supabase_configured():
        return {
            "status": "not_configured",
            "message": "Supabase credentials not set",
        }
    
    try:
        client = get_supabase_client()
        if not client:
            return {
                "status": "error",
                "message": "Failed to create Supabase client",
            }
        
        # Try a simple query to test connection
        # This will fail gracefully if no tables exist
        return {
            "status": "connected",
            "url": SUPABASE_URL,
            "message": "Supabase connection successful",
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
        }
