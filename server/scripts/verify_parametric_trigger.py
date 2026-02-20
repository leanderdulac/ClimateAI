
import asyncio
import sys
import os
import uuid
from datetime import datetime, date

# Determine the project root
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

from sqlalchemy import select, delete
from config import database as db_config
from models.sqlalchemy_models import Policy, Claim, ClimateData, Location, User
from services.parametric_service import ParametricTriggerService

async def verify_parametric_trigger():
    # Setup DB connection
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not set")
        return


    db_config._create_engine_and_session_maker(db_url)
    await db_config.init_db()
    
    async with db_config.async_session_maker() as session:
        print("✅ DB Connected")
        
        # 1. Setup Test Data
        test_id = str(uuid.uuid4())[:8]
        
        # Create Dummy Location
        location = Location(
            id=str(uuid.uuid4()),
            name="Test Location",
            city="Test City",
            state="TS",
            country="TestLand",
            latitude=-10.0,
            longitude=-50.0
        )
        session.add(location)
        
        # Create Dummy Policy
        policy = Policy(
            id=str(uuid.uuid4()),
            policy_number=f"TEST-POL-{test_id}",
            policy_type="parametric",
            status="active",
            location_id=location.id,
            coverage_amount=10000.00,
            premium=500.00,
            effective_date=date.today(),
            expiration_date=date.today(),
            # TRIGGER: Max Temp >= 30
            trigger_conditions={
                "metric": "temperature_max",
                "operator": ">=",
                "threshold": 30.0
            },
            payout_structure={"percentage": 0.5} # 50% payout
        )
        session.add(policy)
        
        # Create Triggering Weather Event
        climate_data = ClimateData(
            id=str(uuid.uuid4()),
            location_id=location.id,
            recorded_date=date.today(),
            temperature_max=35.0, # TRIGGERS (>30)
            precipitation=0.0
        )
        session.add(climate_data)
        
        await session.commit()
        print(f"📝 Test Data Created: Policy {policy.policy_number}, Temp {climate_data.temperature_max}C")
        
        # 2. Run Service
        service = ParametricTriggerService(session)
        print("🚀 Running Parametric Trigger Service...")
        triggered_claims = await service.scan_active_policies()
        
        # 3. Verify Results
        passed = False
        if triggered_claims:
            for claim in triggered_claims:
                if claim.policy_id == policy.id:
                    print(f"✅ Claim Created! Number: {claim.claim_number}, Amount: {claim.approved_amount}")
                    if claim.approved_amount == 5000.00: # 50% of 10000
                         print("✅ Payout Calculation Correct (5000.00)")
                         passed = True
                    else:
                         print(f"❌ Payout Calculation WRONG. Expected 5000.00, Got {claim.approved_amount}")
        else:
            print("❌ No claims created.")

        # 4. Cleanup
        print("🧹 Cleaning up test data...")
        await session.delete(policy)
        await session.delete(location)
        await session.delete(climate_data)
        for claim in triggered_claims:
             await session.delete(claim)
        await session.commit()

        if passed:
            print("🎉 VERIFICATION SUCCESSFUL")
        else:
            print("💥 VERIFICATION FAILED")

if __name__ == "__main__":
    asyncio.run(verify_parametric_trigger())
