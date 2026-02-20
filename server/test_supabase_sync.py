#!/usr/bin/env python3
"""
Test sync connection to Supabase database.
Requires DB_PASSWORD to be set in environment or .env file.
"""

import psycopg2
import os
import sys

from dotenv import load_dotenv
load_dotenv()

DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "db.tyzmywhvpmdfepxdtyes.supabase.co")
DB_PORT = int(os.getenv("DB_PORT", "6543"))
DB_USER = os.getenv("DB_USER", "postgres")
DB_NAME = os.getenv("DB_NAME", "postgres")

if not DB_PASSWORD:
    print("❌ ERROR: DB_PASSWORD must be set in .env file")
    sys.exit(1)

def test_conn():
    print(f"Testing sync connection to {DB_HOST}:{DB_PORT}...")
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            connect_timeout=10
        )
        print("✅ SUCCESS!")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_conn()
