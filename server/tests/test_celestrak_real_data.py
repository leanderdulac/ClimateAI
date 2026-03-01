import sys
import os
import asyncio
from datetime import datetime

# Adicionar o diretório server ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.celestrak_service import celestrak_service

async def test_real_integration():
    print("=== Testing CelesTrak Real Integration ===")
    
    # 1. Test Orbit TLE Data (Already real, just verifying)
    print("\n[1/4] Testing TLE Data (Space Stations)...")
    tles = celestrak_service.get_tle_data(category='stations')
    print(f"Fetched {len(tles)} TLE records.")
    if tles:
        print(f"Sample Satellite: {tles[0].satellite_name} (NORAD: {tles[0].norad_id})")
    
    # 2. Test Real SATCAT Search
    print("\n[2/4] Testing Real SATCAT Search (ISS: 25544)...")
    iss_info = celestrak_service.get_satellite_info('25544')
    if iss_info:
        print(f"Found: {iss_info.satellite_name}")
        print(f"Country: {iss_info.country}, Launch: {iss_info.launch_date}")
        print(f"Operator: {iss_info.operator}")
    else:
        print("FAILED: ISS not found in SATCAT")

    # 3. Test Real Space Weather
    print("\n[3/4] Testing Real Space Weather...")
    weather = celestrak_service.get_space_weather()
    if weather:
        print(f"Timestamp: {weather.timestamp}")
        print(f"Kp Index: {weather.kp_index}, Storm: {weather.geomagnetic_storm}")
        print(f"Solar Flux: {weather.solar_flux}")
    else:
        print("FAILED: Space weather data not fetched")

    # 4. Test Real Conjunction Alerts (SOCRATES Top 10)
    print("\n[4/4] Testing Real SOCRATES Top 10 Conjunctions...")
    alerts = celestrak_service.get_conjunction_alerts()
    print(f"Fetched {len(alerts)} conjunction alerts.")
    if alerts:
        for i, alert in enumerate(alerts[:3]):
            print(f"Alert {i+1}: {alert.object1_name} vs {alert.object2_name}")
            print(f"  Miss Distance: {alert.miss_distance_km} km, Prob: {alert.collision_probability}")
            print(f"  Risk Level: {alert.risk_level.value}")
    else:
        print("No alerts found (or fetch failed)")

if __name__ == "__main__":
    asyncio.run(test_real_integration())
