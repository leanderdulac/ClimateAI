#!/usr/bin/env python3
"""
Test combinations of users and databases for Supabase connections.
Requires DB_PASSWORD and DB_HOST to be set in environment or .env file.
"""

import psycopg2
import os
import sys
import socket

from dotenv import load_dotenv
load_dotenv()

DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "db.tyzmywhvpmdfepxdtyes.supabase.co")

if not DB_PASSWORD:
    print("❌ ERROR: DB_PASSWORD must be set in .env file")
    # Try to load from known location if missing
    try:
        with open('.env', 'r') as f:
            for line in f:
                if line.startswith('DB_PASSWORD='):
                    DB_PASSWORD = line.strip().split('=')[1]
                    print(f"Loaded DB_PASSWORD from .env: {DB_PASSWORD[:2]}***")
    except:
        pass

if not DB_PASSWORD:
    print("❌ Critical: Could not find DB_PASSWORD")
    sys.exit(1)

USERS = ["postgres", "authenticated", "anon"] # Added typical Supabase roles
DATABASES = ["postgres"]
PORTS = [5432, 6543]
HOSTS = [
    DB_HOST,
    "aws-0-sa-east-1.pooler.supabase.com",
    "54.94.90.106" # One of the IPs for the pooler
]

for host in HOSTS:
    print(f"\n--- Testing Host: {host} ---")
    for user in USERS:
        for db in DATABASES:
            for port in PORTS:
                print(f"Testing {user}@{host}:{port}/{db}...")
                try:
                    conn = psycopg2.connect(
                        host=host, port=port, user=user,
                        password=DB_PASSWORD, database=db, connect_timeout=5,
                        sslmode='require'
                    )
                    print(f"  ✅ SUCCESS!")
                    conn.close()
                except Exception as e:
                    print(f"  ❌ Failed: {str(e).splitlines()[0]}")
