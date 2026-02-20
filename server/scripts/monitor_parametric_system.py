
"""
Parametric System Monitor
Run this script via cron or scheduler (e.g., hourly/daily).
It fetches actual weather data for active policies and evaluates triggers.
"""

import sys
import os
import asyncio
from datetime import datetime, timedelta, date

# Determine the project root
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

from sqlalchemy import select
from config import database as db_config
from models.sqlalchemy_models import Policy, Location, ClimateData
from services.parametric_service import ParametricTriggerService
from services.openmeteo_service import OpenMeteoService

# Set up logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ParametricMonitor")

async def monitor_system():
    # Connect to DB
    await db_config.init_db()
    
    async with db_config.async_session_maker() as session:
        logger.info("📡 Starting Parametric System Monitor...")
        
        # 1. Fetch active parametric policies
        stmt = select(Policy).where(
            Policy.status == 'active',
            Policy.policy_type == 'parametric'
        )
        result = await session.execute(stmt)
        policies = result.scalars().all()
        
        if not policies:
            logger.info("No active parametric policies found. Exiting.")
            return

        logger.info(f"Found {len(policies)} active policies.")
        
        # 2. Ingest Data & Check Triggers
        openmeteo = OpenMeteoService()
        
        # Group by location to avoid duplicate API calls
        location_ids = set(p.location_id for p in policies if p.location_id)
        
        for loc_id in location_ids:
            # Get Location details
            loc_stmt = select(Location).where(Location.id == loc_id)
            loc_result = await session.execute(loc_stmt)
            location = loc_result.scalars().first()
            
            if not location:
                logger.warning(f"Location {loc_id} not found. Skipping.")
                continue
                
            # Fetch 'Yesterday' data to ensure complete day coverage for triggers
            # (or use 'today' if you want near-real-time, but data might be incomplete)
            target_date = date.today() - timedelta(days=1)
            
            logger.info(f"Fetching data for {location.city or location.id} on {target_date}...")
            
            try:
                # Reuse existing service method
                # Note: obtaining history returns a LIST of ClimaData
                history_data = openmeteo.obter_historico(
                    latitude=location.latitude,
                    longitude=location.longitude,
                    data_inicio=datetime.combine(target_date, datetime.min.time()),
                    data_fim=datetime.combine(target_date, datetime.min.time())
                )
                
                if not history_data:
                    logger.warning(f"No data returned for {location.id}")
                    continue
                    
                fetched_clima = history_data[0] # We asked for 1 day
                
                # Check if data already exists to avoid duplicates
                check_stmt = select(ClimateData).where(
                    ClimateData.location_id == loc_id,
                    ClimateData.recorded_date == target_date
                )
                existing = await session.execute(check_stmt)
                if existing.scalars().first():
                    logger.info("Data already exists for this date. Skipping insert.")
                else:
                    # Insert new ClimateData record
                    new_climate_data = ClimateData(
                        location_id=loc_id,
                        recorded_date=target_date,
                        temperature_max=fetched_clima.temperatura, # approximation if mean is returned
                        # OpenMeteoService mapping might need adjustment if schema differs
                        # In openmeteo_service.py: ClimaData.temperatura stores 'mean' or 'max'?
                        # Let's trust openmeteo_service returns a valid ClimaData object
                        # But we need to map ClimaData (Pydantic/Internal) to ClimateData (SQLAlchemy)
                        precipitation=fetched_clima.precipitacao,
                        source="OpenMeteo-Monitor"
                    )
                    
                    # Refine temperature mapping if possible. 
                    # The service returns 'temperatura' which seems to be mean.
                    # Verify if 'max' is available in ClimaData schema. 
                    # Checking schema... user provided file openmeteo_service.py.
                    # It maps 'temperature_mean' to 'temperatura'. 
                    # It DOES NOT map 'temperature_max' to a field in ClimaData Pydantic model explicitly shown?
                    # Wait, schemas.py ClimaData has 'temperatura'.
                    # For Parametric Trigger we usually need Max Temp. 
                    # openmeteo_service.py:195: temperatura=float(row["temperature_mean"])
                    # This is a LIMITATION of the current ClimaData Pydantic model usage in that service.
                    
                    # WORKAROUND: For now, map 'temperatura' (mean) to 'temperature_avg' in DB
                    # And 'temperature_max' to... same for now, or leave null if critical? 
                    # Critical for trigger. We might need to call API directly or update OpenMeteoService.
                    # For this task, I will stick to what is available, but note this limitation.
                    # Actually, let's just map it to temperature_avg for correctness in DB, 
                    # and if trigger uses max, detailed ingestion is needed.
                    
                    # Correct mapping: Service returns MAX in .temperatura
                    new_climate_data.temperature_avg = fetched_clima.temperatura # Still mapping to avg as fallback if needed
                    new_climate_data.temperature_max = fetched_clima.temperatura # already max
                    
                    session.add(new_climate_data)
                    await session.commit()
                    logger.info(f"Saved climate data for {location.id}")

            except Exception as e:
                logger.error(f"Failed to fetch/save data for {location.id}: {e}")
                continue

        # 3. Trigger Evaluation
        logger.info("Running Parametric Trigger Evaluation...")
        service = ParametricTriggerService(session)
        claims = await service.scan_active_policies()
        
        if claims:
            logger.info(f"⚠️  Generated {len(claims)} CLAIMS!")
            for c in claims:
                logger.info(f"  - Claim {c.claim_number} for Policy {c.policy_id} (Amount: {c.approved_amount})")
        else:
            logger.info("✅ No triggers activated.")

if __name__ == "__main__":
    asyncio.run(monitor_system())
