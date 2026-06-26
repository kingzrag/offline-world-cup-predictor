
#!/usr/bin/env python3
import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import json

async def main():
    print("Launching browser...")
    async with async_playwright() as p:
        stealth = Stealth()
        stealth.hook_playwright_context(p)
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        captured_request = None
        
        async def handle_request(request):
            nonlocal captured_request
            if "api.sofascore.com" in request.url and not captured_request:
                captured_request = request
                print(f"Captured API request: {request.url}")
                print(f"Headers: {request.headers}")
        
        page.on("request", handle_request)
        
        print("Navigating to https://www.sofascore.com/football/live...")
        await page.goto("https://www.sofascore.com/football/live", wait_until="domcontentloaded", timeout=60000)
        
        print("Waiting 15 seconds for API requests...")
        await asyncio.sleep(15)
        
        if captured_request:
            # Save headers and cookies
            cookies = await context.cookies()
            with open("captured_headers.json", "w") as f:
                json.dump({
                    "headers": dict(captured_request.headers),
                    "cookies": cookies
                }, f, indent=2)
            print("Saved captured headers and cookies to captured_headers.json")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
