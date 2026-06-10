import httpx
import asyncio

async def test():
    # Public test key
    api_key = "123"
    team_api_id = "133604"  # Arsenal
    url = f"https://www.thesportsdb.com/api/v1/json/{api_key}/lookup_all_players.php"
    
    print(f"Requesting URL: {url}?id={team_api_id}")
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params={"id": team_api_id})
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Response Text (first 500 chars): {response.text[:500]}")
        try:
            json_data = response.json()
            print("Successfully decoded JSON!")
            print(f"Keys: {list(json_data.keys())}")
            print(f"Player value: {json_data.get('player')}")
        except Exception as e:
            print(f"Failed to decode JSON: {e}")

if __name__ == "__main__":
    asyncio.run(test())
