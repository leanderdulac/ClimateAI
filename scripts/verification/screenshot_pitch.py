import asyncio
from playwright.async_api import async_playwright
import os

async def take_screenshots():
    os.makedirs("pitch_screenshots", exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        
        print("Capturing Dashboard...")
        await page.goto("http://localhost:5173/")
        await page.wait_for_timeout(3000)
        await page.screenshot(path="pitch_screenshots/1_dashboard.png", full_page=True)
        
        print("Capturing Pricing Simulator...")
        await page.goto("http://localhost:5173/simulator")
        await page.wait_for_timeout(3000)
        await page.screenshot(path="pitch_screenshots/2_pricing_simulator.png", full_page=True)
        
        print("Capturing Tokenization...")
        await page.goto("http://localhost:5173/tokenization")
        await page.wait_for_timeout(3000)
        await page.screenshot(path="pitch_screenshots/3_tokenization.png", full_page=True)
        
        print("Capturing Analytics/Dashboard...")
        await page.goto("http://localhost:5173/analytics")
        await page.wait_for_timeout(3000)
        await page.screenshot(path="pitch_screenshots/4_analytics.png", full_page=True)
        
        await browser.close()
        print("Screenshots captured successfully in pitch_screenshots/ folder.")

asyncio.run(take_screenshots())
