
#!/usr/bin/env python3
import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

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
        
        print("Navigating to https://www.sofascore.com...")
        await page.goto("https://www.sofascore.com", wait_until="domcontentloaded", timeout=60000)
        
        print("Waiting 10 seconds...")
        await asyncio.sleep(10)
        
        html = await page.content()
        with open("sofascore_page.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("Saved page HTML to sofascore_page.html")
        
        if "cloudflare" in html.lower():
            print("\n⚠️ CLOUDFLARE DETECTED IN PAGE HTML!")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
