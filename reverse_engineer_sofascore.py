
#!/usr/bin/env python3
import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime

async def main():
    print("=" * 100)
    print("SOFASCORE LIVE DATA REVERSE ENGINEERING")
    print("=" * 100)
    print(f"Started at: {datetime.now().isoformat()}")
    
    async with async_playwright() as p:
        print("\nLaunching Chromium...")
        
        browser = await p.chromium.launch(
            headless=False
        )
        
        page = await browser.new_page(
            viewport={"width": 1920, "height": 1080}
        )
        
        all_requests = []
        
        async def capture_request(request):
            request_info = {
                "timestamp": datetime.now().isoformat(),
                "url": request.url,
                "method": request.method,
                "headers": dict(request.headers),
                "post_data": None
            }
            try:
                request_info["post_data"] = request.post_data
            except Exception:
                pass
            all_requests.append(request_info)
            
            # Print all API requests immediately
            if "api.sofascore.com" in request.url:
                print(f"\n📡 OUTGOING API REQUEST: {request.method} {request.url}")
        
        async def capture_response(response):
            matching_request = next((r for r in all_requests if r["url"] == response.url), None)
            if matching_request:
                matching_request.update({
                    "response_status": response.status,
                    "response_headers": dict(response.headers),
                    "content_type": response.headers.get("content-type", "unknown")
                })
                
                # Check if it contains football data
                if "api.sofascore.com" in response.url:
                    try:
                        data = await response.json()
                        matching_request["response_data_preview"] = json.dumps(data, indent=2)[:1500] + "..."
                        matching_request["contains_live_data"] = "events" in data or "event" in data
                        matching_request["uses_graphql"] = "graphql" in response.url.lower()
                        print(f"\n✅ CAPTURED LIVE DATA: {response.url}")
                        print(f"   Status: {response.status}")
                        print(f"   Preview: {matching_request['response_data_preview']}")
                    except Exception as e:
                        matching_request["response_data_preview"] = f"Could not parse JSON: {e}"
                        matching_request["contains_live_data"] = False
                        matching_request["uses_graphql"] = False
        
        page.on("request", capture_request)
        page.on("response", capture_response)
        
        # 1. Navigate directly to live page
        print("\n1. Navigating to https://www.sofascore.com/football/live...")
        await page.goto("https://www.sofascore.com/football/live", wait_until="networkidle", timeout=120000)
        
        print("\n2. Waiting 60 seconds to let all data load...")
        await asyncio.sleep(60)
        
        # Save report
        report_path = "sofascore_network_report_final.json"
        print(f"\n3. Saving final network report to {report_path}")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump({
                "report_generated_at": datetime.now().isoformat(),
                "total_requests": len(all_requests),
                "requests": all_requests
            }, f, indent=2)
        
        print(f"\n✅ Report saved! Total requests: {len(all_requests)}")
        
        # Print summary of API requests
        api_requests = [r for r in all_requests if "api.sofascore.com" in r.get("url", "")]
        if api_requests:
            print("\n" + "=" * 100)
            print("API REQUESTS FOUND!")
            print("=" * 100)
            for req in api_requests:
                print(f"\n- {req.get('method')} {req.get('url')}")
                print(f"  Status: {req.get('response_status')}")
                print(f"  Contains live data: {req.get('contains_live_data')}")
        else:
            print("\n❌ No api.sofascore.com requests found!")
        
        # Check if Cloudflare is blocking
        page_content = await page.content()
        if "cloudflare" in page_content.lower():
            print("\n⚠️ CLOUDFLARE IS BLOCKING THE PAGE!")
        
        await browser.close()
        print("\n✅ Done!")

if __name__ == "__main__":
    asyncio.run(main())
