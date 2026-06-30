import httpx
import logging
import zlib
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from sqlalchemy.dialects.postgresql import insert
from utils.config import settings
from models import Team, Match
from models.bookmaker_odds import BookmakerOdds
from utils.logger import logger

class OddsService:
    """Service responsible for fetching odds from The Odds API and persisting them."""

    BASE_URL = "https://api.the-odds-api.com/v4"

    def _request(self, endpoint: str, params: Dict[str, Any] = None) -> Any:
        """Internal wrapper for HTTP GET with proper error handling and logging."""
        if params is None:
            params = {}
        params["apiKey"] = settings.ODDS_API_KEY
        url = f"{self.BASE_URL}/{endpoint}"
        logger.info(f"Sending GET request to URL: {url} with params: { {k: v for k, v in params.items() if k != 'apiKey'} }")
        try:
            response = httpx.get(url, params=params, timeout=30.0, headers={"User-Agent": "football-platform"})
            if response.status_code != 200:
                logger.error(f"Odds API responded with status {response.status_code}: {response.text}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            logger.error(f"Odds API request failed for {endpoint}: {exc}")
            raise

    # -------------------------------------------------------------------
    # Public fetch methods
    # -------------------------------------------------------------------
    def fetch_upcoming_odds(self) -> List[Dict[str, Any]]:
        """Return a list of upcoming soccer (football) odds for all active soccer leagues."""
        sports = self._request("sports")
        soccer_keys = [s["key"] for s in sports if s.get("key", "").startswith("soccer")]
        if not soccer_keys:
            logger.error("No soccer sports available in The Odds API response.")
            return []
            
        all_odds = []
        logger.info(f"Discovered {len(soccer_keys)} active soccer leagues. Fetching odds...")
        for sport_key in soccer_keys:
            if "winner" in sport_key:
                # Skip outright winner markets
                continue
            try:
                odds = self._request(f"sports/{sport_key}/odds", {"regions": "eu", "markets": "h2h"})
                logger.info(f"Fetched {len(odds)} upcoming matches from sport key: {sport_key}")
                all_odds.extend(odds)
            except Exception as e:
                logger.error(f"Failed to fetch odds for sport key {sport_key}: {e}")
                
        logger.info(f"Total upcoming odds entries collected: {len(all_odds)}")
        return all_odds

    def fetch_match_odds(self, match_id: str) -> List[Dict[str, Any]]:
        """Fetch odds for a single match identified by the API's eventId/match_id."""
        sports = self._request("sports")
        soccer_key = next((s["key"] for s in sports if s.get("key", "").startswith("soccer")), None)
        if not soccer_key:
            return []
        odds = self._request(f"sports/{soccer_key}/odds", {"regions": "eu", "markets": "h2h", "eventId": match_id})
        return odds

    # -------------------------------------------------------------------
    # Transformation & Team/Match Mapping helpers
    # -------------------------------------------------------------------
    def find_team_by_name(self, db: Session, name: str) -> Optional[Team]:
        """Looks up a team in the database using exact, case-insensitive, or partial matches."""
        # Reject women's national teams immediately
        if name and any(s in name.lower() for s in ["women", "women's", "woman"]):
            return None

        # 1. Exact match
        team = db.query(Team).filter(Team.name == name).first()
        if team:
            return team
        # 2. Case-insensitive exact match
        team = db.query(Team).filter(func.lower(Team.name) == name.lower()).first()
        if team:
            return team
        # 3. Simple ILIKE partial match
        team = db.query(Team).filter(Team.name.ilike(f"%{name}%")).first()
        if team:
            return team
        # 4. Suffix stripping search
        parts = [p for p in name.split() if p.lower() not in ["fc", "cf", "ud", "rc", "afc", "sc", "sv"]]
        if parts:
            query = db.query(Team)
            for part in parts:
                query = query.filter(Team.name.ilike(f"%{part}%"))
            team = query.first()
            if team:
                return team
        return None

    def match_odds_to_db(self, db: Session, home_name: str, away_name: str, commence_time_str: str) -> int:
        """Finds the corresponding database match ID, falling back to a deterministic hash integer."""
        # Clean API commence time (e.g. 2026-07-22T20:00:00Z)
        unique_string = f"{home_name}_{away_name}_{commence_time_str}"
        fallback_id = zlib.crc32(unique_string.encode()) & 0x7fffffff
        
        try:
            dt = datetime.fromisoformat(commence_time_str.replace("Z", "+00:00"))
        except Exception:
            return fallback_id
            
        home_team = self.find_team_by_name(db, home_name)
        away_team = self.find_team_by_name(db, away_name)
        if not home_team or not away_team:
            return fallback_id
            
        start_dt = dt - timedelta(days=3)
        end_dt = dt + timedelta(days=3)
        
        match = db.query(Match).filter(
            and_(
                Match.home_team_id == home_team.id,
                Match.away_team_id == away_team.id,
                Match.utc_date >= start_dt,
                Match.utc_date <= end_dt
            )
        ).first()
        if match:
            return match.id
        return fallback_id

    def _flatten_raw(self, db: Session, raw: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert the nested API structure into flat rows ready for upsert."""
        sport = raw.get("sport_key")
        commence_time = raw.get("commence_time")
        home_team = raw.get("home_team", "")
        away_team = raw.get("away_team", "")
        
        if not home_team or not away_team:
            # Fallback if the structure differs
            teams = raw.get("teams", [])
            if len(teams) >= 2:
                home_team, away_team = teams[0], teams[1]
                
        # Get internal integer match ID mapping (falls back deterministically if not scheduled)
        db_match_id = self.match_odds_to_db(db, home_team, away_team, commence_time)
        
        rows = []
        for bookmaker in raw.get("bookmakers", []):
            bk_name = bookmaker.get("title")
            for market in bookmaker.get("markets", []):
                if market.get("key") != "h2h":
                    continue
                
                # Extract outcome prices
                outcomes = {outcome["name"]: outcome["price"] for outcome in market.get("outcomes", [])}
                home_price = outcomes.get(home_team)
                draw_price = outcomes.get("Draw")
                away_price = outcomes.get(away_team)
                
                if home_price is None or away_price is None:
                    # Skip if odds are invalid or missing
                    continue
                    
                row = {
                    "match_id": db_match_id,
                    "sport": sport,
                    "bookmaker": bk_name,
                    "home_team": home_team,
                    "away_team": away_team,
                    "home_odds": float(home_price),
                    "draw_odds": float(draw_price) if draw_price is not None else None,
                    "away_odds": float(away_price),
                    "last_updated": datetime.now(timezone.utc),
                }
                rows.append(row)
        return rows

    # -------------------------------------------------------------------
    # Persistence
    # -------------------------------------------------------------------
    def store_odds(self, db: Session, raw_odds: List[Dict[str, Any]]) -> None:
        """Bulk up-insert odds rows, de-duplicating on match_id + bookmaker."""
        flat_rows: List[Dict[str, Any]] = []
        for entry in raw_odds:
            flat_rows.extend(self._flatten_raw(db, entry))
            
        if not flat_rows:
            logger.info("No odds rows to store.")
            return
            
        stmt = insert(BookmakerOdds).values(flat_rows)
        update_dict = {
            "home_odds": stmt.excluded.home_odds,
            "draw_odds": stmt.excluded.draw_odds,
            "away_odds": stmt.excluded.away_odds,
            "last_updated": stmt.excluded.last_updated,
        }
        upsert = stmt.on_conflict_do_update(index_elements=["match_id", "bookmaker"], set_=update_dict)
        try:
            db.execute(upsert)
            db.commit()
            logger.info(f"Stored/updated {len(flat_rows)} odds rows (across {len(set((r['match_id'], r['bookmaker']) for r in flat_rows))} unique match/bookmaker combos).")
        except Exception as exc:
            db.rollback()
            logger.error(f"Failed to persist odds: {exc}")
            raise
