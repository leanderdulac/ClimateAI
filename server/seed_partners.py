
import asyncio
import uuid
import hashlib
import secrets
from datetime import datetime
from sqlalchemy import select
from config.database import get_db_session, init_db, close_db
from models.sqlalchemy_models import Partner, APIKey

async def seed_partners():
    print("Initializing DB...")
    await init_db()
    
    async for session in get_db_session():
        print("Checking for existing partners...")
        stmt = select(Partner).where(Partner.slug == "climatewise-demo")
        result = await session.execute(stmt)
        existing = result.scalars().first()
        
        if existing:
            print(f"Partner 'ClimateWise Demo' already exists (ID: {existing.id})")
            partner_id = existing.id
        else:
            print("Creating 'ClimateWise Demo' partner...")
            new_partner = Partner(
                id=str(uuid.uuid4()),
                name="ClimateWise Demo",
                slug="climatewise-demo",
                contact_email="demo@climatewise.io",
                api_enabled=True
            )
            session.add(new_partner)
            await session.commit()
            partner_id = new_partner.id
            print(f"Partner created! ID: {partner_id}")
            
        # Create API Key
        print("Checking/Creating API Key...")
        stmt_key = select(APIKey).where(APIKey.partner_id == partner_id)
        result_key = await session.execute(stmt_key)
        existing_keys = result_key.scalars().all()
        
        if existing_keys:
            print(f"Found {len(existing_keys)} API keys for this partner.")
        else:
            # Generate a key
            raw_key = f"sk_live_{secrets.token_urlsafe(24)}"
            key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
            
            new_key = APIKey(
                id=str(uuid.uuid4()),
                partner_id=partner_id,
                key_hash=key_hash,
                prefix=raw_key[:10],
                name="Default Key",
                created_at=datetime.utcnow()
            )
            session.add(new_key)
            await session.commit()
            print(f"Created new API Key: {raw_key}")
            print("SAVE THIS KEY! It will not be shown again.")
            
    await close_db()

if __name__ == "__main__":
    asyncio.run(seed_partners())
