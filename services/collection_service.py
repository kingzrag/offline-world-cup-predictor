import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from collectors import FootballDataCollector
from collectors.api_football import APIFootballCollector
from collectors.sofascore import SofaScoreCollector
from models import (
    Competition,
    Injury,
    Match,
    MatchEvent,
    MatchLineup,
    MatchStatistic,
    Player,
    PlayerMatchPerformance,
    Standing,
    Suspension,
    SuspensionHistory,
    SuspensionStatus,
    Team,
)
from models.match_event import EventType
from providers.api_football import APIFootballProvider
from providers.base import MatchStatisticsData

# Provider architecture imports
from providers.fbref import FBREF_COMPETITION_MAP, FBrefProvider
from providers.statsbomb import StatsBombProvider
from services.intelligence_service import IntelligenceService
from utils.config import settings
from utils.logger import logger


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
        self.sofascore_collector = SofaScoreCollector()

        # New provider architecture
        try:
            self.fbref_provider = FBrefProvider()
        except Exception as e:
            logger.warning(f"CollectionService: FBref provider init failed: {e}")
            self.fbref_provider = None

        try:
            self.statsbomb_provider = StatsBombProvider()
        except Exception as e:
            logger.warning(f"CollectionService: StatsBomb provider init failed: {e}")
            self.statsbomb_provider = None

        try:
            self.af_provider = APIFootballProvider()
            if not self.af_provider.enabled:
                self.af_provider = None
        except Exception as e:
            logger.warning(f"CollectionService: API-Football provider init failed: {e}")
            self.af_provider = None

        self.intelligence_service = IntelligenceService()

    def _get_or_create_team(
        self,
        db: Session,
        api_id: str,
        name: str,
        short_name: str = None,
        tla: str = None,
        crest_url: str = None,
    ) -> Team:
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
                logger.info(
                    f"Merging team '{name}' with existing team ID {t.id} ('{t.name}') by setting api_id to {api_id}"
                )
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
            crest_url=crest_url,
        )
        db.add(team)
        db.flush()
        return team

    async def ingest_teams(
        self, db: Session, competition_code: str = "WC"
    ) -> Dict[str, Any]:
        logger.info(f"Starting teams ingestion for competition: {competition_code}")
        summary = {"competitions": 0, "teams": 0, "standings": 0}

        try:
            # 1. Competitions Ingestion
            logger.info("Ingesting competitions metadata...")
            comps = await self.fd_collector.fetch_competitions()
            comp_db_map = {}
            for c in comps:
                existing_comp = (
                    db.query(Competition).filter_by(api_id=str(c["id"])).first()
                )
                if not existing_comp:
                    existing_comp = Competition(
                        api_id=str(c["id"]),
                        name=c["name"],
                        code=c["code"],
                        area=c["area"],
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
                target_comp = (
                    db.query(Competition).filter_by(code=competition_code).first()
                )
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
                    crest_url=team_data.get("crest"),
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
                    goals_difference=row["goalDifference"],
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

    async def ingest_players(
        self, db: Session, competition_code: str = "WC"
    ) -> Dict[str, Any]:
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

    async def ingest_injuries(
        self, db: Session, competition_code: str = "WC"
    ) -> Dict[str, Any]:
        """
        Injury ingestion using Transfermarkt as the data source.
        """
        logger.info(
            f"Delegating injury ingestion to TransfermarktService for {competition_code}..."
        )
        from services.transfermarkt_service import TransfermarktService

        tm_service = TransfermarktService()
        return tm_service.ingest_injuries(db, competition_code)

    async def ingest_suspensions(
        self, db: Session, competition_code: str = "WC"
    ) -> Dict[str, Any]:
        """
        Suspension ingestion using Transfermarkt as the data source.
        """
        logger.info(
            f"Delegating suspension ingestion to TransfermarktService for {competition_code}..."
        )
        from services.transfermarkt_service import TransfermarktService

        tm_service = TransfermarktService()
        return tm_service.ingest_suspensions(db, competition_code)

    async def ingest_matches(
        self, db: Session, competition_code: str = "WC"
    ) -> Dict[str, Any]:
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
                    tla=home_team_data.get("tla"),
                )
                away_team = self._get_or_create_team(
                    db,
                    api_id=away_api_id,
                    name=away_team_data["name"],
                    short_name=away_team_data.get("shortName"),
                    tla=away_team_data.get("tla"),
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
                if (
                    home_score is None
                    and away_score is None
                    and match_status in {"IN_PLAY", "PAUSED"}
                ):
                    home_score = half_time.get("home")
                    away_score = half_time.get("away")

                winner = score_data.get("winner")
                live_minute = (
                    m.get("minute") if match_status in {"IN_PLAY", "PAUSED"} else None
                )

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
        - Fetches and stores statistics, lineups, events
        """
        logger.info("Starting API-Football live data ingestion...")
        summary = {
            "live_matches_fetched": 0,
            "matches_updated": 0,
            "red_cards_found": 0,
            "minutes_updated": 0,
            "statistics_updated": 0,
            "lineups_updated": 0,
            "events_updated": 0,
            "updated_match_ids": [],
        }

        try:
            # Fetch all live fixtures
            live_fixtures = await self.api_football_collector.fetch_live_matches()
            summary["live_matches_fetched"] = len(live_fixtures)
            logger.info(f"Fetched {len(live_fixtures)} live matches from API-Football")

            for fixture_data in live_fixtures:
                fixture_id = fixture_data.get("fixture", {}).get("id")
                if not fixture_id:
                    continue

                parsed = self.api_football_collector.parse_live_fixture(fixture_data)

                # Try to match using team names
                home_team_name = parsed["home_team"].get("name")
                away_team_name = parsed["away_team"].get("name")

                home_team = (
                    db.query(Team).filter(Team.name.ilike(home_team_name)).first()
                )
                away_team = (
                    db.query(Team).filter(Team.name.ilike(away_team_name)).first()
                )
                if not home_team or not away_team:
                    continue

                # Find the match in our DB
                match = (
                    db.query(Match)
                    .filter(
                        Match.home_team_id == home_team.id,
                        Match.away_team_id == away_team.id,
                        Match.status != "FINISHED",
                    )
                    .order_by(Match.utc_date.desc())
                    .first()
                )

                if not match:
                    continue

                updated = False

                # Update api_football_id if missing
                if match.api_football_id != str(fixture_id):
                    match.api_football_id = str(fixture_id)
                    updated = True

                # Update current minute
                if parsed["current_minute"] is not None:
                    if match.current_minute != parsed["current_minute"]:
                        match.current_minute = parsed["current_minute"]
                        summary["minutes_updated"] += 1
                        updated = True

                # Update red/yellow cards
                old_home_red = match.home_red_cards or 0
                old_away_red = match.away_red_cards or 0

                match.home_red_cards = parsed["home_red_cards"]
                match.away_red_cards = parsed["away_red_cards"]
                match.home_yellow_cards = parsed["home_yellow_cards"]
                match.away_yellow_cards = parsed["away_yellow_cards"]

                if old_home_red != (match.home_red_cards or 0) or old_away_red != (
                    match.away_red_cards or 0
                ):
                    summary["red_cards_found"] += (
                        (match.home_red_cards or 0) + (match.away_red_cards or 0)
                    ) - (old_home_red + old_away_red)
                    updated = True

                # Update current scores
                if parsed["current_home_score"] is not None:
                    match.current_home_score = parsed["current_home_score"]
                    updated = True
                if parsed["current_away_score"] is not None:
                    match.current_away_score = parsed["current_away_score"]
                    updated = True

                # Now fetch and store statistics, lineups, events
                try:
                    # 1. Fetch and store statistics
                    stats = await self.api_football_collector.fetch_fixture_statistics(
                        fixture_id
                    )
                    parsed_stats = self.api_football_collector.parse_statistics(stats)
                    await self.store_match_statistics(db, match, parsed_stats)
                    summary["statistics_updated"] += 1

                    # 2. Fetch and store lineups
                    lineups = await self.api_football_collector.fetch_fixture_lineups(
                        fixture_id
                    )
                    await self.store_match_lineups(db, match, lineups)
                    summary["lineups_updated"] += 1

                    # 3. Fetch and store events
                    events = await self.api_football_collector.fetch_fixture_events(
                        fixture_id
                    )
                    await self.store_match_events(db, match, events)
                    summary["events_updated"] += 1

                except Exception as e:
                    logger.warning(
                        f"Could not fetch extra data for fixture {fixture_id}: {e}"
                    )

                if updated:
                    summary["matches_updated"] += 1
                    summary["updated_match_ids"].append(match.id)
                    logger.info(
                        f"Updated match {match.id} ({home_team_name} vs {away_team_name}): "
                        f"min: {match.current_minute}, "
                        f"home red: {match.home_red_cards}, away red: {match.away_red_cards}"
                    )

            db.commit()

        except Exception as e:
            db.rollback()
            logger.error(f"Error in API-Football live ingestion: {e}", exc_info=True)
            raise

        logger.info(f"API-Football live data ingestion complete: {summary}")
        return summary

    async def store_match_statistics(
        self, db: Session, match: Match, statistics: Dict[str, Any]
    ) -> None:
        """Store match statistics in match_statistics table"""
        logger.info(f"Storing statistics for match {match.id}")
        # Delete old stats for this match first
        logger.debug(f"Deleting existing statistics for match {match.id}")
        db.query(MatchStatistic).filter_by(match_id=match.id).delete()

        home_stats = statistics.get("home", {})
        away_stats = statistics.get("away", {})

        match_stat = MatchStatistic(
            match_id=match.id,
            home_possession=home_stats.get("Ball possession"),
            away_possession=away_stats.get("Ball possession"),
            home_shots=home_stats.get("Total shots"),
            away_shots=away_stats.get("Total shots"),
            home_shots_on_target=home_stats.get("Shots on target"),
            away_shots_on_target=away_stats.get("Shots on target"),
            home_corners=home_stats.get("Corner kicks"),
            away_corners=away_stats.get("Corner kicks"),
            home_expected_goals=home_stats.get("Expected goals (xG)"),
            away_expected_goals=away_stats.get("Expected goals (xG)"),
            home_fouls=home_stats.get("Fouls"),
            away_fouls=away_stats.get("Fouls"),
            home_offsides=home_stats.get("Offsides"),
            away_offsides=away_stats.get("Offsides"),
        )

        db.add(match_stat)
        logger.debug(f"Added new statistics record for match {match.id}")

        # Also update match table with formation/xG/possession if available
        logger.debug(f"Updating match {match.id} with new stats in match table")
        if home_stats.get("Expected goals (xG)"):
            match.home_expected_goals = home_stats.get("Expected goals (xG)")
        if home_stats.get("Ball possession"):
            match.home_possession = home_stats.get("Ball possession")
        if away_stats.get("Expected goals (xG)"):
            match.away_expected_goals = away_stats.get("Expected goals (xG)")
        if away_stats.get("Ball possession"):
            match.away_possession = away_stats.get("Ball possession")

    async def store_match_lineups(
        self, db: Session, match: Match, lineups: Dict[str, Any]
    ) -> None:
        """Store match lineups in match_lineups table"""
        logger.info(f"Storing lineups for match {match.id}")
        # Delete old lineups first
        logger.debug(f"Deleting existing lineups for match {match.id}")
        db.query(MatchLineup).filter_by(match_id=match.id).delete()

        for side in ["home", "away"]:
            team_data = lineups.get(side)
            if not team_data:
                continue

            # Find team in our DB - map via side
            team = None
            if side == "home" and match.home_team:
                team = match.home_team
            elif side == "away" and match.away_team:
                team = match.away_team

            # Create lineup record
            lineup = MatchLineup(
                match_id=match.id,
                team_id=team.id if team else None,
                formation=team_data.get("formation"),
                starting_xi=str(
                    [p for p in team_data.get("players", []) if p.get("is_starter")]
                ),
                substitutes=str(
                    [p for p in team_data.get("players", []) if not p.get("is_starter")]
                ),
            )

            db.add(lineup)
            logger.debug(f"Added lineup record for {side} team for match {match.id}")

            # Update match formations
            if team_data.get("formation"):
                if side == "home":
                    match.home_formation = team_data.get("formation")
                else:
                    match.away_formation = team_data.get("formation")

            # Also store player ratings in PlayerMatchPerformance
            await self.store_player_performances(
                db, match, side, team_data.get("players", []), team
            )

    async def store_player_performances(
        self, db: Session, match: Match, side: str, players: List[Dict], team
    ):
        """Store player performances (ratings) in PlayerMatchPerformance table"""
        logger.debug(
            f"Storing {len(players)} player performances for match {match.id}, side: {side}"
        )
        for player in players:
            # Check for existing record first
            existing = None
            if player.get("sofa_score_player_id"):
                existing = (
                    db.query(PlayerMatchPerformance)
                    .filter(
                        PlayerMatchPerformance.match_id == match.id,
                        PlayerMatchPerformance.sofa_score_id
                        == str(player.get("sofa_score_player_id")),
                    )
                    .first()
                )

            if existing:
                # Update existing
                logger.debug(
                    f"Updating existing player performance for {player.get('player_name')}"
                )
                existing.player_name = player.get("player_name")
                existing.position = player.get("position")
                existing.is_starter = player.get("is_starter")
                existing.sofa_score_rating = player.get("sofa_score_rating")
            else:
                # Create new
                logger.debug(
                    f"Creating new player performance for {player.get('player_name')}"
                )
                perf = PlayerMatchPerformance(
                    match_id=match.id,
                    team_id=team.id if team else None,
                    sofa_score_id=str(player.get("sofa_score_player_id"))
                    if player.get("sofa_score_player_id")
                    else None,
                    player_name=player.get("player_name"),
                    position=player.get("position"),
                    is_starter=player.get("is_starter"),
                    sofa_score_rating=player.get("sofa_score_rating"),
                )
                db.add(perf)

    async def store_match_events(
        self, db: Session, match: Match, events: List[Dict[str, Any]]
    ) -> None:
        """Store match events (goals, cards, substitutions) in match_events table"""
        logger.info(f"Storing {len(events)} events for match {match.id}")

        for event in events:
            # Check for existing event by SofaScore ID to avoid duplicates
            existing = (
                db.query(MatchEvent)
                .filter(
                    MatchEvent.match_id == match.id,
                    MatchEvent.sofa_score_id == event.get("sofa_score_id"),
                )
                .first()
            )

            # Find team for event
            team = None
            if event.get("is_home") and match.home_team:
                team = match.home_team
            elif not event.get("is_home") and match.away_team:
                team = match.away_team

            event_type = self._event_type_from_provider_value(event.get("type"))
            if event_type is None:
                continue

            if existing:
                # Update existing
                logger.debug(f"Updating existing event {event.get('sofa_score_id')}")
                existing.type = event_type
                existing.minute = event.get("minute")
                existing.description = event.get("description")
                existing.player_name = event.get("player_name")
                existing.team_id = team.id if team else None
            else:
                # Create new
                logger.debug(f"Creating new event {event.get('sofa_score_id')}")
                db_event = MatchEvent(
                    match_id=match.id,
                    team_id=team.id if team else None,
                    type=event_type,
                    minute=event.get("minute"),
                    description=event.get("description"),
                    player_name=event.get("player_name"),
                    sofa_score_id=event.get("sofa_score_id"),
                )
                db.add(db_event)

            # Check if it's a red card and handle suspension!
            if (
                event.get("type") in ["RED_CARD", "SECOND_YELLOW_CARD"]
                and team
                and event.get("player_name")
            ):
                logger.info(
                    f"Red card detected! Handling suspension for {event.get('player_name')}"
                )
                self.handle_red_card_for_suspension(
                    db, match.id, team.id, event.get("player_name")
                )

    async def ingest_sofascore_live(self, db: Session) -> Dict[str, Any]:
        """
        Ingest live match data from SofaScore
        """
        logger.info("Starting SofaScore live data ingestion...")
        summary = {
            "live_matches_fetched": 0,
            "matches_updated": 0,
            "statistics_updated": 0,
            "lineups_updated": 0,
            "events_updated": 0,
            "updated_match_ids": [],
            "errors": [],
        }

        try:
            # Fetch all live matches
            live_data = self.sofascore_collector.get_live_matches()
            if not live_data or not live_data.get("events"):
                logger.warning("No live events returned from SofaScore")
                return summary

            summary["live_matches_fetched"] = len(live_data["events"])
            logger.info(
                f"Fetched {summary['live_matches_fetched']} live matches from SofaScore"
            )

            for event_data in live_data["events"]:
                try:
                    sofa_score_id = str(event_data.get("id"))
                    home_team_name = event_data.get("homeTeam", {}).get("name")
                    away_team_name = event_data.get("awayTeam", {}).get("name")

                    logger.info(
                        f"Processing SofaScore event {sofa_score_id}: {home_team_name} vs {away_team_name}"
                    )

                    # Find the match in our database
                    home_team = (
                        db.query(Team).filter(Team.name.ilike(home_team_name)).first()
                    )
                    away_team = (
                        db.query(Team).filter(Team.name.ilike(away_team_name)).first()
                    )

                    if not home_team or not away_team:
                        logger.debug(
                            f"Skipping event {sofa_score_id}: Teams {home_team_name}/{away_team_name} not found in DB"
                        )
                        continue

                    match = (
                        db.query(Match)
                        .filter(
                            Match.home_team_id == home_team.id,
                            Match.away_team_id == away_team.id,
                            Match.status != "FINISHED",
                        )
                        .order_by(Match.utc_date.desc())
                        .first()
                    )

                    if not match:
                        logger.debug(
                            f"Skipping event {sofa_score_id}: No matching match in DB"
                        )
                        continue

                    # Update match with SofaScore ID if missing
                    if not match.sofa_score_id:
                        match.sofa_score_id = sofa_score_id

                    # Fetch and store statistics
                    raw_stats = self.sofascore_collector.get_match_statistics(
                        sofa_score_id
                    )
                    if raw_stats:
                        parsed_stats = self.sofascore_collector.parse_match_statistics(
                            raw_stats
                        )
                        await self.store_match_statistics(db, match, parsed_stats)
                        summary["statistics_updated"] += 1

                    # Fetch and store lineups
                    raw_lineups = self.sofascore_collector.get_match_lineups(
                        sofa_score_id
                    )
                    if raw_lineups:
                        parsed_lineups = self.sofascore_collector.parse_match_lineups(
                            raw_lineups
                        )
                        await self.store_match_lineups(db, match, parsed_lineups)
                        summary["lineups_updated"] += 1

                    # Fetch and store events
                    raw_events = self.sofascore_collector.get_match_events(
                        sofa_score_id
                    )
                    if raw_events:
                        parsed_events = self.sofascore_collector.parse_match_events(
                            raw_events
                        )
                        await self.store_match_events(db, match, parsed_events)
                        summary["events_updated"] += 1

                    summary["matches_updated"] += 1
                    summary["updated_match_ids"].append(match.id)

                except Exception as e:
                    logger.error(
                        f"Error processing SofaScore event {event_data.get('id')}: {e}",
                        exc_info=True,
                    )
                    summary["errors"].append(str(e))
                    continue

            db.commit()
            logger.info("Committed changes to database")

        except Exception as e:
            db.rollback()
            logger.error(f"Error in SofaScore live ingestion: {e}", exc_info=True)
            summary["errors"].append(str(e))
            raise

        logger.info(f"SofaScore live data ingestion complete: {summary}")
        return summary

    def handle_red_card_for_suspension(
        self, db: Session, match_id: int, team_id: int, player_name: str
    ):
        """
        Create a pending suspension when a red card is detected
        """
        try:
            # Check if there's already a pending suspension for this player
            existing = (
                db.query(Suspension)
                .filter_by(
                    team_id=team_id,
                    player_name=player_name,
                    status=SuspensionStatus.PENDING,
                )
                .first()
            )

            if existing:
                logger.info(f"Pending suspension already exists for {player_name}")
                return

            # Get team info
            team = db.query(Team).filter_by(id=team_id).first()
            if not team:
                logger.error(f"Team not found for id {team_id}")
                return

            # Create new pending suspension
            suspension = Suspension(
                player_name=player_name,
                team_id=team_id,
                team_name=team.name,
                source="SofaScore",
                status=SuspensionStatus.PENDING,
                reason="Red Card",
                suspension_reason="Red Card",
            )
            db.add(suspension)
            db.flush()

            # Create history entry
            history = SuspensionHistory(
                suspension_id=suspension.id,
                old_status=None,
                new_status=SuspensionStatus.PENDING,
                changed_by="SofaScore Collector",
                reason="Red card detected in live match",
            )
            db.add(history)

            db.commit()
            logger.info(f"Created pending suspension for {player_name}")

        except Exception as e:
            db.rollback()
            logger.error(f"Error handling red card suspension: {e}", exc_info=True)

    async def ingest_football_data(
        self, db: Session, competition_code: str = "WC"
    ) -> Dict[str, Any]:
        """
        Orchestrates the FULL data collection pipeline in the correct order:

        Step 1:  Football-Data.org (competitions, teams, standings)
        Step 2:  Football-Data.org (fixtures, match history)
        Step 3:  Transfermarkt (injuries, suspensions, squad values)
        Step 4:  FIFA Rankings
        Step 5:  Elo Ratings
        Step 6:  FBref (match stats, player stats)
        Step 7:  StatsBomb (events, xG, lineups)
        Step 8:  API-Football (stats, lineups, events — if key available)
        Step 9:  Odds API
        Step 10: Match Intelligence (compute all 16 metrics)
        """
        logger.info(
            f"Executing full data collection pipeline for {competition_code}..."
        )
        summary = {}

        # --- Step 1: Football-Data.org (competitions, teams, standings) ---
        try:
            logger.info(
                "Pipeline Step 1: Ingesting Football-Data.org competitions, teams, standings..."
            )
            teams_summary = await self.ingest_teams(db, competition_code)
            summary.update(teams_summary)
        except Exception as e:
            logger.error(f"Pipeline Step 1 (teams) failed: {e}")

        # --- Step 2: Football-Data.org (fixtures, match history) ---
        try:
            logger.info(
                "Pipeline Step 2: Ingesting Football-Data.org matches & history..."
            )
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
            logger.info(
                "Pipeline Step 3c: Ingesting squad market values and procedural rosters..."
            )
            players_summary = await self.ingest_players(db, competition_code)
            summary.update(players_summary)
        except Exception as e:
            logger.error(f"Pipeline Step 3c (squad values) failed: {e}")

        # --- Step 4: FIFA Rankings ---
        try:
            logger.info("Pipeline Step 4: Ingesting FIFA Rankings...")
            from services.fifa_ranking_service import (
                fetch_fifa_rankings,
                upsert_fifa_rankings,
            )

            rankings = fetch_fifa_rankings()
            upsert_fifa_rankings(db, rankings)
            summary["fifa_rankings"] = "success"
        except Exception as e:
            logger.error(f"Pipeline Step 4 (FIFA rankings) failed: {e}")

        # --- Step 5: Elo Ratings ---
        try:
            logger.info("Pipeline Step 5: Ingesting ELO Ratings...")
            from ml.compute_elo_ratings import (
                compute_all_elo_ratings,
                save_elo_ranks_to_teams,
                save_elo_to_db,
            )

            elo_ratings = compute_all_elo_ratings()
            if elo_ratings:
                save_elo_to_db(elo_ratings)
                save_elo_ranks_to_teams(elo_ratings)
                summary["elo_ratings"] = "success"
            else:
                summary["elo_ratings"] = "empty"
        except Exception as e:
            logger.error(f"Pipeline Step 5 (Elo ratings) failed: {e}")

        # --- Step 6: FBref (match stats, player stats) ---
        try:
            logger.info("Pipeline Step 6: Ingesting FBref statistics...")
            fbref_summary = await self.ingest_fbref_stats(db, competition_code)
            summary["fbref"] = fbref_summary
        except Exception as e:
            logger.error(f"Pipeline Step 6 (FBref) failed: {e}")
            summary["fbref"] = {"error": str(e)}

        # --- Step 7: StatsBomb Open Data ---
        try:
            logger.info("Pipeline Step 7: Ingesting StatsBomb Open Data...")
            sb_summary = await self.ingest_statsbomb_data(db, competition_code)
            summary["statsbomb"] = sb_summary
        except Exception as e:
            logger.error(f"Pipeline Step 7 (StatsBomb) failed: {e}")
            summary["statsbomb"] = {"error": str(e)}

        # --- Step 8: API-Football (optional) ---
        try:
            logger.info("Pipeline Step 8: Ingesting API-Football data...")
            af_summary = await self.ingest_api_football_data(db, competition_code)
            summary["api_football"] = af_summary
        except Exception as e:
            logger.error(f"Pipeline Step 8 (API-Football) failed: {e}")
            summary["api_football"] = {"error": str(e)}

        # --- Step 9: Odds API ---
        try:
            logger.info("Pipeline Step 9: Ingesting Odds data...")
            from services.odds_service import OddsService

            odds_service = OddsService()
            raw_odds = odds_service.fetch_upcoming_odds()
            odds_service.store_odds(db, raw_odds)
            summary["odds"] = "success"
        except Exception as e:
            logger.error(f"Pipeline Step 9 (Odds API) failed: {e}")

        # --- Step 10: Match Intelligence ---
        try:
            logger.info("Pipeline Step 10: Computing Match Intelligence...")
            intel_summary = self.build_match_intelligence(db, competition_code)
            summary["match_intelligence"] = intel_summary
        except Exception as e:
            logger.error(f"Pipeline Step 10 (Match Intelligence) failed: {e}")
            summary["match_intelligence"] = {"error": str(e)}

        logger.info(f"Full data collection pipeline completed: {summary}")
        return summary

    # ------------------------------------------------------------------
    # Step 6: FBref ingestion
    # ------------------------------------------------------------------

    async def ingest_fbref_stats(
        self, db: Session, competition_code: str
    ) -> Dict[str, Any]:
        """
        Scrape FBref match statistics for a competition and store them in the DB.
        Skips if FBref is unavailable or competition is not supported.
        """
        summary = {"matches_updated": 0, "skipped": 0, "errors": []}

        if not self.fbref_provider:
            logger.warning("FBref provider not available, skipping FBref ingestion")
            summary["status"] = "provider_unavailable"
            return summary

        if competition_code not in FBREF_COMPETITION_MAP:
            logger.info(
                f"FBref: Competition '{competition_code}' not in supported list, skipping"
            )
            summary["status"] = "competition_not_supported"
            return summary

        try:
            # Get matches from FBref
            fbref_matches = await self.fbref_provider.get_competition_matches(
                competition_code
            )
            logger.info(
                f"FBref: Got {len(fbref_matches)} matches for {competition_code}"
            )

            for fbref_match in fbref_matches:
                if fbref_match.status != "FINISHED":
                    summary["skipped"] += 1
                    continue
                try:
                    # Try to find a corresponding DB match
                    home_name = (
                        fbref_match.home_team.name if fbref_match.home_team else ""
                    )
                    away_name = (
                        fbref_match.away_team.name if fbref_match.away_team else ""
                    )
                    if not home_name or not away_name:
                        summary["skipped"] += 1
                        continue

                    db_match = self._find_db_match_by_teams(
                        db, home_name, away_name, fbref_match.utc_date
                    )
                    if not db_match:
                        summary["skipped"] += 1
                        continue

                    # Fetch and store match statistics
                    fbref_id = (
                        fbref_match.provider_ids.get("FBref", "")
                        if fbref_match.provider_ids
                        else ""
                    )
                    if fbref_id:
                        stats_data = await self.fbref_provider.get_match_statistics(
                            fbref_id
                        )
                        if stats_data:
                            self._upsert_match_statistics(
                                db, db_match.id, stats_data, source="FBref"
                            )
                            summary["matches_updated"] += 1

                except Exception as e:
                    logger.debug(f"FBref: Error processing match: {e}")
                    summary["errors"].append(str(e))
                    continue

            db.commit()
            summary["status"] = "success"

        except Exception as e:
            db.rollback()
            logger.error(f"FBref ingestion failed: {e}", exc_info=True)
            summary["status"] = "failed"
            summary["errors"].append(str(e))

        return summary

    # ------------------------------------------------------------------
    # Step 7: StatsBomb ingestion
    # ------------------------------------------------------------------

    async def ingest_statsbomb_data(
        self, db: Session, competition_code: str
    ) -> Dict[str, Any]:
        """
        Download StatsBomb Open Data for a competition and store competitions,
        matches, match statistics, lineups, player performances, and key events.
        Already-imported matches are skipped automatically.
        """
        summary = {
            "competitions_upserted": 0,
            "matches_processed": 0,
            "matches_created": 0,
            "matches_skipped_already_imported": 0,
            "stats_stored": 0,
            "lineups_stored": 0,
            "player_performances_stored": 0,
            "events_stored": 0,
            "errors": [],
        }

        if not self.statsbomb_provider:
            logger.warning("StatsBomb provider not available, skipping")
            summary["status"] = "provider_unavailable"
            return summary

        from providers.statsbomb import _COMPETITION_CODE_MAP

        if competition_code not in _COMPETITION_CODE_MAP:
            logger.info(
                f"StatsBomb: Competition '{competition_code}' not in Open Data, skipping"
            )
            summary["status"] = "competition_not_in_open_data"
            return summary

        try:
            competition = db.query(Competition).filter_by(code=competition_code).first()
            if not competition:
                provider_comp = next(
                    (
                        c
                        for c in await self.statsbomb_provider.get_competitions()
                        if c.code == competition_code
                    ),
                    None,
                )
                competition = Competition(
                    name=provider_comp.name if provider_comp else competition_code,
                    code=competition_code,
                    area=provider_comp.area if provider_comp else None,
                )
                db.add(competition)
                db.flush()
                summary["competitions_upserted"] += 1

            sb_matches = await self.statsbomb_provider.get_competition_matches(
                competition_code
            )
            logger.info(
                f"StatsBomb: Found {len(sb_matches)} matches for {competition_code}"
            )

            for sb_match in sb_matches:
                try:
                    summary["matches_processed"] += 1

                    home_name = sb_match.home_team.name if sb_match.home_team else ""
                    away_name = sb_match.away_team.name if sb_match.away_team else ""
                    sb_id = (
                        sb_match.provider_ids.get("StatsBomb", "")
                        if sb_match.provider_ids
                        else ""
                    ) or (sb_match.id.replace("statsbomb_", "") if sb_match.id else "")
                    if not sb_id:
                        continue

                    db_match = (
                        db.query(Match).filter_by(statsbomb_id=str(sb_id)).first()
                    )
                    if not db_match:
                        db_match = self._find_db_match_by_teams(
                            db, home_name, away_name, sb_match.utc_date
                        )

                    if not db_match:
                        home_team = self._get_or_create_team_by_name(db, home_name)
                        away_team = self._get_or_create_team_by_name(db, away_name)
                        db_match = Match(
                            competition_id=competition.id,
                            home_team_id=home_team.id,
                            away_team_id=away_team.id,
                            utc_date=sb_match.utc_date,
                            status=sb_match.status or "FINISHED",
                            stage=sb_match.stage,
                            home_score=sb_match.home_score,
                            away_score=sb_match.away_score,
                            winner=self._derive_winner(
                                sb_match.home_score, sb_match.away_score
                            ),
                            statsbomb_id=str(sb_id),
                        )
                        db.add(db_match)
                        db.flush()
                        summary["matches_created"] += 1
                    elif not db_match.statsbomb_id:
                        db_match.statsbomb_id = str(sb_id)
                        db.flush()

                    existing_stats = (
                        db.query(MatchStatistic).filter_by(match_id=db_match.id).first()
                    )
                    has_statsbomb_stats = bool(
                        existing_stats
                        and existing_stats.data_source
                        and "StatsBomb" in existing_stats.data_source
                    )
                    has_statsbomb_players = (
                        db.query(PlayerMatchPerformance)
                        .filter(
                            PlayerMatchPerformance.match_id == db_match.id,
                            PlayerMatchPerformance.statsbomb_id.isnot(None),
                        )
                        .first()
                        is not None
                    )
                    has_statsbomb_events = (
                        db.query(MatchEvent)
                        .filter(
                            MatchEvent.match_id == db_match.id,
                            MatchEvent.description.ilike("StatsBomb:%"),
                        )
                        .first()
                        is not None
                    )
                    has_statsbomb_lineups = (
                        db.query(MatchLineup)
                        .filter(
                            MatchLineup.match_id == db_match.id,
                            MatchLineup.coach_name == "StatsBomb Import",
                        )
                        .count()
                        >= 2
                    )

                    if (
                        has_statsbomb_stats
                        and has_statsbomb_players
                        and has_statsbomb_events
                        and has_statsbomb_lineups
                    ):
                        summary["matches_skipped_already_imported"] += 1
                        continue

                    bundle_counts = self._store_statsbomb_match_bundle(
                        db, db_match, str(sb_id)
                    )
                    summary["stats_stored"] += bundle_counts["stats_stored"]
                    summary["lineups_stored"] += bundle_counts["lineups_stored"]
                    summary["player_performances_stored"] += bundle_counts[
                        "player_performances_stored"
                    ]
                    summary["events_stored"] += bundle_counts["events_stored"]
                    db.commit()

                except Exception as e:
                    logger.debug(
                        f"StatsBomb: Error processing match {sb_match.id}: {e}",
                        exc_info=True,
                    )
                    summary["errors"].append(str(e))
                    db.rollback()
                    continue

            db.commit()
            summary["status"] = "success"

        except Exception as e:
            db.rollback()
            logger.error(f"StatsBomb ingestion failed: {e}", exc_info=True)
            summary["status"] = "failed"
            summary["errors"].append(str(e))

        return summary

    # ------------------------------------------------------------------
    # Step 8: API-Football ingestion
    # ------------------------------------------------------------------

    async def ingest_api_football_data(
        self, db: Session, competition_code: str
    ) -> Dict[str, Any]:
        """
        Ingest match data from API-Football if the API key is available.
        """
        summary = {"matches_updated": 0, "stats_stored": 0, "errors": []}

        if not self.af_provider:
            logger.info("API-Football: Provider not available (no key), skipping")
            summary["status"] = "disabled_no_key"
            return summary

        try:
            af_matches = await self.af_provider.get_competition_matches(
                competition_code
            )
            logger.info(
                f"API-Football: Found {len(af_matches)} matches for {competition_code}"
            )

            finished = [m for m in af_matches if m.status == "FINISHED"]
            logger.info(f"API-Football: Processing {len(finished)} finished matches")

            for af_match in finished[:30]:  # Limit per run
                try:
                    home_name = af_match.home_team.name if af_match.home_team else ""
                    away_name = af_match.away_team.name if af_match.away_team else ""
                    db_match = self._find_db_match_by_teams(
                        db, home_name, away_name, af_match.utc_date
                    )

                    af_match_id = af_match.id  # e.g. "af_12345"

                    # Get stats
                    stats_data = await self.af_provider.get_match_statistics(
                        af_match_id
                    )
                    if stats_data:
                        if db_match:
                            self._upsert_match_statistics(
                                db, db_match.id, stats_data, source="APIFootball"
                            )
                            summary["stats_stored"] += 1
                        summary["matches_updated"] += 1

                except Exception as e:
                    logger.debug(f"API-Football: Error processing match: {e}")
                    summary["errors"].append(str(e))
                    continue

            db.commit()
            summary["status"] = "success"

        except Exception as e:
            db.rollback()
            logger.error(f"API-Football ingestion failed: {e}", exc_info=True)
            summary["status"] = "failed"
            summary["errors"].append(str(e))

        return summary

    # ------------------------------------------------------------------
    # Step 10: Match Intelligence
    # ------------------------------------------------------------------

    def build_match_intelligence(
        self, db: Session, competition_code: str
    ) -> Dict[str, Any]:
        """
        Compute all 16 Match Intelligence metrics for every recent match
        in the given competition and log the results.
        """
        summary = {"matches_processed": 0, "errors": []}

        try:
            competition = (
                db.query(Competition)
                .filter(Competition.code == competition_code)
                .first()
            )
            if not competition:
                summary["status"] = "competition_not_found"
                return summary

            recent_matches = (
                db.query(Match)
                .filter(
                    Match.competition_id == competition.id,
                    Match.status == "FINISHED",
                )
                .order_by(desc(Match.utc_date))
                .limit(20)
                .all()
                if competition
                else []
            )

            # Import desc for this query
            from sqlalchemy import desc as _desc

            recent_matches = (
                db.query(Match)
                .filter(
                    Match.competition_id == competition.id,
                )
                .order_by(_desc(Match.utc_date))
                .limit(20)
                .all()
            )

            for match in recent_matches:
                try:
                    intelligence = (
                        self.intelligence_service.calculate_match_intelligence(
                            db, match
                        )
                    )
                    summary["matches_processed"] += 1
                    logger.debug(
                        f"Intelligence for match {match.id}: "
                        f"confidence={intelligence.confidence_score:.2f}, "
                        f"completeness={intelligence.data_completeness:.0%}"
                    )
                except Exception as e:
                    logger.debug(f"Intelligence error for match {match.id}: {e}")
                    summary["errors"].append(str(e))

            summary["status"] = "success"

        except Exception as e:
            logger.error(f"Match Intelligence build failed: {e}", exc_info=True)
            summary["status"] = "failed"
            summary["errors"].append(str(e))

        return summary

    # ------------------------------------------------------------------
    # Shared helper methods for the new providers
    # ------------------------------------------------------------------

    def _event_type_from_provider_value(
        self, raw_type: Optional[str]
    ) -> Optional[EventType]:
        if not raw_type:
            return None
        normalized = str(raw_type).strip().upper()
        mapping = {
            "GOAL": EventType.GOAL,
            "PENALTY_GOAL": EventType.PENALTY_GOAL,
            "OWN_GOAL": EventType.OWN_GOAL,
            "OWN_GOAL_FOR": EventType.OWN_GOAL,
            "YELLOW_CARD": EventType.YELLOW_CARD,
            "SECOND_YELLOW_CARD": EventType.SECOND_YELLOW_CARD,
            "RED_CARD": EventType.RED_CARD,
            "SUBSTITUTION": EventType.SUBSTITUTION,
            "INJURY": EventType.INJURY,
            "VAR_CHECK": EventType.VAR_CHECK,
        }
        return mapping.get(normalized)

    def _find_db_match_by_teams(
        self,
        db: Session,
        home_name: str,
        away_name: str,
        match_date: Optional[datetime],
        date_tolerance_days: int = 3,
    ) -> Optional[Match]:
        """
        Find a DB match by fuzzy team name matching + date proximity.
        Returns None if no match found.
        """

        def _normalize(name: str) -> str:
            return name.lower().strip().replace("-", " ")

        home_clean = _normalize(home_name)
        away_clean = _normalize(away_name)

        # Try exact team name match first
        home_team = db.query(Team).filter(Team.name.ilike(f"%{home_name}%")).first()
        away_team = db.query(Team).filter(Team.name.ilike(f"%{away_name}%")).first()

        if not home_team or not away_team:
            return None

        query = db.query(Match).filter(
            Match.home_team_id == home_team.id,
            Match.away_team_id == away_team.id,
        )

        if match_date:
            from_date = match_date - timedelta(days=date_tolerance_days)
            to_date = match_date + timedelta(days=date_tolerance_days)
            query = query.filter(
                Match.utc_date >= from_date,
                Match.utc_date <= to_date,
            )

        return query.order_by(Match.utc_date.desc()).first()

    def _get_or_create_team_by_name(self, db: Session, name: str) -> Team:
        if name and any(s in name.lower() for s in ["women", "women's", "woman"]):
            raise ValueError(f"Rejecting women's team lookup/creation: {name}")

        team = db.query(Team).filter(Team.name.ilike(name)).first()
        if team:
            return team
        team = db.query(Team).filter(Team.name.ilike(f"%{name}%")).first()
        if team:
            return team
        team = Team(name=name)
        db.add(team)
        db.flush()
        return team

    def _get_or_create_player(
        self,
        db: Session,
        team_id: int,
        player_name: str,
        provider_api_id: Optional[str] = None,
        position: Optional[str] = None,
    ) -> Player:
        player = None
        if provider_api_id:
            player = db.query(Player).filter_by(api_id=provider_api_id).first()
        if not player:
            player = (
                db.query(Player)
                .filter(
                    Player.team_id == team_id,
                    Player.name.ilike(player_name),
                )
                .first()
            )
        if player:
            if provider_api_id and not player.api_id:
                player.api_id = provider_api_id
            if position and not player.position:
                player.position = position
            db.flush()
            return player

        player = Player(
            api_id=provider_api_id,
            team_id=team_id,
            name=player_name,
            position=position,
        )
        db.add(player)
        db.flush()
        return player

    def _derive_winner(
        self, home_score: Optional[int], away_score: Optional[int]
    ) -> Optional[str]:
        if home_score is None or away_score is None:
            return None
        if home_score > away_score:
            return "HOME_TEAM"
        if away_score > home_score:
            return "AWAY_TEAM"
        return "DRAW"

    def _format_formation(self, raw_formation: Optional[Any]) -> Optional[str]:
        if raw_formation is None:
            return None
        digits = [ch for ch in str(raw_formation) if ch.isdigit()]
        if len(digits) <= 1:
            return str(raw_formation)
        return "-".join(digits)

    def _upsert_match_lineup_record(
        self,
        db: Session,
        match_id: int,
        team_id: int,
        formation: Optional[str],
        starters: List[str],
        substitutes: List[str],
        coach_name: str = "StatsBomb Import",
    ) -> None:
        lineup = (
            db.query(MatchLineup).filter_by(match_id=match_id, team_id=team_id).first()
        )
        if not lineup:
            lineup = MatchLineup(match_id=match_id, team_id=team_id)
            db.add(lineup)
        lineup.formation = formation
        lineup.starting_xi = json.dumps(starters)
        lineup.substitutes = json.dumps(substitutes)
        lineup.coach_name = coach_name
        db.flush()

    def _upsert_player_match_performance(
        self,
        db: Session,
        match_id: int,
        team_id: int,
        perf_data: Dict[str, Any],
    ) -> None:
        statsbomb_id = perf_data.get("statsbomb_id")
        query = db.query(PlayerMatchPerformance).filter(
            PlayerMatchPerformance.match_id == match_id,
            PlayerMatchPerformance.team_id == team_id,
        )
        if statsbomb_id:
            perf = query.filter(
                PlayerMatchPerformance.statsbomb_id == statsbomb_id
            ).first()
        else:
            perf = query.filter(
                PlayerMatchPerformance.player_name == perf_data["player_name"]
            ).first()

        if not perf:
            perf = PlayerMatchPerformance(match_id=match_id, team_id=team_id)
            db.add(perf)

        for attr in [
            "player_id",
            "player_name",
            "position",
            "minutes_played",
            "goals",
            "assists",
            "shots",
            "shots_on_target",
            "passes",
            "successful_passes",
            "pass_accuracy",
            "tackles",
            "interceptions",
            "saves",
            "yellow_cards",
            "red_cards",
            "aerial_duels",
            "aerial_duels_won",
            "key_passes",
            "pressures",
            "carries",
            "statsbomb_xg",
        ]:
            if attr in perf_data:
                setattr(perf, attr, perf_data[attr])

        perf.is_starter = 1 if perf_data.get("is_starter") else 0
        perf.statsbomb_id = statsbomb_id
        db.flush()

    def _store_statsbomb_match_bundle(
        self, db: Session, db_match: Match, statsbomb_id: str
    ) -> Dict[str, int]:
        counts = {
            "stats_stored": 0,
            "lineups_stored": 0,
            "player_performances_stored": 0,
            "events_stored": 0,
        }
        match_key = f"statsbomb_{statsbomb_id}"
        raw_events = (
            self.statsbomb_provider.get_full_event_stream(match_key)
            if self.statsbomb_provider
            else []
        )
        raw_lineups = (
            self.statsbomb_provider._get_lineups(int(statsbomb_id))
            if self.statsbomb_provider
            else []
        )
        if not raw_events:
            return counts

        stats_data = None
        if self.statsbomb_provider:
            stats_data = self.statsbomb_provider._calculate_match_stats_from_events(
                match_key, raw_events
            )
        if stats_data:
            self._upsert_match_statistics(
                db, db_match.id, stats_data, source="StatsBomb"
            )
            counts["stats_stored"] += 1

        def normalize(name: str) -> str:
            return (name or "").lower().replace("-", " ").strip()

        team_context: Dict[int, Dict[str, Any]] = {}
        if raw_lineups:
            for lineup in raw_lineups:
                team_name = lineup.get("team_name", "")
                raw_team_id = lineup.get("team_id")
                if raw_team_id is None:
                    continue
                if normalize(team_name) == normalize(db_match.home_team.name):
                    db_team = db_match.home_team
                    side = "home"
                elif normalize(team_name) == normalize(db_match.away_team.name):
                    db_team = db_match.away_team
                    side = "away"
                else:
                    db_team = self._get_or_create_team_by_name(db, team_name)
                    side = "unknown"
                team_context[int(raw_team_id)] = {
                    "db_team": db_team,
                    "side": side,
                    "formation": None,
                    "starters": [],
                    "substitutes": [],
                    "players": {},
                }

        for ev in raw_events:
            if ev.get("type", {}).get("name") != "Starting XI":
                continue
            raw_team_id = ev.get("team", {}).get("id")
            if raw_team_id is None or raw_team_id not in team_context:
                continue
            ctx = team_context[int(raw_team_id)]
            lineup = ev.get("tactics", {}).get("lineup", [])
            ctx["formation"] = self._format_formation(
                ev.get("tactics", {}).get("formation")
            )
            ctx["starters"] = [
                p.get("player", {}).get("name", "")
                for p in lineup
                if p.get("player", {}).get("name")
            ]
            starter_ids = {
                p.get("player", {}).get("id")
                for p in lineup
                if p.get("player", {}).get("id") is not None
            }
            ctx["starter_ids"] = starter_ids
            for p in lineup:
                player = p.get("player", {})
                player_id = player.get("id")
                if player_id is None:
                    continue
                ctx["players"][int(player_id)] = {
                    "player_name": player.get("name"),
                    "position": p.get("position", {}).get("name"),
                    "is_starter": True,
                    "minutes_played": 90,
                    "goals": 0,
                    "assists": 0,
                    "shots": 0,
                    "shots_on_target": 0,
                    "passes": 0,
                    "successful_passes": 0,
                    "pass_accuracy": None,
                    "tackles": 0,
                    "interceptions": 0,
                    "saves": 0,
                    "yellow_cards": 0,
                    "red_cards": 0,
                    "aerial_duels": 0,
                    "aerial_duels_won": 0,
                    "key_passes": 0,
                    "pressures": 0,
                    "carries": 0,
                    "statsbomb_xg": 0.0,
                    "statsbomb_id": str(player_id),
                }

        for lineup in raw_lineups:
            raw_team_id = lineup.get("team_id")
            if raw_team_id is None or int(raw_team_id) not in team_context:
                continue
            ctx = team_context[int(raw_team_id)]
            starter_ids = ctx.get("starter_ids", set())
            for p in lineup.get("lineup", []):
                player_id = p.get("player_id")
                player_name = p.get("player_name")
                if player_id is None:
                    continue
                player_key = int(player_id)
                entry = ctx["players"].setdefault(
                    player_key,
                    {
                        "player_name": player_name,
                        "position": (p.get("positions") or [{}])[0].get("position"),
                        "is_starter": player_key in starter_ids,
                        "minutes_played": None,
                        "goals": 0,
                        "assists": 0,
                        "shots": 0,
                        "shots_on_target": 0,
                        "passes": 0,
                        "successful_passes": 0,
                        "pass_accuracy": None,
                        "tackles": 0,
                        "interceptions": 0,
                        "saves": 0,
                        "yellow_cards": 0,
                        "red_cards": 0,
                        "aerial_duels": 0,
                        "aerial_duels_won": 0,
                        "key_passes": 0,
                        "pressures": 0,
                        "carries": 0,
                        "statsbomb_xg": 0.0,
                        "statsbomb_id": str(player_id),
                    },
                )
                if not entry.get("position"):
                    entry["position"] = (p.get("positions") or [{}])[0].get("position")
            ctx["substitutes"] = [
                p.get("player_name")
                for p in lineup.get("lineup", [])
                if p.get("player_id") not in starter_ids and p.get("player_name")
            ]

        key_pass_map: Dict[str, int] = {}
        goalkeeper_save_types = {
            "shot faced",
            "shot saved",
            "save",
            "saved",
            "penalty saved",
            "penalty saved to post",
            "saved twice",
        }
        on_target_outcomes = {"Saved", "Goal", "Saved to Post"}

        for ev in raw_events:
            raw_team_id = ev.get("team", {}).get("id")
            if raw_team_id is None or int(raw_team_id) not in team_context:
                continue
            ctx = team_context[int(raw_team_id)]
            player = ev.get("player", {})
            player_id = player.get("id")
            player_name = player.get("name")
            etype = ev.get("type", {}).get("name")
            minute = ev.get("minute", 0) or 0
            perf = None
            if player_id is not None:
                perf = ctx["players"].setdefault(
                    int(player_id),
                    {
                        "player_name": player_name,
                        "position": ev.get("position", {}).get("name"),
                        "is_starter": False,
                        "minutes_played": None,
                        "goals": 0,
                        "assists": 0,
                        "shots": 0,
                        "shots_on_target": 0,
                        "passes": 0,
                        "successful_passes": 0,
                        "pass_accuracy": None,
                        "tackles": 0,
                        "interceptions": 0,
                        "saves": 0,
                        "yellow_cards": 0,
                        "red_cards": 0,
                        "aerial_duels": 0,
                        "aerial_duels_won": 0,
                        "key_passes": 0,
                        "pressures": 0,
                        "carries": 0,
                        "statsbomb_xg": 0.0,
                        "statsbomb_id": str(player_id),
                    },
                )
                if not perf.get("position"):
                    perf["position"] = ev.get("position", {}).get("name")

            if etype == "Pass" and perf is not None:
                pass_data = ev.get("pass", {})
                outcome = pass_data.get("outcome", {}).get("name")
                perf["passes"] += 1
                if outcome in (None, "", "Complete"):
                    perf["successful_passes"] += 1
                if pass_data.get("shot_assist") or pass_data.get("goal_assist"):
                    perf["key_passes"] += 1
                event_id = ev.get("id")
                if event_id and player_id is not None:
                    key_pass_map[str(event_id)] = int(player_id)
            elif etype == "Shot" and perf is not None:
                shot = ev.get("shot", {})
                outcome = shot.get("outcome", {}).get("name")
                perf["shots"] += 1
                perf["statsbomb_xg"] += float(shot.get("statsbomb_xg") or 0.0)
                if outcome in on_target_outcomes:
                    perf["shots_on_target"] += 1
                if outcome == "Goal":
                    perf["goals"] += 1
                    self._store_match_event_if_new(
                        db,
                        db_match.id,
                        {
                            "type": "GOAL",
                            "minute": minute,
                            "player_name": player_name,
                            "description": "StatsBomb:Goal",
                            "team_id": ctx["db_team"].id,
                        },
                    )
                    counts["events_stored"] += 1
                key_pass_id = shot.get("key_pass_id")
                if key_pass_id and key_pass_id in key_pass_map:
                    assister = ctx["players"].get(key_pass_map[key_pass_id])
                    if assister is not None:
                        assister["assists"] += 1
            elif etype == "Pressure" and perf is not None:
                perf["pressures"] += 1
            elif etype == "Carry" and perf is not None:
                perf["carries"] += 1
            elif etype == "Interception" and perf is not None:
                perf["interceptions"] += 1
            elif etype == "Tackle" and perf is not None:
                perf["tackles"] += 1
            elif etype == "Duel" and perf is not None:
                duel_name = (
                    ev.get("duel", {}).get("type", {}).get("name") or ""
                ).lower()
                if "tackle" in duel_name:
                    perf["tackles"] += 1
                if "aerial" in duel_name:
                    perf["aerial_duels"] += 1
                    if "won" in duel_name:
                        perf["aerial_duels_won"] += 1
            elif etype == "Goal Keeper" and perf is not None:
                gk_name = (
                    ev.get("goalkeeper", {}).get("type", {}).get("name") or ""
                ).lower()
                if (
                    gk_name in goalkeeper_save_types
                    or "saved" in gk_name
                    or "shot faced" in gk_name
                ):
                    perf["saves"] += 1
            elif etype == "Bad Behaviour" and perf is not None:
                card_name = (
                    ev.get("bad_behaviour", {}).get("card", {}).get("name") or ""
                ).lower()
                if "yellow" in card_name:
                    perf["yellow_cards"] += 1
                    self._store_match_event_if_new(
                        db,
                        db_match.id,
                        {
                            "type": "YELLOW_CARD",
                            "minute": minute,
                            "player_name": player_name,
                            "description": "StatsBomb:Yellow Card",
                            "team_id": ctx["db_team"].id,
                        },
                    )
                    counts["events_stored"] += 1
                elif "red" in card_name:
                    perf["red_cards"] += 1
                    self._store_match_event_if_new(
                        db,
                        db_match.id,
                        {
                            "type": "RED_CARD",
                            "minute": minute,
                            "player_name": player_name,
                            "description": "StatsBomb:Red Card",
                            "team_id": ctx["db_team"].id,
                        },
                    )
                    counts["events_stored"] += 1
            elif etype == "Substitution":
                replacement = ev.get("substitution", {}).get("replacement", {})
                replacement_id = replacement.get("id")
                replacement_name = replacement.get("name")
                if perf is not None and perf.get("minutes_played") in (None, 90):
                    perf["minutes_played"] = minute
                if replacement_id is not None:
                    replacement_perf = ctx["players"].setdefault(
                        int(replacement_id),
                        {
                            "player_name": replacement_name,
                            "position": None,
                            "is_starter": False,
                            "minutes_played": max(0, 90 - minute),
                            "goals": 0,
                            "assists": 0,
                            "shots": 0,
                            "shots_on_target": 0,
                            "passes": 0,
                            "successful_passes": 0,
                            "pass_accuracy": None,
                            "tackles": 0,
                            "interceptions": 0,
                            "saves": 0,
                            "yellow_cards": 0,
                            "red_cards": 0,
                            "aerial_duels": 0,
                            "aerial_duels_won": 0,
                            "key_passes": 0,
                            "pressures": 0,
                            "carries": 0,
                            "statsbomb_xg": 0.0,
                            "statsbomb_id": str(replacement_id),
                        },
                    )
                    replacement_perf["is_starter"] = False
                self._store_match_event_if_new(
                    db,
                    db_match.id,
                    {
                        "type": "SUBSTITUTION",
                        "minute": minute,
                        "player_name": player_name,
                        "description": f"StatsBomb:Substitution->{replacement_name or ''}",
                        "team_id": ctx["db_team"].id,
                    },
                )
                counts["events_stored"] += 1

        for raw_team_id, ctx in team_context.items():
            starters = [name for name in ctx.get("starters", []) if name]
            substitutes = [name for name in ctx.get("substitutes", []) if name]
            self._upsert_match_lineup_record(
                db,
                db_match.id,
                ctx["db_team"].id,
                ctx.get("formation"),
                starters,
                substitutes,
            )
            counts["lineups_stored"] += 1

            if ctx["side"] == "home" and ctx.get("formation"):
                db_match.home_formation = ctx["formation"]
            elif ctx["side"] == "away" and ctx.get("formation"):
                db_match.away_formation = ctx["formation"]

            for player_payload in ctx["players"].values():
                if not player_payload.get("player_name"):
                    continue
                player = self._get_or_create_player(
                    db,
                    ctx["db_team"].id,
                    player_payload["player_name"],
                    provider_api_id=f"statsbomb_{player_payload['statsbomb_id']}"
                    if player_payload.get("statsbomb_id")
                    else None,
                    position=player_payload.get("position"),
                )
                if player_payload.get("passes"):
                    player_payload["pass_accuracy"] = round(
                        100.0
                        * player_payload.get("successful_passes", 0)
                        / player_payload["passes"],
                        1,
                    )
                player_payload["player_id"] = player.id
                self._upsert_player_match_performance(
                    db,
                    db_match.id,
                    ctx["db_team"].id,
                    player_payload,
                )
                counts["player_performances_stored"] += 1

        db.flush()
        return counts

    def _upsert_match_statistics(
        self,
        db: Session,
        match_id: int,
        stats: MatchStatisticsData,
        source: str = "unknown",
    ):
        """
        Upsert match statistics into the DB.
        If a row already exists, only fill in NULL fields (don't overwrite existing data).
        """
        existing = (
            db.query(MatchStatistic).filter(MatchStatistic.match_id == match_id).first()
        )

        if existing:
            # Only fill missing fields — don't overwrite existing provider data
            if existing.home_possession is None and stats.home_possession is not None:
                existing.home_possession = stats.home_possession
            if existing.away_possession is None and stats.away_possession is not None:
                existing.away_possession = stats.away_possession
            if existing.home_shots is None and stats.home_shots is not None:
                existing.home_shots = stats.home_shots
            if existing.away_shots is None and stats.away_shots is not None:
                existing.away_shots = stats.away_shots
            if (
                existing.home_shots_on_target is None
                and stats.home_shots_on_target is not None
            ):
                existing.home_shots_on_target = stats.home_shots_on_target
            if (
                existing.away_shots_on_target is None
                and stats.away_shots_on_target is not None
            ):
                existing.away_shots_on_target = stats.away_shots_on_target
            if (
                existing.home_expected_goals is None
                and stats.home_expected_goals is not None
            ):
                existing.home_expected_goals = stats.home_expected_goals
            if (
                existing.away_expected_goals is None
                and stats.away_expected_goals is not None
            ):
                existing.away_expected_goals = stats.away_expected_goals
            if existing.home_corners is None and stats.home_corners is not None:
                existing.home_corners = stats.home_corners
            if existing.away_corners is None and stats.away_corners is not None:
                existing.away_corners = stats.away_corners
            if existing.home_fouls is None and stats.home_fouls is not None:
                existing.home_fouls = stats.home_fouls
            if existing.away_fouls is None and stats.away_fouls is not None:
                existing.away_fouls = stats.away_fouls
            # Extended columns
            if existing.home_passes is None and stats.home_passes is not None:
                existing.home_passes = stats.home_passes
            if existing.away_passes is None and stats.away_passes is not None:
                existing.away_passes = stats.away_passes
            if (
                existing.home_successful_passes is None
                and stats.home_successful_passes is not None
            ):
                existing.home_successful_passes = stats.home_successful_passes
            if (
                existing.away_successful_passes is None
                and stats.away_successful_passes is not None
            ):
                existing.away_successful_passes = stats.away_successful_passes
            if (
                existing.home_pass_accuracy is None
                and stats.home_pass_accuracy is not None
            ):
                existing.home_pass_accuracy = stats.home_pass_accuracy
            if (
                existing.away_pass_accuracy is None
                and stats.away_pass_accuracy is not None
            ):
                existing.away_pass_accuracy = stats.away_pass_accuracy
            if existing.home_tackles is None and stats.home_tackles is not None:
                existing.home_tackles = stats.home_tackles
            if existing.away_tackles is None and stats.away_tackles is not None:
                existing.away_tackles = stats.away_tackles
            if (
                existing.home_interceptions is None
                and stats.home_interceptions is not None
            ):
                existing.home_interceptions = stats.home_interceptions
            if (
                existing.away_interceptions is None
                and stats.away_interceptions is not None
            ):
                existing.away_interceptions = stats.away_interceptions
            if (
                existing.home_aerial_duels is None
                and stats.home_aerial_duels is not None
            ):
                existing.home_aerial_duels = stats.home_aerial_duels
            if (
                existing.away_aerial_duels is None
                and stats.away_aerial_duels is not None
            ):
                existing.away_aerial_duels = stats.away_aerial_duels
            if existing.home_pressures is None and stats.home_pressures is not None:
                existing.home_pressures = stats.home_pressures
            if existing.away_pressures is None and stats.away_pressures is not None:
                existing.away_pressures = stats.away_pressures
            if existing.home_carries is None and stats.home_carries is not None:
                existing.home_carries = stats.home_carries
            if existing.away_carries is None and stats.away_carries is not None:
                existing.away_carries = stats.away_carries
            # Update source tracking
            if existing.data_source and source not in existing.data_source:
                existing.data_source = f"{existing.data_source},{source}"
            elif not existing.data_source:
                existing.data_source = source
            db.flush()
        else:
            new_stat = MatchStatistic(
                match_id=match_id,
                home_possession=stats.home_possession,
                away_possession=stats.away_possession,
                home_shots=stats.home_shots,
                away_shots=stats.away_shots,
                home_shots_on_target=stats.home_shots_on_target,
                away_shots_on_target=stats.away_shots_on_target,
                home_expected_goals=stats.home_expected_goals,
                away_expected_goals=stats.away_expected_goals,
                home_corners=stats.home_corners,
                away_corners=stats.away_corners,
                home_fouls=stats.home_fouls,
                away_fouls=stats.away_fouls,
                home_passes=stats.home_passes,
                away_passes=stats.away_passes,
                home_successful_passes=stats.home_successful_passes,
                away_successful_passes=stats.away_successful_passes,
                home_pass_accuracy=stats.home_pass_accuracy,
                away_pass_accuracy=stats.away_pass_accuracy,
                home_tackles=stats.home_tackles,
                away_tackles=stats.away_tackles,
                home_interceptions=stats.home_interceptions,
                away_interceptions=stats.away_interceptions,
                home_aerial_duels=stats.home_aerial_duels,
                away_aerial_duels=stats.away_aerial_duels,
                home_pressures=stats.home_pressures,
                away_pressures=stats.away_pressures,
                home_carries=stats.home_carries,
                away_carries=stats.away_carries,
                data_source=source,
            )
            db.add(new_stat)
            db.flush()

    def _store_match_event_if_new(self, db: Session, match_id: int, event_data):
        """Store a match event only if it doesn't already exist (dedup by composite key)."""
        try:
            raw_type = (
                event_data.get("type")
                if isinstance(event_data, dict)
                else getattr(event_data, "type", None)
            )
            event_type = self._event_type_from_provider_value(raw_type)
            if event_type is None:
                return

            minute = (
                event_data.get("minute")
                if isinstance(event_data, dict)
                else getattr(event_data, "minute", None)
            )
            player_name = (
                event_data.get("player_name")
                if isinstance(event_data, dict)
                else getattr(event_data, "player_name", None)
            )
            description = (
                event_data.get("description")
                if isinstance(event_data, dict)
                else getattr(event_data, "description", None)
            )
            team_id = (
                event_data.get("team_id")
                if isinstance(event_data, dict)
                else getattr(event_data, "team_id", None)
            )

            existing = (
                db.query(MatchEvent)
                .filter(
                    MatchEvent.match_id == match_id,
                    MatchEvent.type == event_type,
                    MatchEvent.minute == minute,
                    MatchEvent.player_name == player_name,
                )
                .first()
            )
            if existing:
                return

            new_event = MatchEvent(
                match_id=match_id,
                team_id=team_id,
                type=event_type,
                minute=minute or 0,
                player_name=player_name,
                description=description,
            )
            db.add(new_event)
            db.flush()
        except Exception as e:
            logger.debug(f"Error storing match event: {e}")
