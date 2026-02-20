#!/usr/bin/env python3
"""
Test script for Supabase signup
Requires SUPABASE_URL and SUPABASE_ANON_KEY to be set in environment or .env file.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_ANON_KEY"):
    print("❌ ERROR: SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env file")
    sys.exit(1)

from supabase import create_client

async def test_signup():
    client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY"))
    result = client.auth.sign_up({"email": "test@example.com", "password": "test123456"})
    print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(test_signup())
