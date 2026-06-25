from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Dict, Any, List

from utils.config import settings
from utils.logger import logger
from collectors import FootballDataCollector
from collectors.api_football import APIFootballCollector
from models import Competition, Team, Player, Injury, Match, Standing

class CollectionService:
    """
    Orchestration service for data collection pipelines.
    Queries external endpoints and writes atomic transaction transactions to DB.

    Supported data sources:
      - Football-Data.org  (competitions, standings, matches)
      - API-Football       (live match data, red cards, current minute)
      - Transfermarkt      (injuries, suspensions, squad values)
      - FIFA Rankings      (fifa rankings service)
      - Elo Ratings        (elo service)
      - The Odds API       (handled via OddsService)
    """
    def __init__(self):
        self.fd_collector = FootballDataCollector(settings.FOOTBALL_DATA_API_KEY)
        self.api_football_collector = APIFootballCollector(settings.API_FOOTBALL_KEY)

    def _get_or_create_team(self, db: Session, api_id: str, name: str, short_name: str = None, tla: str = None, crest_url: str = None) -> Team:
        """
        Looks up a team by api_id, then falls back to case-insensitive name/alias matching
        to merge historical and API records instead of creating duplicates.
        """
        # 1. Exact lookup by api_id
        team = db.query(Team).filter_by(api_id=api_id).first()
        if team:
            # Sync metadata fields if they were missing
            updated = False
            if not team.short_name and short_name:
                team.short_name = short_name
                updated = True
            if not team.tla and tla:
                team.tla = tla
                updated = True
            if not team.crest_url and crest_url:
                team.crest_url = crest_url
                updated = True
            if updated:
                db.flush()
            return team

        # 2. Case-insensitive / alias-based name matching
        def clean_name(n):
            n = n.lower().strip()
            n = n.replace("-", " ")
            n = n.replace("&", "and")
            aliases = {
                "usa": "united states",
                "us": "united states",
                "united states of america": "united states",
                "czechia": "czech republic",
                "congo dr": "dr congo",
                "republic of ireland": "ireland",
                "côte d'ivoire": "ivory coast",
                "cote d'ivoire": "ivory coast",
            }
            return aliases.get(n, n)

        target_clean = clean_name(name)

        # Retrieve all teams to perform flexible name mapping
        all_teams = db.query(Team).all()
        for t in all_teams:
            if clean_name(t.name) == target_clean:
                logger.info(f"Merging team '{name}' with existing team ID {t.id} ('{t.name}') by setting api_id to {api_id}")
                t.api_id = api_id
                if short_name:
                    t.short_name = short_name
                if tla:
                    t.tla = tla
                if crest_url:
                    t.crest_url = crest_url
                db.flush()
                return t

        # 3. Create a brand new team record
        team = Team(
            api_id=api_id,
            name=name,
            short_name=short_name,
            tla=tla,
            crest_url=crest_url
        )
        db.add(team)
        db.flush()
        return team

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
                team_db = self._get_or_create_team(
                    db,
                    api_id=team_api_id,
                    name=team_data["name"],
                    short_name=team_data.get("short_name"),
                    tla=team_data.get("tla"),
                    crest_url=team_data.get("crest")
                )

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
        summary: Dict[str, Any] = {
            "matches": 0,
            "updated_count": 0,
            "updated_match_ids": [],
            "changes": [],
        }
        created_teams_count = 0
        placeholder_matches_skipped = 0

        try:
            target_comp = db.query(Competition).filter_by(code=competition_code).first()
            if not target_comp:
                logger.error(f"Competition {competition_code} not found.")
                return summary

            logger.info("Ingesting league matches...")
            matches_data = await self.fd_collector.fetch_matches(competition_code)
            if not matches_data:
                logger.warning(
                    f"No match data returned for {competition_code} — skipping ingestion cycle"
                )
                return summary

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

                home_team = self._get_or_create_team(
                    db,
                    api_id=home_api_id,
                    name=home_team_data["name"],
                    short_name=home_team_data.get("shortName"),
                    tla=home_team_data.get("tla")
                )
                away_team = self._get_or_create_team(
                    db,
                    api_id=away_api_id,
                    name=away_team_data["name"],
                    short_name=away_team_data.get("shortName"),
                    tla=away_team_data.get("tla")
                )

                existing_match = db.query(Match).filter_by(api_id=str(m["id"])).first()
                # Parse as aware UTC datetime, then store as naive UTC.
                # Explicitly converting to UTC before stripping tzinfo ensures
                # the value stored is always UTC regardless of server timezone.
                _aware = datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00"))
                utc_date = _aware.astimezone(timezone.utc).replace(tzinfo=None)
                score_data = m.get("score", {})
                full_time = score_data.get("fullTime", {})
                half_time = score_data.get("halfTime", {})
                home_score = full_time.get("home")
                away_score = full_time.get("away")
                match_status = m["status"]

                # During live play fullTime may lag; fall back to halfTime when needed.
                if home_score is None and away_score is None and match_status in {"IN_PLAY", "PAUSED"}:
                    home_score = half_time.get("home")
                    away_score = half_time.get("away")

                winner = score_data.get("winner")
                live_minute = m.get("minute") if match_status in {"IN_PLAY", "PAUSED"} else None

                before_state = None
                if existing_match:
                    before_state = {
                        "home_score": existing_match.home_score,
                        "away_score": existing_match.away_score,
                        "status": existing_match.status,
                        "live_minute": existing_match.live_minute,
                        "winner": existing_match.winner,
                    }

                if not existing_match:
                    existing_match = Match(
                        api_id=str(m["id"]),
                        competition_id=target_comp.id,
                        home_team_id=home_team.id,
                        away_team_id=away_team.id,
                        utc_date=utc_date,
                        status=match_status,
                        stage=m.get("stage"),
                        group=m.get("group"),
                        home_score=home_score,
                        away_score=away_score,
                        winner=winner,
                        live_minute=live_minute,
                    )
                    db.add(existing_match)
                else:
                    existing_match.utc_date = utc_date
                    existing_match.status = match_status
                    existing_match.stage = m.get("stage") or existing_match.stage
                    existing_match.group = m.get("group") or existing_match.group
                    if home_score is not None:
                        existing_match.home_score = home_score
                    if away_score is not None:
                        existing_match.away_score = away_score
                    if winner is not None:
                        existing_match.winner = winner
                    existing_match.live_minute = live_minute

                after_state = {
                    "home_score": existing_match.home_score,
                    "away_score": existing_match.away_score,
                    "status": existing_match.status,
                    "live_minute": existing_match.live_minute,
                    "winner": existing_match.winner,
                }

                if before_state and before_state != after_state:
                    home_name = home_team.name
                    away_name = away_team.name
                    change_entry = {
                        "match_id": existing_match.id,
                        "api_id": existing_match.api_id,
                        "fixture": f"{home_name} vs {away_name}",
                        "old_score": f"{before_state['home_score']}-{before_state['away_score']}",
                        "new_score": f"{after_state['home_score']}-{after_state['away_score']}",
                        "old_status": before_state["status"],
                        "new_status": after_state["status"],
                        "old_minute": before_state["live_minute"],
                        "new_minute": after_state["live_minute"],
                    }
                    summary["updated_count"] += 1
                    summary["updated_match_ids"].append(existing_match.id)
                    summary["changes"].append(change_entry)
                    logger.info(
                        f"Match updated id={existing_match.id} api_id={existing_match.api_id} "
                        f"({home_name} vs {away_name}): "
                        f"score {change_entry['old_score']} → {change_entry['new_score']}, "
                        f"status {change_entry['old_status']} → {change_entry['new_status']}, "
                        f"minute {change_entry['old_minute']} → {change_entry['new_minute']}"
                    )

                summary["matches"] += 1

            db.commit()
            logger.info(
                f"Skipped {placeholder_matches_skipped} placeholder matches with unknown teams."
            )
            logger.info(
                f"Auto-created {created_teams_count} missing teams during match ingestion."
            )
            logger.info(
                f"Matches ingestion completed: processed={summary['matches']} "
                f"updated={summary['updated_count']} "
                f"updated_ids={summary['updated_match_ids']}"
            )
            return summary

        except Exception as e:
            db.rollback()
            logger.error(f"Error during Matches Ingestion: {str(e)}")
            raise e

    async def ingest_api_football_live(self, db: Session) -> Dict[str, Any]:
        """
        Ingest live match data from API-Football:
        - Fetches live matches
        - Tries to match to existing Match records
        - Updates current_minute, api_football_id, home/away red/yellow cards
        """
        logger.info("Starting API-Football live data ingestion...")
        summary = {
            "live_matches_fetched": 0,
            "matches_updated": 0,
            "red_cards_found": 0,
            "minutes_updated": 0,
            "updated_match_ids": [],
        }
        
        try:
            # Fetch all live fixtures
            live_fixtures = await self.api_football_collector.fetch_live_matches()
            summary["live_matches_fetched"] = len(live_fixtures)
            logger.info(f"Fetched {len(live_fixtures)} live matches from API-Football")

            for fixture_data in live_fixtures:
                # First, get events for this fixture to get red/yellow cards
                fixture_id = fixture_data.get("fixture", {}).get("id")
                if not fixture_id:
                    try:
                        events = await self.api_football_collector.fetch_fixture_events(fixture_id)
                        fixture_data["events"] = events
                    except Exception as e:
                            logger.debug(f"Could not fetch events for fixture {fixture_id}: {e}")
                    
                parsed = self.api_football_collector.parse_live_fixture(fixture_data)
                
                # Try to match the match in our DB
                # Try to match using team names
                home_team_name = parsed["home_team"].get("name")
                away_team_name = parsed["away_team"].get("name")

                # Find matches with same home/away team
                home_team = db.query(Team).filter(Team.name.ilike(home_team_name)).first()
                away_team = db.query(Team).filter(Team.name.ilike(away_team_name)).first()
                if not home_team or not away_team:
                    continue
                
                # Now find the actual match (latest match between these teams that's not finished
                match = (
                    db.query(Match)
                    .filter(
                        Match.home_team_id == home_team.id,
                        Match.away_team_id == away_team.id,
                        Match.status != "FINISHED"
                    )
                    .order_by(Match.utc_date.desc())
                    .first()
                )
                
                if not match:
                    continue  # Skip if we don't have this match in DB
                
                # Okay, we found a match to update!
                updated = False
                
                # Update api_football_id
                if match.api_football_id != parsed["api_football_id"]:
                    match.api_football_id = parsed["api_football_id"]
                    updated = True
                
                # Update current minute
                if parsed["current_minute"] is not None:
                    if match.current_minute != parsed["current_minute"]:
                        match.current_minute = parsed["current_minute"]
                        summary["minutes_updated"] += 1
                        updated = True
                
                # Update red/yellow cards
                old_home_red = match.home_red_cards
                old_away_red = match.away_red_cards
                
                match.home_red_cards = parsed["home_red_cards"]
                match.away_red_cards = parsed["away_red_cards"]
                match.home_yellow_cards = parsed["home_yellow_cards"]
                match.away_yellow_cards = parsed["away_yellow_cards"]
                
                if old_home_red != match.home_red_cards or old_away_red != match.away_red_cards:
                    summary["red_cards_found"] += (
                        (match.home_red_cards + match.away_red_cards) - (old_home_red + old_away_red)
                    )
                    updated = True
                
                # Update current scores too!
                if parsed["current_home_score"] is not None:
                    match.current_home_score = parsed["current_home_score"]
                    updated = True
                if parsed["current_away_score"] is not None:
                    match.current_away_score = parsed["current_away_score"]
                    updated = True
                
                if updated:
                    summary["matches_updated"] += 1
                    summary["updated_match_ids"].append(match.id)
                    logger.info(
                        f"Updated match {match.id} ({home_team_name} vs {away_team_name}: "
                        f"min: {match.current_minute}, "
                        f"home red: {match.home_red_cards}, away red: {match.away_red_cards}"
                    )
            
            db.commit()
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error in API-Football live ingestion: {str(e)}", exc_info=True)
            raise
        
        logger.info(f"API-Football live data ingestion complete: {summary}")
        return summary

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
