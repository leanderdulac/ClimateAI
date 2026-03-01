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

DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")

USERS = [os.getenv("DB_USER", "postgres")]
DATABASES = [os.getenv("DB_NAME", "postgres")]
PORTS = [int(os.getenv("DB_PORT", "5432"))]
HOSTS = [
    DB_HOST,
    os.getenv("DB_READONLY_HOST", DB_HOST),
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
