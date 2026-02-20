#!/usr/bin/env python3
"""
Test direct database connection to Supabase.
Requires DB_PASSWORD and DB_HOST to be set in environment or .env file.
"""

import psycopg2
import os
import sys

from dotenv import load_dotenv
load_dotenv()

DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
if not DB_HOST and os.getenv("DATABASE_URL"):
    # Attempt to parse from DATABASE_URL
    try:
        from urllib.parse import urlparse
        parsed = urlparse(os.getenv("DATABASE_URL"))
        DB_HOST = parsed.hostname
    except:
        pass

DB_USER = os.getenv("DB_USER", "postgres")
DB_NAME = os.getenv("DB_NAME", "postgres")

if not DB_PASSWORD or not DB_HOST:
    print("❌ ERROR: DB_PASSWORD and DB_HOST (or DATABASE_URL) must be set in .env file")
    sys.exit(1)

if not DB_PASSWORD:
    print("❌ ERROR: DB_PASSWORD must be set in .env file")
    sys.exit(1)

def test_conn(port):
    print(f"Testing sync connection to {DB_HOST}:{port}...")
    try:
        conn = psycopg2.connect(
            host=DB_HOST, port=port, user=DB_USER,
            password=DB_PASSWORD, database=DB_NAME, connect_timeout=10
        )
        print("✅ SUCCESS!")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_conn(5432)
    test_conn(6543)
