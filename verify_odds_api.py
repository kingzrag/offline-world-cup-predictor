import httpx
import sys
from utils.config import settings

def main():
    api_key = settings.ODDS_API_KEY
    if not api_key:
        print("API Key Valid: NO (API key is empty in settings)")
        sys.exit(1)
        
    print(f"Using API Key: {api_key[:4]}...{api_key[-4:] if len(api_key) > 4 else ''}")
    
    # Check general sports list
    url = "https://api.the-odds-api.com/v4/sports"
    params = {"apiKey": api_key}
    
    try:
        response = httpx.get(url, params=params, timeout=10.0)
        if response.status_code == 200:
            print("API Key Valid: YES")
            sports = response.json()
            soccer_sports = [s for s in sports if s.get("key", "").startswith("soccer")]
            
            print("\nSupported Soccer Sports:")
            for s in soccer_sports[:10]:
                print(f"- {s.get('key')} ({s.get('title')})")
            if len(soccer_sports) > 10:
                print(f"... and {len(soccer_sports) - 10} more.")
                
            # Verify historical odds support
            print("\nChecking historical odds support...")
            hist_url = "https://api.the-odds-api.com/v4/historical/sports/soccer_epl/odds/"
            hist_params = {
                "apiKey": api_key,
                "regions": "uk",
                "markets": "h2h",
                "date": "2024-06-01T12:00:00Z"
            }
            hist_resp = httpx.get(hist_url, params=hist_params, timeout=10.0)
            if hist_resp.status_code == 200:
                print("Historical odds supported: YES")
            else:
                print("Historical odds supported: NO")
                print(f"Details: {hist_resp.status_code} - {hist_resp.text}")
                
        elif response.status_code == 401:
            print("API Key Valid: NO (Unauthorized)")
            sys.exit(1)
        else:
            print(f"API Key Valid: UNKNOWN (Status {response.status_code}: {response.text})")
            sys.exit(1)
            
    except Exception as exc:
        print(f"Error connecting to The Odds API: {exc}")
        sys.exit(1)

if __name__ == "__main__":
    main()
