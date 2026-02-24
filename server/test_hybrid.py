import asyncio
from api.parametric_trigger_verification import simulate_hybrid_index
from datetime import datetime
import json

async def main():
    try:
        # Test Santos/SP (where the fallback OpenMeteo happens or CEMADEN coordinates)
        print("Testing Santos/SP...")
        result = await simulate_hybrid_index(
            municipio="SANTOS",
            uf="SP",
            data_inicio="2025-01-01",
            data_fim="2025-01-10",
            insured_capital=100000.0
        )
        print(json.dumps(result, indent=2, default=str))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
