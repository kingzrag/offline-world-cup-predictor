
#!/usr/bin/env python3
from curl_cffi import requests
import json
import sys

def investigate():
    print("=" * 80)
    print("SOFASCORE SCRAPING INVESTIGATION")
    print("=" * 80)
    print()

    # 1. Try fetching main website first to get cookies
    print("1. Testing main website https://www.sofascore.com/")
    print("-" * 80)
    main_url = "https://www.sofascore.com/"
    try:
        # Impersonate a real browser and follow redirects
        session = requests.Session(impersonate="chrome120")
        response = session.get(main_url, timeout=30)
        print(f"  Status: {response.status_code}")
        print(f"  Cookies received: {len(session.cookies)}")
        for name, value in session.cookies.items():
            print(f"    - {name}={value}")
        print(f"  Response headers snippet: {dict(list(response.headers.items())[:10])}")
        print()

        # Check response content
        content = response.text
        if "Just a moment" in content or "Cloudflare" in content:
            print("  ⚠️  CLOUDFLARE CHALLENGE DETECTED!")

        # Now try the live matches endpoint
        print("2. Testing live matches endpoint")
        print("-" * 80)
        api_url = "https://api.sofascore.com/api/v1/sport/football/events/live"
        headers = {
            "Referer": main_url,
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "https://www.sofascore.com"
        }
        api_response = session.get(api_url, headers=headers, timeout=30)
        print(f"  API URL: {api_url}")
        print(f"  Status: {api_response.status_code}")
        try:
            print(f"  Response JSON: {json.dumps(api_response.json(), indent=4)[:500]}...")
        except Exception as e:
            print(f"  Response text: {api_response.text[:500]}...")

    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    investigate()
