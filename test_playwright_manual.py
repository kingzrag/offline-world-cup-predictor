
#!/usr/bin/env python3
import asyncio
from playwright.async_api import async_playwright
import json

async def main():
    print("Starting manual investigation...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  # Set to False if you want to see
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        # Log all responses
        async def log_response(response):
            print(f"Response: {response.status} {response.url}")

        page.on("response", log_response)

        try:
            print("Going to sofascore.com...")
            await page.goto("https://www.sofascore.com", wait_until="domcontentloaded", timeout=60000)
            print(f"Page title: {await page.title()}")
            print(f"Page URL: {page.url}")
            
            print("\nWaiting 15 seconds...")
            await asyncio.sleep(15)
            
            # Get page content
            content = await page.content()
            print(f"\nPage content length: {len(content)}")
            
            # Write to file
            with open("sofascore_page_content.html", "w") as f:
                f.write(content)
            print("\nPage content written to sofascore_page_content.html")
            
            # Check if there's a Cloudflare challenge
            if "cloudflare" in content.lower():
                print("\n⚠️ Cloudflare challenge detected in page content!")

        except Exception as e:
            print(f"Error: {e}")
            import traceback
            print(traceback.format_exc())

        print("\nClosing browser...")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())

