import httpx
import asyncio

async def test():
    api_key = "123"
    wrong_team_id = "57"  # Football-Data.org ID for Arsenal
    url = f"https://www.thesportsdb.com/api/v1/json/{api_key}/lookup_all_players.php"
    
    print(f"Requesting URL: {url}?id={wrong_team_id}")
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params={"id": wrong_team_id})
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")

if __name__ == "__main__":
    asyncio.run(test())
