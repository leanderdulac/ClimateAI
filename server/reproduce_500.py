import asyncio
import aiohttp

async def main():
    payload = {
        "asset_value": 100000,
        "severity_amount": 10000,
        "frequency_pct": 10,
        "coverage_period_years": 1,
        "scr_score": 450,
        "is_manual_underwriting": False,
        "latitude": -23.55,
        "longitude": -46.63
    }
    async with aiohttp.ClientSession() as session:
        tasks = [session.post("http://localhost:8000/api/v1/policy-pricing/calculate", json=payload) for _ in range(6)]
        resps = await asyncio.gather(*tasks)
        for r in resps:
            print(r.status, await r.text()[:100])

asyncio.run(main())
