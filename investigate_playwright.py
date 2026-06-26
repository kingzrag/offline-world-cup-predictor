
#!/usr/bin/env python3
import asyncio
from playwright.async_api import async_playwright
import json

async def investigate_with_playwright():
    print("=" * 80)
    print("SOFASCORE INVESTIGATION WITH PLAYWRIGHT")
    print("=" * 80)
    print()

    async with async_playwright() as p:
        print("Launching browser (headless=False for debugging)")
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        # Collect all API requests made by the page
        api_responses = []
        
        async def handle_response(response):
            if "api.sofascore.com" in response.url:
                print(f"\n  [API RESPONSE] {response.status} {response.url}")
                try:
                    data = await response.json()
                    api_responses.append((response.url, data))
                    print(f"    Success! JSON data received: {list(data.keys())}")
                    if "events" in data:
                        print(f"    Found {len(data['events'])} events")
                except Exception as e:
                    text = await response.text()
                    print(f"    Response text: {text[:500]}...")
        
        page.on("response", handle_response)
        
        try:
            print("Navigating to SofaScore main page")
            await page.goto("https://www.sofascore.com", wait_until="domcontentloaded", timeout=60000)
            
            print("\nClicking on Football...")
            # Find and click football link
            await page.wait_for_timeout(3000)
            
            print("\nWaiting 15 seconds for page to load and make API requests...")
            await asyncio.sleep(15)
            
            print(f"\nPage title: {await page.title()}")
            print(f"\nCaptured API responses: {len(api_responses)}")
            for url, data in api_responses:
                print(f"  - {url}")

        except Exception as e:
            print(f"Error: {type(e).__name__}: {e}")
            import traceback
            print(traceback.format_exc())
        finally:
            print("\nKeeping browser open for 30 seconds for manual inspection...")
            await asyncio.sleep(30)
            await browser.close()

if __name__ == "__main__":
    asyncio.run(investigate_with_playwright())
