#!/usr/bin/env python3
"""
Quick Supabase health check
"""
import asyncio
import sys
import os

# Add server to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.supabase_client import check_supabase_health

async def main():
    result = await check_supabase_health()
    print('🔍 Supabase Health Check:')
    print(f'📊 Status: {result["status"]}')
    print(f'💬 Message: {result["message"]}')
    if 'url' in result:
        print(f'🌐 URL: {result["url"]}')

if __name__ == "__main__":
    asyncio.run(main())