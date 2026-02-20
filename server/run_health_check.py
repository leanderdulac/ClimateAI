
import asyncio
import os
import sys

# Add current dir to path
sys.path.insert(0, os.getcwd())

from dotenv import load_dotenv
load_dotenv()

if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_ANON_KEY"):
    print("❌ ERROR: SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env file")
    sys.exit(1)

from config.supabase_client import check_supabase_health

async def main():
    print("Running Supabase health check...")
    result = await check_supabase_health()
    print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
