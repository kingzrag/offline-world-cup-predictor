from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from collectors.base import BaseCollector
from utils.logger import logger
from providers.base import (
    BaseProvider,
    CompetitionData,
    MatchData,
    TeamData,
    StandingData,
    MatchStatisticsData,
    MatchLineupData,
    MatchEventData,
    InjuryData,
    SuspensionData,
)


class FootballDataProvider(BaseProvider):
    """
    Football-Data.org API Provider
    - Competitions, standings, fixtures, results, teams
    """
    name = "FootballData"
    
    def __init__(self, api_key: str):
        super().__init__()
        self.collector = BaseCollector(api_key=api_key, base_url="https://api.football-data.org/v4")
    
    def _get_headers(self) -> Dict[str, str]:
        return {"X-Auth-Token": self.collector.api_key}
    
    async def get_competitions(self) -> List[CompetitionData]:
        try:
            res = await self.collector._request("competitions", headers=self._get_headers())
            competitions = []
            for comp in res.get("competitions", []):
                competitions.append(CompetitionData(
                    id=str(comp["id"]),
                    name=comp["name"],
                    code=comp["code"],
                    area=comp.get("area", {}).get("name", "Unknown"),
                    source=self.name
                ))
            return competitions
        except Exception as e:
            logger.error(f"{self.name} error in get_competitions: {e}")
            return []
    
    async def get_competition_standings(self, competition_code: str) -> List[StandingData]:
        try:
            res = await self.collector._request(
                f"competitions/{competition_code}/standings",
                headers=self._get_headers()
            )
            standings = []
            for table_holder in res.get("standings", []):
                if table_holder.get("type") == "TOTAL":
                    for row in table_holder.get("table", []):
                        team_data = TeamData(
                            id=str(row["team"]["id"]),
                            name=row["team"]["name"],
                            short_name=row["team"].get("shortName"),
                            tla=row["team"].get("tla"),
                            crest_url=row["team"].get("crest"),
                            source=self.name
                        )
                        standings.append(StandingData(
                            competition_id=competition_code,
                            team=team_data,
                            position=row["position"],
                            played_games=row["playedGames"],
                            won=row["won"],
                            draw=row["draw"],
                            lost=row["lost"],
                            points=row["points"],
                            goals_for=row["goalsFor"],
                            goals_against=row["goalsAgainst"],
                            goals_difference=row["goalDifference"],
                            source=self.name
                        ))
            return standings
        except Exception as e:
            logger.error(f"{self.name} error in get_competition_standings: {e}")
            return []
    
    async def get_competition_matches(self, competition_code: str) -> List[MatchData]:
        try:
            res = await self.collector._request(
                f"competitions/{competition_code}/matches",
                headers=self._get_headers(),
                empty_on_failure=True
            )
            if not res:
                logger.warning(f"{self.name}: No match data returned for {competition_code}")
                return []
            
            matches = []
            for m in res.get("matches", []):
                home_team_data = m.get("homeTeam", {})
                away_team_data = m.get("awayTeam", {})
                
                if not home_team_data.get("id") or not away_team_data.get("id"):
                    continue
                
                home_team = TeamData(
                    id=str(home_team_data["id"]),
                    name=home_team_data["name"],
                    short_name=home_team_data.get("shortName"),
                    tla=home_team_data.get("tla"),
                    crest_url=home_team_data.get("crest"),
                    source=self.name
                )
                away_team = TeamData(
                    id=str(away_team_data["id"]),
                    name=away_team_data["name"],
                    short_name=away_team_data.get("shortName"),
                    tla=away_team_data.get("tla"),
                    crest_url=away_team_data.get("crest"),
                    source=self.name
                )
                
                score = m.get("score", {})
                full_time = score.get("fullTime", {})
                half_time = score.get("halfTime", {})
                home_score = full_time.get("home")
                away_score = full_time.get("away")
                
                _aware = datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00"))
                utc_date = _aware.astimezone(timezone.utc).replace(tzinfo=None)
                
                matches.append(MatchData(
                    id=str(m["id"]),
                    competition_id=competition_code,
                    home_team=home_team,
                    away_team=away_team,
                    utc_date=utc_date,
                    status=m["status"],
                    stage=m.get("stage"),
                    group=m.get("group"),
                    home_score=home_score,
                    away_score=away_score,
                    winner=score.get("winner"),
                    live_minute=m.get("minute"),
                    provider_ids={self.name: str(m["id"])},
                    source=self.name
                ))
            
            return matches
        except Exception as e:
            logger.error(f"{self.name} error in get_competition_matches: {e}")
            return []
    
    async def get_live_matches(self) -> List[MatchData]:
        # Football-Data doesn't have a dedicated live endpoint, so use competition matches and filter
        try:
            # Try a few major international competitions
            matches = []
            for comp in ["WC", "EC", "CL"]:
                try:
                    comp_matches = await self.get_competition_matches(comp)
                    matches.extend([
                        m for m in comp_matches
                        if m.status in ["IN_PLAY", "PAUSED"]
                    ])
                except Exception as e:
                    logger.debug(f"{self.name}: Could not get live matches for {comp}: {e}")
            return matches
        except Exception as e:
            logger.error(f"{self.name} error in get_live_matches: {e}")
            return []
    
    async def get_match_statistics(self, match_id: str) -> Optional[MatchStatisticsData]:
        logger.debug(f"{self.name}: Match statistics not available via Football-Data API")
        return None
    
    async def get_match_lineups(self, match_id: str) -> Optional[Dict[str, Any]]:
        logger.debug(f"{self.name}: Match lineups not available via Football-Data API")
        return None
    
    async def get_match_events(self, match_id: str) -> List[Any]:
        logger.debug(f"{self.name}: Match events not available via Football-Data API")
        return []
    
    async def get_team_injuries(self, team_id: str) -> List[InjuryData]:
        logger.debug(f"{self.name}: Team injuries not available via Football-Data API")
        return []
    
    async def get_team_suspensions(self, team_id: str) -> List[SuspensionData]:
        logger.debug(f"{self.name}: Team suspensions not available via Football-Data API")
        return []
