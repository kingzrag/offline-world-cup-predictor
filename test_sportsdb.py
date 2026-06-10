import asyncio
import json
import logging
from utils.logger import logger
from collectors.thesportsdb import TheSportsDBCollector

# Use the free API key defined in .env (default 1 or 123 in our config)
API_KEY = "123"

async def fetch_and_print(team_name: str, collector: TheSportsDBCollector):
    logger.info(f"=== Testing team: {team_name} ===")
    # 1. Team search (searchteams.php?t=team_name)
    team_search = await collector._request("searchteams.php", params={"t": team_name})
    logger.info("--- Team Search Raw JSON ---")
    print(json.dumps(team_search, indent=2))
    # Grab first matching team id
    teams = team_search.get("teams") or []
    if not teams:
        logger.error(f"No team found for {team_name}")
        return
    team = teams[0]
    team_id = team.get("idTeam")
    logger.info(f"Found team id: {team_id}")

    # 2. Player search (searchplayers.php?t=team_name) – returns players across all leagues
    player_search = await collector._request("searchplayers.php", params={"t": team_name})
    logger.info("--- Player Search Raw JSON (searchplayers) ---")
    print(json.dumps(player_search, indent=2))

    # 3. Squad retrieval (lookup_all_players.php?id=team_id)
    squad = await collector._request("lookup_all_players.php", params={"id": team_id})
    logger.info("--- Squad Retrieval Raw JSON (lookup_all_players) ---")
    print(json.dumps(squad, indent=2))

async def main():
    collector = TheSportsDBCollector(API_KEY)
    for name in ["Arsenal", "Manchester City", "Liverpool"]:
        await fetch_and_print(name, collector)

if __name__ == "__main__":
    asyncio.run(main())
