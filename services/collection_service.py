from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict, Any, List

from utils.config import settings
from utils.logger import logger
from collectors import FootballDataCollector
from models import Competition, Team, Player, Injury, Match, Standing

class CollectionService:
    """
    Orchestration service for data collection pipelines.
    Queries external endpoints and writes atomic transaction transactions to DB.

    Supported data sources:
      - Football-Data.org  (competitions, standings, matches)
      - Transfermarkt      (injuries, suspensions, squad values)
      - FIFA Rankings      (fifa rankings service)
      - Elo Ratings        (elo service)
      - The Odds API       (handled via OddsService)
    """
    def __init__(self):
        self.fd_collector = FootballDataCollector(settings.FOOTBALL_DATA_API_KEY)

    async def ingest_teams(self, db: Session, competition_code: str = "WC") -> Dict[str, Any]:
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
                
                founded = None
                venue = None

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

    async def ingest_players(self, db: Session, competition_code: str = "WC") -> Dict[str, Any]:
        """
        Ingests squad roster details procedurally (replacing TheSportsDB roster details).
        """
        logger.info(f"Ingesting squads procedurally for {competition_code}...")
        try:
            from collect_national_team_squads import ingest_squads
            from ml.compute_national_team_market_values import compute_market_values
            
            ingest_squads()
            compute_market_values()
            
            from models import NationalTeamPlayer
            count = db.query(NationalTeamPlayer).count()
            return {"players": count}
        except Exception as e:
            logger.error(f"Error during procedural squad ingestion: {e}")
            return {"players": 0}

    async def ingest_injuries(self, db: Session, competition_code: str = "WC") -> Dict[str, Any]:
        """
        Injury ingestion using Transfermarkt as the data source.
        """
        logger.info(f"Delegating injury ingestion to TransfermarktService for {competition_code}...")
        from services.transfermarkt_service import TransfermarktService
        tm_service = TransfermarktService()
        return tm_service.ingest_injuries(db, competition_code)

    async def ingest_suspensions(self, db: Session, competition_code: str = "WC") -> Dict[str, Any]:
        """
        Suspension ingestion using Transfermarkt as the data source.
        """
        logger.info(f"Delegating suspension ingestion to TransfermarktService for {competition_code}...")
        from services.transfermarkt_service import TransfermarktService
        tm_service = TransfermarktService()
        return tm_service.ingest_suspensions(db, competition_code)

    async def ingest_matches(self, db: Session, competition_code: str = "WC") -> Dict[str, Any]:
        logger.info(f"Starting matches ingestion for competition: {competition_code}")
        summary = {"matches": 0}
        created_teams_count = 0
        placeholder_matches_skipped = 0

        try:
            target_comp = db.query(Competition).filter_by(code=competition_code).first()
            if not target_comp:
                logger.error(f"Competition {competition_code} not found.")
                return summary

            logger.info("Ingesting league matches...")
            matches_data = await self.fd_collector.fetch_matches(competition_code)
            for m in matches_data:
                home_team_data = m.get("homeTeam", {})
                away_team_data = m.get("awayTeam", {})
                home_api_id = home_team_data.get("id")
                away_api_id = away_team_data.get("id")

                # Skip knockout-stage placeholder matches where teams are not yet decided.
                if not home_api_id or not away_api_id:
                    placeholder_matches_skipped += 1
                    logger.info(
                        f"Skipping placeholder match {m['id']} because teams are not yet assigned."
                    )
                    continue

                home_api_id = str(home_api_id)
                away_api_id = str(away_api_id)

                home_team = db.query(Team).filter_by(api_id=home_api_id).first()
                away_team = db.query(Team).filter_by(api_id=away_api_id).first()

                if not home_team or not away_team:
                    logger.warning(
                        f"Skipping match {m['id']} due to missing teams in DB. "
                        f"Home={home_team_data.get('name')} ({home_api_id}) "
                        f"Away={away_team_data.get('name')} ({away_api_id})"
                    )

                    # --- Self-healing: auto-create missing teams from match payload ---
                    try:
                        if not home_team:
                            home_team = Team(
                                api_id=home_api_id,
                                name=home_team_data["name"],
                                short_name=home_team_data.get("shortName"),
                                tla=home_team_data.get("tla"),
                            )
                            db.add(home_team)
                            db.flush()
                            logger.info(
                                f"Created missing team: {home_team.name} ({home_api_id})"
                            )
                            created_teams_count += 1

                        if not away_team:
                            away_team = Team(
                                api_id=away_api_id,
                                name=away_team_data["name"],
                                short_name=away_team_data.get("shortName"),
                                tla=away_team_data.get("tla"),
                            )
                            db.add(away_team)
                            db.flush()
                            logger.info(
                                f"Created missing team: {away_team.name} ({away_api_id})"
                            )
                            created_teams_count += 1

                    except Exception as team_err:
                        db.rollback()
                        logger.error(
                            f"Failed to auto-create missing team(s) for match {m['id']}: {team_err}. Skipping match."
                        )
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
                        winner=winner,
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
            logger.info(
                f"Skipped {placeholder_matches_skipped} placeholder matches with unknown teams."
            )
            logger.info(
                f"Auto-created {created_teams_count} missing teams during match ingestion."
            )
            logger.info(f"Matches ingestion completed: {summary}")
            return summary

        except Exception as e:
            db.rollback()
            logger.error(f"Error during Matches Ingestion: {str(e)}")
            raise e

    async def ingest_football_data(self, db: Session, competition_code: str = "WC") -> Dict[str, Any]:
        """
        Orchestrates the entire ingestion pipeline:
        Step 1: Football-Data.org (competitions, teams, standings)
        Step 2: Football-Data.org (fixtures, match history)
        Step 3: Transfermarkt (injuries, suspensions, squad values)
        Step 4: FIFA Rankings
        Step 5: Elo Ratings
        Step 6: Odds API
        """
        logger.info(f"Executing full data collection pipeline for {competition_code}...")
        summary = {}
        
        # --- Step 1: Football-Data.org (competitions, teams, standings) ---
        try:
            logger.info("Pipeline Step 1: Ingesting Football-Data.org competitions, teams, standings...")
            teams_summary = await self.ingest_teams(db, competition_code)
            summary.update(teams_summary)
        except Exception as e:
            logger.error(f"Pipeline Step 1 (teams) failed: {e}")
            
        # --- Step 2: Football-Data.org (fixtures, match history) ---
        try:
            logger.info("Pipeline Step 2: Ingesting Football-Data.org matches & history...")
            matches_summary = await self.ingest_matches(db, competition_code)
            summary.update(matches_summary)
        except Exception as e:
            logger.error(f"Pipeline Step 2 (matches) failed: {e}")
            
        # --- Step 3: Transfermarkt (injuries, suspensions, squad values) ---
        # 3a. Injuries
        try:
            logger.info("Pipeline Step 3a: Ingesting Transfermarkt injuries...")
            injuries_summary = await self.ingest_injuries(db, competition_code)
            summary.update(injuries_summary)
        except Exception as e:
            logger.error(f"Pipeline Step 3a (injuries) failed: {e}")
            
        # 3b. Suspensions
        try:
            logger.info("Pipeline Step 3b: Ingesting Transfermarkt suspensions...")
            suspensions_summary = await self.ingest_suspensions(db, competition_code)
            summary.update(suspensions_summary)
        except Exception as e:
            logger.error(f"Pipeline Step 3b (suspensions) failed: {e}")
            
        # 3c. Squad values & procedural roster players (lightweight Transfermarkt-based replacement)
        try:
            logger.info("Pipeline Step 3c: Ingesting squad market values and procedural rosters...")
            players_summary = await self.ingest_players(db, competition_code)
            summary.update(players_summary)
        except Exception as e:
            logger.error(f"Pipeline Step 3c (squad values) failed: {e}")

        # --- Step 4: FIFA Rankings ---
        try:
            logger.info("Pipeline Step 4: Ingesting FIFA Rankings...")
            from services.fifa_ranking_service import fetch_fifa_rankings, upsert_fifa_rankings
            rankings = fetch_fifa_rankings()
            upsert_fifa_rankings(db, rankings)
            summary["fifa_rankings"] = "success"
        except Exception as e:
            logger.error(f"Pipeline Step 4 (FIFA rankings) failed: {e}")
            
        # --- Step 5: Elo Ratings ---
        try:
            logger.info("Pipeline Step 5: Ingesting ELO Ratings...")
            from ml.compute_elo_ratings import compute_all_elo_ratings, save_elo_to_db, save_elo_ranks_to_teams
            elo_ratings = compute_all_elo_ratings()
            if elo_ratings:
                save_elo_to_db(elo_ratings)
                save_elo_ranks_to_teams(elo_ratings)
                summary["elo_ratings"] = "success"
            else:
                summary["elo_ratings"] = "empty"
        except Exception as e:
            logger.error(f"Pipeline Step 5 (Elo ratings) failed: {e}")
            
        # --- Step 6: Odds API ---
        try:
            logger.info("Pipeline Step 6: Ingesting Odds data...")
            from services.odds_service import OddsService
            odds_service = OddsService()
            raw_odds = odds_service.fetch_upcoming_odds()
            odds_service.store_odds(db, raw_odds)
            summary["odds"] = "success"
        except Exception as e:
            logger.error(f"Pipeline Step 6 (Odds API) failed: {e}")
            
        logger.info(f"Full data collection pipeline completed successfully: {summary}")
        return summary
