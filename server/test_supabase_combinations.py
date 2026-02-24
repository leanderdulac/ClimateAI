#!/usr/bin/env python3
"""
Test combinations of users and databases for Supabase connections.
Requires DB_PASSWORD and DB_HOST to be set in environment or .env file.
"""

import asyncpg
import asyncio
import os
import sys

from dotenv import load_dotenv
load_dotenv()

DB_PASSWORD = os.getenv("DB_PASSWORD", "brBU04YrEeJiXUne")
DB_HOST = os.getenv("DB_HOST", "db.tyzmywhvpmdfepxdtyes.supabase.co")

USERS = ["postgres", "postgres.tyzmywhvpmdfepxdtyes"]
DATABASES = ["postgres"]
PORTS = [5432, 6543]
HOSTS = [
    DB_HOST,
    "aws-0-sa-east-1.pooler.supabase.com",
    "54.94.90.106" 
]

async def test_all():
    for host in HOSTS:
        print(f"\n--- Testing Host: {host} ---")
        for user in USERS:
            for db in DATABASES:
                for port in PORTS:
                    print(f"Testing {user}@{host}:{port}/{db}...")
                    try:
                        conn = await asyncpg.connect(
                            host=host, port=port, user=user,
                            password=DB_PASSWORD, database=db, timeout=3,
                            ssl='require'
                        )
                        print(f"  ✅ SUCCESS!")
                        await conn.close()
                    except Exception as e:
                        print(f"  ❌ Failed: {str(e).splitlines()[0]}")

asyncio.run(test_all())
