import asyncio
from services.sgb_service import GeologicalRiskAdjuster

def check():
    adjuster = GeologicalRiskAdjuster()
    # São Paulo default lat, lon
    lat = -23.55
    lon = -46.63
    print("Testing GeologicalRiskAdjuster on SP coordinates...")
    result = adjuster.adjust_premium(1000.0, lat, lon)
    print("Result:", result)

if __name__ == "__main__":
    check()
