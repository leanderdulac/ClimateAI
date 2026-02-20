
import os
import sys
import psycopg2
from urllib.parse import urlparse
from dotenv import load_dotenv

# Add server directory to path to load config if needed, though we just need dotenv here
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

load_dotenv()

def get_db_connection():
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")
    db_user = os.getenv("DB_USER", "postgres")
    db_name = os.getenv("DB_NAME", "postgres")
    
    # Fallback to DATABASE_URL if individual vars aren't set but URL is
    if not db_host and os.getenv("DATABASE_URL"):
        try:
            parsed = urlparse(os.getenv("DATABASE_URL"))
            db_host = parsed.hostname
            db_user = parsed.username
            db_password = parsed.password
            db_name = parsed.path.lstrip('/')
            port = parsed.port or 5432
            print(f"Using connection from DATABASE_URL: {db_host}:{port}")
            return psycopg2.connect(
                host=db_host,
                user=db_user,
                password=db_password,
                dbname=db_name,
                port=port
            )
        except Exception as e:
            print(f"Error parsing DATABASE_URL: {e}")
            return None

    if not db_password or not db_host:
        print("Error: DB credentials not found in environment variables.")
        return None

    print(f"Connecting to {db_host}...")
    return psycopg2.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_name,
        port=5432  # Default port, adjust if needed
    )

def run_migration():
    conn = get_db_connection()
    if not conn:
        print("Failed to connect to database.")
        return False
    
    try:
        cur = conn.cursor()
        
        print("Checking if columns exist...")
        
        # Check for trigger_conditions
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='policies' AND column_name='trigger_conditions';")
        if cur.fetchone():
            print("Column 'trigger_conditions' already exists.")
        else:
            print("Adding column 'trigger_conditions'...")
            cur.execute("ALTER TABLE policies ADD COLUMN trigger_conditions JSONB DEFAULT '{}';")
            
        # Check for payout_structure
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='policies' AND column_name='payout_structure';")
        if cur.fetchone():
            print("Column 'payout_structure' already exists.")
        else:
            print("Adding column 'payout_structure'...")
            cur.execute("ALTER TABLE policies ADD COLUMN payout_structure JSONB DEFAULT '{}';")
            
        conn.commit()
        print("Migration completed successfully.")
        cur.close()
        conn.close()
        return True
    
    except Exception as e:
        print(f"Migration failed: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
