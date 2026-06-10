from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict, Any, List

from utils.config import settings
from utils.logger import logger
from collectors import FootballDataCollector, TheSportsDBCollector
from models import Competition, Team, Player, Injury, Match, Standing

class CollectionService:
    """
    Orchestration service for data collection pipelines.
    Queries external endpoints and writes atomic transaction transactions to DB.

    Supported data sources:
      - Football-Data.org  (competitions, standings, matches)
      - TheSportsDB        (team details, player squads, injuries)
      - The Odds API       (handled via OddsService)
      - ELO Ratings        (handled via EloService)
    """
    def __init__(self):
        self.fd_collector = FootballDataCollector(settings.FOOTBALL_DATA_API_KEY)
        self.tsdb_collector = TheSportsDBCollector(settings.SPORTSDB_API_KEY)

    async def ingest_teams(self, db: Session, competition_code: str = "PL") -> Dict[str, Any]:
        logger.info(f"Starting teams ingestion for competition: {competition_code}")
        summary = {"competitions": 0, "teams": 0, "standings": 0}
        
        try:
            # 1. Competitions Ingestion
            logger.info("Ingesting competitions metadata...")
            comps = await self.fd_collector.fetch_competitions()
            comp_db_map = {}
            for c in comps:
                existing_comp = db.query(Competition).filter_by(api_id=str(c["id"])).first()
                if not existing_comp:
                    existing_comp = Competition(
                        api_id=str(c["id"]),
                        name=c["name"],
                        code=c["code"],
                        area=c["area"]
                    )
                    db.add(existing_comp)
                    db.flush()
                else:
                    existing_comp.name = c["name"]
                    existing_comp.code = c["code"]
                    existing_comp.area = c["area"]
                comp_db_map[existing_comp.code] = existing_comp
                summary["competitions"] += 1
            
            db.commit()
            
            target_comp = comp_db_map.get(competition_code)
            if not target_comp:
                target_comp = db.query(Competition).filter_by(code=competition_code).first()
                if not target_comp:
                    logger.error(f"Competition {competition_code} not found.")
                    return summary

            # 2. Standings & Teams Ingestion
            logger.info(f"Ingesting standings and teams for {competition_code}...")
            standings_data = await self.fd_collector.fetch_standings(competition_code)
            
            db.query(Standing).filter_by(competition_id=target_comp.id).delete()
            db.commit()

            for row in standings_data:
                team_data = row["team"]
                team_api_id = str(team_data["id"])
                team_db = db.query(Team).filter_by(api_id=team_api_id).first()
                
                # Fetch deeper profile details from TheSportsDB
                tsdb_details = await self.tsdb_collector.fetch_team_details(team_data["name"])
                founded = tsdb_details.get("founded") if tsdb_details else None
                venue = tsdb_details.get("venue") if tsdb_details else None

                if not team_db:
                    team_db = Team(
                        api_id=team_api_id,
                        name=team_data["name"],
                        short_name=team_data.get("short_name"),
                        tla=team_data.get("tla"),
                        crest_url=team_data.get("crest"),
                        founded=founded,
                        venue=venue
                    )
                    db.add(team_db)
                    db.flush()
                else:
                    team_db.name = team_data["name"]
                    team_db.short_name = team_data.get("short_name") or team_db.short_name
                    team_db.tla = team_data.get("tla") or team_db.tla
                    team_db.crest_url = team_data.get("crest") or team_db.crest_url
                    if founded: team_db.founded = founded
                    if venue: team_db.venue = venue

                summary["teams"] += 1

                standing_row = Standing(
                    competition_id=target_comp.id,
                    team_id=team_db.id,
                    position=row["position"],
                    played_games=row["playedGames"],
                    won=row["won"],
                    draw=row["draw"],
                    lost=row["lost"],
                    points=row["points"],
                    goals_for=row["goalsFor"],
                    goals_against=row["goalsAgainst"],
                    goals_difference=row["goalDifference"]
                )
                db.add(standing_row)
                summary["standings"] += 1

            db.commit()
            logger.info(f"Teams ingestion completed: {summary}")
            return summary

        except Exception as e:
            db.rollback()
            logger.error(f"Error during Teams Ingestion: {str(e)}")
            raise e

    async def ingest_players(self, db: Session, competition_code: str = "PL") -> Dict[str, Any]:
        logger.info(f"Starting players ingestion for competition: {competition_code}")
        summary = {"players": 0}
        
        try:
            target_comp = db.query(Competition).filter_by(code=competition_code).first()
            if not target_comp:
                logger.error(f"Competition {competition_code} not found.")
                return summary

            standings = db.query(Standing).filter_by(competition_id=target_comp.id).all()
            for standing in standings:
                team_db = standing.team
                team_api_id = team_db.api_id

                logger.info(f"Ingesting roster details for team: {team_db.name}...")
                try:
                    squad = await self.tsdb_collector.fetch_players_by_team(team_api_id, team_db.id, team_db.name)
                    if not squad:
                        logger.warning(f"No squad details retrieved for team: {team_db.name}. Skipping roster update.")
                        continue

                    for p in squad:
                        p_db = db.query(Player).filter_by(api_id=p["api_id"]).first()
                        if not p_db:
                            p_db = Player(
                                api_id=p["api_id"],
                                team_id=team_db.id,
                                name=p["name"],
                                position=p["position"],
                                date_of_birth=p["date_of_birth"],
                                nationality=p["nationality"],
                                role=p["role"]
                            )
                            db.add(p_db)
                        else:
                            p_db.name = p["name"]
                            p_db.position = p["position"]
                            p_db.team_id = team_db.id
                        summary["players"] += 1
                    
                    db.commit()
                except Exception as e:
                    db.rollback()
                    logger.error(f"Failed to ingest roster for team {team_db.name}: {e}. Continuing with next team...")

            logger.info(f"Players ingestion completed: {summary}")
            return summary

        except Exception as e:
            logger.error(f"Error during Players Ingestion: {str(e)}")
            raise e

    async def ingest_injuries(self, db: Session, competition_code: str = "PL") -> Dict[str, Any]:
        """
        Injury ingestion using Transfermarkt as the data source.
        """
        logger.info(f"Delegating injury ingestion to TransfermarktService for {competition_code}...")
        from services.transfermarkt_service import TransfermarktService
        tm_service = TransfermarktService()
        return tm_service.ingest_injuries(db, competition_code)

    async def ingest_suspensions(self, db: Session, competition_code: str = "PL") -> Dict[str, Any]:
        """
        Suspension ingestion using Transfermarkt as the data source.
        """
        logger.info(f"Delegating suspension ingestion to TransfermarktService for {competition_code}...")
        from services.transfermarkt_service import TransfermarktService
        tm_service = TransfermarktService()
        return tm_service.ingest_suspensions(db, competition_code)

    async def ingest_matches(self, db: Session, competition_code: str = "PL") -> Dict[str, Any]:
        logger.info(f"Starting matches ingestion for competition: {competition_code}")
        summary = {"matches": 0}

        try:
            target_comp = db.query(Competition).filter_by(code=competition_code).first()
            if not target_comp:
                logger.error(f"Competition {competition_code} not found.")
                return summary

            logger.info("Ingesting league matches...")
            matches_data = await self.fd_collector.fetch_matches(competition_code)
            for m in matches_data:
                home_api_id = str(m["homeTeam"]["id"])
                away_api_id = str(m["awayTeam"]["id"])
                
                home_team = db.query(Team).filter_by(api_id=home_api_id).first()
                away_team = db.query(Team).filter_by(api_id=away_api_id).first()

                if not home_team or not away_team:
                    logger.warning(f"Skipping match {m['id']} due to missing teams in DB")
                    continue

                existing_match = db.query(Match).filter_by(api_id=str(m["id"])).first()
                utc_date = datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00"))
                full_time = m.get("score", {}).get("fullTime", {})
                home_score = full_time.get("home")
                away_score = full_time.get("away")
                winner = m.get("score", {}).get("winner")

                if not existing_match:
                    existing_match = Match(
                        api_id=str(m["id"]),
                        competition_id=target_comp.id,
                        home_team_id=home_team.id,
                        away_team_id=away_team.id,
                        utc_date=utc_date,
                        status=m["status"],
                        stage=m.get("stage"),
                        group=m.get("group"),
                        home_score=home_score,
                        away_score=away_score,
                        winner=winner
                    )
                    db.add(existing_match)
                else:
                    existing_match.utc_date = utc_date
                    existing_match.status = m["status"]
                    existing_match.stage = m.get("stage") or existing_match.stage
                    existing_match.group = m.get("group") or existing_match.group
                    existing_match.home_score = home_score if home_score is not None else existing_match.home_score
                    existing_match.away_score = away_score if away_score is not None else existing_match.away_score
                    existing_match.winner = winner or existing_match.winner
                
                summary["matches"] += 1
            
            db.commit()
            logger.info(f"Matches ingestion completed: {summary}")
            return summary

        except Exception as e:
            db.rollback()
            logger.error(f"Error during Matches Ingestion: {str(e)}")
            raise e

    async def ingest_football_data(self, db: Session, competition_code: str = "PL") -> Dict[str, Any]:
        """
        Orchestrates the entire ingestion pipeline:
        1. Teams
        2. Players
        3. Injuries
        4. Suspensions
        5. Matches
        """
        logger.info(f"Executing full data collection pipeline for {competition_code}...")
        summary = {}
        
        try:
            # 1. Teams Ingestion
            teams_summary = await self.ingest_teams(db, competition_code)
            summary.update(teams_summary)
            
            # 2. Players Ingestion
            players_summary = await self.ingest_players(db, competition_code)
            summary.update(players_summary)
            
            # 3. Injuries Ingestion
            injuries_summary = await self.ingest_injuries(db, competition_code)
            summary.update(injuries_summary)
            
            # 4. Suspensions Ingestion
            suspensions_summary = await self.ingest_suspensions(db, competition_code)
            summary.update(suspensions_summary)
            
            # 5. Matches Ingestion
            matches_summary = await self.ingest_matches(db, competition_code)
            summary.update(matches_summary)
            
            logger.info(f"Full data collection pipeline completed successfully: {summary}")
            return summary
            
        except Exception as e:
            logger.error(f"Failed to execute full data collection pipeline: {str(e)}")
            raise e
