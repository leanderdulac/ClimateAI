
"""
Parametric Trigger Service
Evaluates active policies against recent weather data to automatically trigger claims.
"""

import logging
from datetime import datetime
from typing import List, Optional
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_db_session
from models.sqlalchemy_models import Policy, Claim, ClimateData

logger = logging.getLogger(__name__)

class ParametricTriggerService:
    """
    Service to handle parametric insurance triggers.
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def scan_active_policies(self):
        """
        Fetches all active parametric policies and checks their triggers.
        """
        logger.info("Scanning active policies for parametric triggers...")
        
        # Fetch active policies of type 'parametric'
        stmt = select(Policy).where(
            Policy.status == 'active',
            Policy.policy_type == 'parametric'
        )
        result = await self.db.execute(stmt)
        policies = result.scalars().all()
        
        triggered_claims = []
        
        for policy in policies:
            try:
                # For each policy, check if a trigger event occurred recently
                # In a real system, we'd query broad weather data first to optimize.
                # Here we check per policy for simplicity and specificity.
                
                # Fetch recent climate data for policy location
                # valid for the last 24 hours (simulated by checking recent records)
                climate_data = await self._get_latest_climate_data(policy.location_id)
                
                if climate_data:
                    claim = await self.evaluate_policy_trigger(policy, climate_data)
                    if claim:
                        triggered_claims.append(claim)
            except Exception as e:
                logger.error(f"Error processing policy {policy.id}: {e}")
                
        logger.info(f"Scan complete. Triggered {len(triggered_claims)} new claims.")
        return triggered_claims

    async def _get_latest_climate_data(self, location_id: str) -> Optional[ClimateData]:
        """
        Retrieves the latest climate record for a location.
        """
        stmt = select(ClimateData).where(
            ClimateData.location_id == location_id
        ).order_by(ClimateData.recorded_date.desc()).limit(1)
        
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def evaluate_policy_trigger(self, policy: Policy, climate_data: ClimateData) -> Optional[Claim]:
        """
        Evaluates if the climate data meets the policy's trigger conditions.
        """
        conditions = policy.trigger_conditions
        if not conditions:
            return None
            
        is_triggered = False
        trigger_reason = []
        
        # Example Condition Structure:
        # {
        #   "temperature": { "min": 40, "max": 50 },
        #   "precipitation": { "max": 10 } (Drought) or { "min": 100 } (Flood)
        # }
        
        # Check Temperature
        if "temperature" in conditions:
            temp_config = conditions["temperature"]
            current_temp = float(climate_data.temperature_max or 0)
            
            if "min" in temp_config and current_temp >= temp_config["min"]:
                is_triggered = True
                trigger_reason.append(f"High Temperature: {current_temp}°C >= {temp_config['min']}°C")
                
            if "max" in temp_config and current_temp <= temp_config["max"]: # e.g. Frost
                 # This logic seems inverted for 'max', usually 'max' in trigger means 'if it exceeds max'.
                 # But if we want 'Frost', we want 'if temp drops below X'. 
                 # Let's assume schema: 'operator': '>=', 'threshold': 40
                 pass

        # Simplified Logic for MVP: Just check explicit 'min' threshold for now
        # { "metric": "temperature_max", "operator": ">=", "threshold": 40 }
        if "metric" in conditions:
            metric = conditions.get("metric")
            threshold = conditions.get("threshold")
            operator = conditions.get("operator", ">=")
            
            val = getattr(climate_data, metric, None)
            
            if val is not None:
                val = float(val)
                if operator == ">=" and val >= threshold:
                    is_triggered = True
                    trigger_reason.append(f"{metric} ({val}) >= {threshold}")
                elif operator == "<=" and val <= threshold:
                    is_triggered = True
                    trigger_reason.append(f"{metric} ({val}) <= {threshold}")

        # Check existing claims to avoid duplicate payout for same event/day
        # (Skipped for MVP simplicity)

        if is_triggered:
            logger.info(f"Policy {policy.id} TRIGGERED! Reason: {trigger_reason}")
            return await self.trigger_claim(policy, climate_data, reasons=trigger_reason)
        
        return None

    async def trigger_claim(self, policy: Policy, climate_data: ClimateData, reasons: List[str]) -> Claim:
        """
        Creates a new approved claim.
        """
        payout_amount = policy.coverage_amount # Default to full payout
        
        # Check payout structure if partial payout defined
        if policy.payout_structure and "fixed_amount" in policy.payout_structure:
            payout_amount = policy.payout_structure["fixed_amount"]
        elif policy.payout_structure and "percentage" in policy.payout_structure:
            payout_amount = float(policy.coverage_amount) * float(policy.payout_structure["percentage"])

        new_claim = Claim(
            id=str(uuid.uuid4()),
            policy_id=policy.id,
            claim_number=f"CLM-PARA-{uuid.uuid4().hex[:8].upper()}",
            claim_type="weather_damage",
            status="approved", # Parametric claims are often auto-approved
            event_date=climate_data.recorded_date,
            event_description=f"Parametric Trigger Activated: {'; '.join(reasons)}",
            claimed_amount=payout_amount,
            approved_amount=payout_amount,
            weather_data={
                "source": climate_data.source,
                "recorded_date": str(climate_data.recorded_date),
                "temperature_max": float(climate_data.temperature_max) if climate_data.temperature_max else None,
                "precipitation": float(climate_data.precipitation) if climate_data.precipitation else None
            }
        )
        
        self.db.add(new_claim)
        await self.db.commit()
        await self.db.refresh(new_claim)
        
        logger.info(f"Claim {new_claim.claim_number} created for Policy {policy.policy_number}")
        return new_claim
