import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from models import Team
from utils.logger import logger

FIFA_RANKING_URL = "https://www.fifa.com/fifa-world-ranking/men"


def fetch_fifa_rankings() -> dict:
    """Scrape FIFA men's ranking page and return a mapping of normalized team name → rank.
    Normalization lowers case and strips common suffixes.
    """
    logger.info("Fetching FIFA rankings from %s", FIFA_RANKING_URL)
    resp = requests.get(FIFA_RANKING_URL, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    rankings: dict[str, int] = {}
    for row in soup.select("table tbody tr"):
        cols = row.find_all("td")
        if len(cols) < 2:
            continue
        rank_text = cols[0].get_text(strip=True).replace('#', '')
        try:
            rank = int(rank_text)
        except ValueError:
            continue
        name = cols[1].get_text(strip=True).lower()
        # Strip common words
        name = name.replace("national team", "").replace("team", "").strip()
        rankings[name] = rank
    logger.info("Fetched %d FIFA rankings", len(rankings))
    return rankings


def upsert_fifa_rankings(db: Session, rankings: dict) -> None:
    """Update Team.fifa_ranking for each team that can be matched.
    If a direct match fails, a simple fallback removes "fc" and "cf".
    """
    for team in db.query(Team).all():
        key = team.name.lower()
        rank = rankings.get(key)
        if rank is None:
            fallback = key.replace("fc", "").replace("cf", "").strip()
            rank = rankings.get(fallback)
        if rank is not None:
            team.fifa_ranking = rank
        else:
            logger.warning("No FIFA ranking found for team '%s'", team.name)
    db.commit()
    logger.info("FIFA rankings upsert completed")
