
import asyncio
import pandas as pd
from datetime import datetime, timedelta
from services.openmeteo_service import OpenMeteoService
from core.parametric_actuary import RainfallIndexContract

async def test_calculation():
    print("--- 1. Testing OpenMeteo Data Fetching ---")
    service = OpenMeteoService()
    
    # Sao Paulo
    lat, lon = -23.5505, -46.6333
    
    # Last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    print(f"Fetching data for SP ({lat}, {lon}) from {start_date.date()} to {end_date.date()}")
    
    try:
        data = await service.obter_historico(lat, lon, start_date, end_date)
        print(f"Received {len(data)} records.")
        if data:
            print(f"Sample Record [0]: Date={data[0].data}, Temp(Max)={data[0].temperatura}, Rain={data[0].precipitacao}")
            print(f"Sample Record [-1]: Date={data[-1].data}, Temp(Max)={data[-1].temperatura}, Rain={data[-1].precipitacao}")
            
            # Verify if Rain makes sense (e.g. not all zeros, unless it's dry season)
            total_rain = sum(d.precipitacao for d in data)
            print(f"Total Rain in period: {total_rain} mm")
    except Exception as e:
        print(f"Error fetching data: {e}")
        return

    print("\n--- 2. Testing Parametric Actuary Logic ---")
    
    # Create a dummy contract
    contract = RainfallIndexContract(
        area_id="test_sp",
        start_date=start_date.strftime("%m-%d"),
        end_date=end_date.strftime("%m-%d"),
        trigger_mm=100.0,
        exhaustion_mm=200.0,
        max_payout=10000.0,
        index_type="cum_period"
    )
    
    # Prepare DataFrame
    df = pd.DataFrame([
        {"date": d.data, "rain_mm": d.precipitacao}
        for d in data
    ])
    
    # Run Index
    idx_val = contract.compute_index_for_period(df, end_date.year)
    print(f"Calculated Index (cum_period): {idx_val}")
    
    # Run Payout
    payout = contract.index_to_payout_amount(idx_val)
    print(f"Payout: {payout}")
    
    print("\n--- 3. Testing Max 3-Day Logic ---")
    contract.index_type = "max_3day"
    contract.trigger_mm = 20.0 # Lower trigger to see if it triggers
    contract.exhaustion_mm = 50.0
    
    idx_val_3day = contract.compute_index_for_period(df, end_date.year)
    print(f"Calculated Index (max_3day): {idx_val_3day}")
    payout_3day = contract.index_to_payout_amount(idx_val_3day)
    print(f"Payout (max_3day): {payout_3day}")

if __name__ == "__main__":
    asyncio.run(test_calculation())
