import pytest
import asyncio
from datetime import datetime
from api.integrated_pricing_framework import calculate_complete_pricing_framework
from services.physical_risk_service import PhysicalRiskService, PropertyCharacteristics, ClimateScenario
from services.transition_risk_service import TransitionRiskService, AssetCharacteristics, EnvironmentalScenario

@pytest.mark.async_context
class TestActuarialValidity:
    @pytest.mark.asyncio
    async def test_premium_sufficiency_baseline(self):
        """Test if premium covers expected losses in baseline scenario (São Paulo)"""
        # Rio de Janeiro coords for heatwave testing
        lat, lon = -22.9068, -43.1729
        
        result = await calculate_complete_pricing_framework(
            location_latitude=lat,
            location_longitude=lon,
            property_value=1000000,
            coverage_amount=800000,
            free_capital=5000000,
            climate_temperature_change=1.5
        )
        
        final_premium = result["final_premium"]
        expected_claims = result["profitability_analysis"]["expected_claims"]
        
        # Actuarial Rule: Premium must be > Expected Claims + Admin Costs
        # Admin costs are around 12% in our model
        min_sufficient_premium = expected_claims * 1.12
        
        assert final_premium > min_sufficient_premium, f"Premium {final_premium} insufficient for claims {expected_claims}"
        assert result["profitability_analysis"]["profitability_status"] in ["PROFITABLE", "HIGHLY_PROFITABLE"]

    @pytest.mark.asyncio
    async def test_climate_sensitivity_loading(self):
        """Verify if premium increases correctly with climate delta T"""
        lat, lon = -23.5505, -46.6333
        
        low_risk = await calculate_complete_pricing_framework(
            location_latitude=lat,
            location_longitude=lon,
            property_value=1000000,
            coverage_amount=800000,
            free_capital=10000000,
            climate_temperature_change=1.0
        )
        
        high_risk = await calculate_complete_pricing_framework(
            location_latitude=lat,
            location_longitude=lon,
            property_value=1000000,
            coverage_amount=800000,
            free_capital=10000000,
            climate_temperature_change=4.0
        )
        
        assert high_risk["final_premium"] > low_risk["final_premium"], "Premium failed to respond to increased climate risk"
        
    @pytest.mark.asyncio
    async def test_concentration_loading(self):
        """Verify supply-demand adjustment for high zone concentration"""
        lat, lon = -23.5505, -46.6333
        
        # High concentration: Total premiums in zone > 25% of free capital
        # 3,000,000 / 10,000,000 = 0.3 (> 0.25)
        high_conc = await calculate_complete_pricing_framework(
            location_latitude=lat,
            location_longitude=lon,
            property_value=1000000,
            coverage_amount=800000,
            free_capital=10000000,
            zone_policies_premiums=[1500000, 1500000] 
        )
        
        assert high_conc["supply_demand_adjustment"] == 1.30, "Capacity loading (1.30) not applied for high concentration"

if __name__ == "__main__":
    asyncio.run(pytest.main([__file__]))
