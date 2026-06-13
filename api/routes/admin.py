"""
api/routes/admin.py
===================
Admin endpoints for seeding and maintaining the database.
These are not meant for regular users — they're for one-off operations.
"""

import os
import csv
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from database.connection import get_db
from models import Match, Team, Competition
from models.team_elo import TeamElo
from utils.logger import logger

router = APIRouter(prefix="/api/admin", tags=["Admin"])

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CSV_PATH = os.path.join(_ROOT, "data", "international", "results.csv")

# Map tournament names to competition codes
TOURNAMENT_CODE_MAP = {
    "FIFA World Cup": "WC",
    "FIFA World Cup qualification": "WCQ",
    "UEFA Euro": "EU",
    "UEFA Euro qualification": "EUQ",
    "Copa America": "CA",
    "African Cup of Nations": "AFCON",
    "AFC Asian Cup": "ASIAN",
    "CONCACAF Gold Cup": "GC",
    "CONCACAF Nations League": "CNL",
    "UEFA Nations League": "UNL",
    "Friendly": "FR",
    "International friendly": "FR",
}


@router.post("/seed-matches", summary="Import international matches from CSV into DB")
def seed_matches(
    since_year: int = Query(
        2018,
        description="Only import matches from this year onwards. Use 2018 for 5+ years of form data.",
    ),
    limit: int = Query(
        5000, ge=1, le=50000,
        description="Maximum number of matches to import.",
    ),
    db: Session = Depends(get_db),
):
    """
    Imports historical international match results from the bundled CSV file
    (data/international/results.csv) into the database.

    This populates the match history needed for form, goals, h2h, ELO momentum,
    strength-of-schedule, and tournament experience features.

    Safe to call multiple times — skips matches that already exist (same teams + date).
    """
    if not os.path.exists(CSV_PATH):
        raise HTTPException(
            status_code=404,
            detail=f"CSV not found at {CSV_PATH}. Ensure the data directory is included in the deployment.",
        )

    logger.info(f"[admin] Starting match import from CSV (since_year={since_year}, limit={limit}) …")

    stats = {"total": 0, "imported": 0, "skipped_existing": 0, "skipped_old": 0, "errors": 0}

    # Pre-build a cache of existing teams
    team_cache: dict[str, Team] = {}
    for t in db.query(Team).all():
        team_cache[t.name.lower()] = t

    # Pre-build competition cache
    comp_cache: dict[str, Competition] = {}
    for c in db.query(Competition).all():
        comp_cache[c.code.lower()] = c

    def get_or_create_team(name: str) -> Team:
        key = name.lower()
        if key in team_cache:
            return team_cache[key]
        team = Team(name=name)
        db.add(team)
        db.flush()
        team_cache[key] = team
        return team

    def get_or_create_competition(name: str, code: str) -> Competition:
        key = code.lower()
        if key in comp_cache:
            return comp_cache[key]
        comp = Competition(name=name, code=code)
        db.add(comp)
        db.flush()
        comp_cache[key] = comp
        return comp

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            stats["total"] += 1
            date_str = row.get("date", "").strip()

            # Parse year quickly
            try:
                year = int(date_str[:4])
            except (ValueError, IndexError):
                stats["errors"] += 1
                continue

            if year < since_year:
                stats["skipped_old"] += 1
                continue

            home_name = row.get("home_team", "").strip()
            away_name = row.get("away_team", "").strip()
            tournament = row.get("tournament", "Friendly").strip()

            try:
                home_score = int(row.get("home_score", 0) or 0)
                away_score = int(row.get("away_score", 0) or 0)
            except ValueError:
                stats["errors"] += 1
                continue

            if not home_name or not away_name:
                stats["errors"] += 1
                continue

            # Parse date
            try:
                match_date = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                stats["errors"] += 1
                continue

            home_team = get_or_create_team(home_name)
            away_team = get_or_create_team(away_name)

            comp_code = TOURNAMENT_CODE_MAP.get(tournament, tournament[:3].upper())
            comp = get_or_create_competition(tournament, comp_code)

            # Check if match already exists (same teams + date)
            existing = db.query(Match).filter(
                Match.home_team_id == home_team.id,
                Match.away_team_id == away_team.id,
                func.date(Match.utc_date) == match_date.date(),
            ).first()

            if existing:
                stats["skipped_existing"] += 1
                continue

            # Determine winner
            if home_score > away_score:
                winner = "HOME_TEAM"
            elif away_score > home_score:
                winner = "AWAY_TEAM"
            else:
                winner = "DRAW"

            match = Match(
                home_team_id=home_team.id,
                away_team_id=away_team.id,
                competition_id=comp.id,
                utc_date=match_date,
                status="FINISHED",
                home_score=home_score,
                away_score=away_score,
                winner=winner,
            )
            db.add(match)
            stats["imported"] += 1

            if stats["imported"] >= limit:
                break

            # Commit in batches of 500
            if stats["imported"] % 500 == 0:
                db.commit()
                logger.info(f"[admin] Imported {stats['imported']} matches so far …")

    db.commit()
    logger.info(
        f"[admin] Match import complete: "
        f"{stats['imported']} imported, {stats['skipped_existing']} existing, "
        f"{stats['skipped_old']} pre-{since_year}, {stats['errors']} errors"
    )

    return {
        "status": "success",
        "stats": stats,
    }


@router.post("/compute-elo", summary="Recompute ELO ratings from match history in the DB")
def recompute_elo(db: Session = Depends(get_db)):
    """
    Recomputes ELO ratings from all FINISHED matches in the database.
    This should be called after /admin/seed-matches to update the team_elo table
    with more accurate ratings based on actual match history.
    """
    try:
        from ml.compute_elo_ratings import compute_all_elo_ratings, save_elo_to_db

        logger.info("[admin] Starting ELO recomputation from DB matches …")
        elo_ratings = compute_all_elo_ratings()

        if not elo_ratings:
            raise HTTPException(status_code=500, detail="ELO computation returned empty results.")

        save_elo_to_db(elo_ratings)

        # Return top 20
        sorted_elo = sorted(elo_ratings.items(), key=lambda x: x[1], reverse=True)
        top_20 = [{"team": name, "elo": round(rating)} for name, rating in sorted_elo[:20]]

        logger.info(f"[admin] ELO recomputation complete. {len(elo_ratings)} teams rated.")

        return {
            "status": "success",
            "teams_rated": len(elo_ratings),
            "top_20": top_20,
        }
    except Exception as e:
        logger.error(f"[admin] ELO recomputation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/db-stats", summary="Database statistics")
def db_stats(db: Session = Depends(get_db)):
    """Returns counts of key tables for debugging."""
    team_count = db.query(Team).count()
    match_count = db.query(Match).count()
    finished_count = db.query(Match).filter_by(status="FINISHED").count()
    elo_count = db.query(TeamElo).count()
    comp_count = db.query(Competition).count()

    # Sample teams with non-null FIFA ranking
    teams_with_rank = db.query(Team).filter(Team.fifa_ranking.isnot(None)).count()
    teams_with_mv = db.query(Team).filter(Team.squad_market_value.isnot(None), Team.squad_market_value > 0).count()

    return {
        "teams": team_count,
        "teams_with_fifa_rank": teams_with_rank,
        "teams_with_squad_value": teams_with_mv,
        "matches_total": match_count,
        "matches_finished": finished_count,
        "elo_ratings": elo_count,
        "competitions": comp_count,
    }
