
import logging
import sys
import pandas as pd
from datetime import datetime, timedelta
from services.openmeteo_service import OpenMeteoService
from services.extreme_value_pricing_service import DefensivePricingOrchestrator, StressTester

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def run_stress_test():
    logger.info("Starting Massive Stress Test (50 Years)...")
    
    # Initialize services
    om_service = OpenMeteoService()
    orchestrator = DefensivePricingOrchestrator()
    
    # Define period: 2016 to 2026 (10 years) - Adjusted for stability & demo
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * 10)
    
    logger.info(f"Fetching data from {start_date.date()} to {end_date.date()}...")
    
    try:
        # Fetch data (will use chunking internally)
        # Using Sao Paulo coordinates
        clima_data_list = om_service.obter_historico(-23.55, -46.63, start_date, end_date)
        
        logger.info(f"Retrieved {len(clima_data_list)} records.")
        
        if not clima_data_list:
            logger.error("No data retrieved! Aborting.")
            return

        # Convert to DataFrame for Pricing Engine
        data_records = [{
            'date': d.data, 
            'temperature': d.temperatura
        } for d in clima_data_list]
        
        df = pd.DataFrame(data_records)
        df['date'] = pd.to_datetime(df['date'])
        
        logger.info("Data loaded. Running Pricing & Fractal Analysis...")
        
        # Run Pricing
        pricing_result = orchestrator.price_contract(df)
        print("\n" + "="*50)
        print("PRICING RESULTS (50 YEARS HISTORY)")
        print("="*50)
        print(pricing_result.model_dump_json(indent=2))
        
        # Run Stress Test (+4°C Shock)
        logger.info("Running Stress Test Scenario (+4°C Climate Shift)...")
        stress_result = StressTester.run_stress_test(df, orchestrator, temp_shift=4.0)
        
        print("\n" + "="*50)
        print("STRESS TEST RESULTS")
        print("="*50)
        print(stress_result.model_dump_json(indent=2))
        
        # Check Fractal Regime
        if pricing_result.fractal_metrics:
            print("\n" + "="*50)
            print(f"FRACTAL REGIME: {pricing_result.fractal_metrics.regime} (H={pricing_result.fractal_metrics.hurst_exponent})")
            print("="*50)

    except Exception as e:
        logger.error(f"Stress Test Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_stress_test())
