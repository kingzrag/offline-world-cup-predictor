import re
from typing import Any, Dict, List, Optional, Set

from sqlalchemy.orm import Session

from models import (
    Competition,
    Injury,
    Match,
    NationalTeamPlayer,
    Standing,
    Suspension,
    Team,
)
from providers.transfermarkt import (
    NATIONAL_TEAM_TRANSFERMARKT_URLS,
    TransfermarktProvider,
)
from utils.logger import logger

INTERNATIONAL_COMPETITION_CODES = {
    "AFCON",
    "AFCONQ",
    "ASIAN",
    "ASIANQ",
    "CA",
    "CNL",
    "EC",
    "EU",
    "EUQ",
    "FRI",
    "GC",
    "OLY",
    "UNL",
    "WC",
    "WCQ",
    "WCQA",
    "WCQC",
    "WCQE",
}


class TransfermarktService:
    """
    Service to ingest injury and suspension data from Transfermarkt.
    Maintains compatibility with CollectionService while using the resilient provider parser.
    """

    def __init__(self):
        self.provider = TransfermarktProvider()

    def _normalize_team_name(self, team_name: str) -> str:
        normalized = re.sub(r"[^a-z0-9 ]+", " ", team_name.lower())
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized.replace("women s", "women")

    def _resolve_team_url(self, db: Session, team: Team) -> Optional[str]:
        if team.transfermarkt_url:
            return team.transfermarkt_url
        matched_url = self.provider.get_team_url(team.name)
        if matched_url:
            logger.info(
                f"TransfermarktService: auto-populating URL for team {team.name} -> {matched_url}"
            )
            team.transfermarkt_url = matched_url
            db.commit()
            return matched_url
        return None

    def _competition_teams(self, db: Session, competition_code: str) -> List[Team]:
        teams: List[Team] = []
        seen_ids: Set[int] = set()

        target_comp = db.query(Competition).filter_by(code=competition_code).first()
        if target_comp:
            standings = (
                db.query(Standing).filter_by(competition_id=target_comp.id).all()
            )
            for standing in standings:
                if standing.team_id not in seen_ids:
                    teams.append(standing.team)
                    seen_ids.add(standing.team_id)

            if not teams:
                matches = (
                    db.query(Match)
                    .filter(Match.competition_id == target_comp.id)
                    .order_by(Match.utc_date.desc())
                    .all()
                )
                for match in matches:
                    for team in (match.home_team, match.away_team):
                        if team and team.id not in seen_ids:
                            teams.append(team)
                            seen_ids.add(team.id)

        if teams:
            return teams

        if competition_code in INTERNATIONAL_COMPETITION_CODES:
            logger.warning(
                f"TransfermarktService: no standings/matches found for {competition_code}; falling back to mapped national teams"
            )
            normalized_map = {
                self._normalize_team_name(name): url
                for name, url in NATIONAL_TEAM_TRANSFERMARKT_URLS.items()
            }
            db_teams = db.query(Team).all()
            for team in db_teams:
                normalized_team = self._normalize_team_name(team.name)
                if normalized_team in normalized_map and team.id not in seen_ids:
                    teams.append(team)
                    seen_ids.add(team.id)
        return teams

    def _player_market_values(self, db: Session, team_id: int) -> Dict[str, float]:
        values: Dict[str, float] = {}
        for player in db.query(NationalTeamPlayer).filter_by(team_id=team_id).all():
            values[player.player_name] = player.market_value or 0.0
            values[self._normalize_team_name(player.player_name)] = (
                player.market_value or 0.0
            )
        return values

    def _match_market_value(
        self, player_name: str, market_values: Dict[str, float]
    ) -> float:
        if player_name in market_values:
            return market_values[player_name]
        return market_values.get(self._normalize_team_name(player_name), 0.0)

    def _replace_team_injuries(
        self,
        db: Session,
        team: Team,
        injuries_list: List[Dict[str, Any]],
        market_values: Dict[str, float],
    ) -> int:
        db.query(Injury).filter_by(team_id=team.id).delete()
        inserted = 0
        seen = set()
        for injury in injuries_list:
            fingerprint = (
                injury.get("player_name") or "",
                injury.get("injury_type") or "",
                injury.get("expected_return_date"),
            )
            if fingerprint in seen:
                continue
            seen.add(fingerprint)
            db.add(
                Injury(
                    player_name=injury["player_name"],
                    team_id=team.id,
                    team_name=team.name,
                    injury_type=injury["injury_type"],
                    expected_return_date=injury.get("expected_return_date"),
                    days_out=injury.get("days_out"),
                    player_market_value=self._match_market_value(
                        injury["player_name"], market_values
                    ),
                )
            )
            inserted += 1
        return inserted

    def _replace_team_suspensions(
        self,
        db: Session,
        team: Team,
        suspensions_list: List[Dict[str, Any]],
        market_values: Dict[str, float],
    ) -> int:
        db.query(Suspension).filter_by(team_id=team.id).delete()
        inserted = 0
        seen = set()
        for suspension in suspensions_list:
            fingerprint = (
                suspension.get("player_name") or "",
                suspension.get("suspension_reason") or "",
                suspension.get("matches_remaining"),
            )
            if fingerprint in seen:
                continue
            seen.add(fingerprint)
            db.add(
                Suspension(
                    player_name=suspension["player_name"],
                    team_id=team.id,
                    team_name=team.name,
                    suspension_reason=suspension["suspension_reason"],
                    matches_remaining=suspension.get("matches_remaining"),
                    player_market_value=self._match_market_value(
                        suspension["player_name"], market_values
                    ),
                )
            )
            inserted += 1
        return inserted

    def _log_team_report(self, team_name: str, report: Dict[str, Any]) -> None:
        logger.info(
            "Transfermarkt team report | "
            f"team={team_name} url={report.get('url')} status={report.get('status_code')} "
            f"cache={report.get('from_cache')} players={report.get('players_extracted', 0)} "
            f"injuries={report.get('injuries_found', 0)} suspensions={report.get('suspensions_found', 0)} "
            f"parse_failures={report.get('parse_failures', 0)} skipped_rows={report.get('skipped_rows', 0)} "
            f"blocked={report.get('blocked', False)} empty={report.get('empty_page', False)}"
        )

    def ingest_injuries(
        self, db: Session, competition_code: str = "WC"
    ) -> Dict[str, Any]:
        logger.info(
            f"Starting Transfermarkt injuries ingestion for competition: {competition_code}"
        )
        summary: Dict[str, Any] = {
            "injuries": 0,
            "teams_processed": 0,
            "pages_visited": 0,
            "players_extracted": 0,
            "parse_failures": 0,
            "skipped_pages": 0,
            "successful_pages": 0,
            "failed_pages": 0,
        }

        teams = self._competition_teams(db, competition_code)
        if not teams:
            logger.error(
                f"TransfermarktService: no teams available for competition {competition_code}"
            )
            return summary

        for team in teams:
            try:
                url = self._resolve_team_url(db, team)
                if not url:
                    summary["skipped_pages"] += 1
                    logger.warning(
                        f"TransfermarktService: no Transfermarkt URL available for team {team.name}, skipping"
                    )
                    continue

                logger.info(
                    f"TransfermarktService: visiting page {url} for team {team.name}"
                )
                injuries_list, _ = self.provider._scrape_team_data(url)
                report = dict(self.provider.last_scrape_report)
                self._log_team_report(team.name, report)
                summary["pages_visited"] += 1
                summary["players_extracted"] += report.get("players_extracted", 0)
                summary["parse_failures"] += report.get("parse_failures", 0)

                if report.get("blocked") or report.get("error") and not injuries_list:
                    summary["failed_pages"] += 1
                    continue
                if report.get("empty_page") and not injuries_list:
                    summary["successful_pages"] += 1
                    summary["teams_processed"] += 1
                    continue

                market_values = self._player_market_values(db, team.id)
                inserted = self._replace_team_injuries(
                    db, team, injuries_list, market_values
                )
                db.commit()
                summary["injuries"] += inserted
                summary["teams_processed"] += 1
                summary["successful_pages"] += 1
            except Exception as exc:
                db.rollback()
                summary["failed_pages"] += 1
                logger.error(
                    f"TransfermarktService: failed to ingest injuries for {team.name}: {exc}",
                    exc_info=True,
                )

        logger.info(f"Transfermarkt injuries ingestion completed: {summary}")
        return summary

    def ingest_suspensions(
        self, db: Session, competition_code: str = "WC"
    ) -> Dict[str, Any]:
        logger.info(
            f"Starting Transfermarkt suspensions ingestion for competition: {competition_code}"
        )
        summary: Dict[str, Any] = {
            "suspensions": 0,
            "teams_processed": 0,
            "pages_visited": 0,
            "players_extracted": 0,
            "parse_failures": 0,
            "skipped_pages": 0,
            "successful_pages": 0,
            "failed_pages": 0,
        }

        teams = self._competition_teams(db, competition_code)
        if not teams:
            logger.error(
                f"TransfermarktService: no teams available for competition {competition_code}"
            )
            return summary

        for team in teams:
            try:
                url = self._resolve_team_url(db, team)
                if not url:
                    summary["skipped_pages"] += 1
                    logger.warning(
                        f"TransfermarktService: no Transfermarkt URL available for team {team.name}, skipping"
                    )
                    continue

                logger.info(
                    f"TransfermarktService: visiting page {url} for team {team.name}"
                )
                _, suspensions_list = self.provider._scrape_team_data(url)
                report = dict(self.provider.last_scrape_report)
                self._log_team_report(team.name, report)
                summary["pages_visited"] += 1
                summary["players_extracted"] += report.get("players_extracted", 0)
                summary["parse_failures"] += report.get("parse_failures", 0)

                if (
                    report.get("blocked")
                    or report.get("error")
                    and not suspensions_list
                ):
                    summary["failed_pages"] += 1
                    continue
                if report.get("empty_page") and not suspensions_list:
                    summary["successful_pages"] += 1
                    summary["teams_processed"] += 1
                    continue

                market_values = self._player_market_values(db, team.id)
                inserted = self._replace_team_suspensions(
                    db, team, suspensions_list, market_values
                )
                db.commit()
                summary["suspensions"] += inserted
                summary["teams_processed"] += 1
                summary["successful_pages"] += 1
            except Exception as exc:
                db.rollback()
                summary["failed_pages"] += 1
                logger.error(
                    f"TransfermarktService: failed to ingest suspensions for {team.name}: {exc}",
                    exc_info=True,
                )

        logger.info(f"Transfermarkt suspensions ingestion completed: {summary}")
        return summary
