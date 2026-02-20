import asyncio
import httpx

async def test_options():
    url = "http://localhost:8000/api/v1/policy-pricing/calculate"
    headers = {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type,authorization"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.options(url, headers=headers)
            print(f"Status Code: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            print(f"Body: {response.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_options())
