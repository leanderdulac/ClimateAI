
import asyncio
import os
import sys
from sqlalchemy import text
from dotenv import load_dotenv

# Add server directory to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

from config.database import get_db_session, _create_engine_and_session_maker

async def verify_connection():
    try:
        # Force initialization if not already done (though get_db_session does it)
        db_url = os.getenv("DATABASE_URL")
        print(f"Connecting to: {db_url}")
        
        # We need to manually initialize if not using get_db_session as a dependency generator
        # But get_db_session is a generator, so we iterate it
        async for session in get_db_session():
            print("Session created.")
            try:
                result = await session.execute(text("SELECT 1"))
                row = result.scalar()
                print(f"Query result: {row}")
                if row == 1:
                    print("SUCCESS: Database connection verified!")
                else:
                    print("WARNING: Database connected but returned unexpected result.")
            except Exception as e:
                print(f"ERROR: Query failed: {e}")
            finally:
                # Break after one session usage
                break
                
    except Exception as e:
        print(f"CRITICAL ERROR: Could not connect to database: {e}")

if __name__ == "__main__":
    asyncio.run(verify_connection())
