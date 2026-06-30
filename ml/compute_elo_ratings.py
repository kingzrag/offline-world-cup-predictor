"""
Compute Elo ratings from all international matches in the database.

Algorithm:
- Process all FINISHED matches chronologically
- Initialize every team at 1500
- Standard football Elo formula with:
  - Competition-weighted K-factor
  - Goal difference multiplier
- Store final ratings in team_elo table

Usage:
    python3 -m ml.compute_elo_ratings
"""

import os
import sys
from datetime import datetime, timezone
from collections import defaultdict

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import asc, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from database.connection import SessionLocal
from models import Match, Team, Competition
from models.team import Team as TeamModel
from models.team_elo import TeamElo
from utils.logger import logger

# ---------------------------------------------------------------------------
# K-factor by competition name
# ---------------------------------------------------------------------------
K_FACTORS = {
    "FIFA World Cup": 60,
    "UEFA Euro": 50,
    "Copa America": 50,
    "African Cup of Nations": 50,
    "AFC Asian Cup": 50,
    "CONCACAF Nations League": 40,
    "UEFA Nations League": 40,
    "FIFA World Cup qualification": 40,
    "World Cup Qualifiers": 40,
    "UEFA Euro qualification": 40,
    "African Cup of Nations qualification": 40,
    "AFC Asian Cup qualification": 40,
    "Friendly": 20,
    "International friendly": 20,
}
DEFAULT_K = 30

INITIAL_ELO = 1500


def goal_diff_multiplier(goal_diff: int) -> float:
    """FIFA-style goal difference multiplier."""
    g = abs(goal_diff)
    if g <= 1:
        return 1.0
    elif g == 2:
        return 1.5
    elif g == 3:
        return 1.75
    else:
        return 1.75 + (g - 3) / 8.0


def expected_score(rating_a: float, rating_b: float) -> float:
    """Expected outcome for team A against team B."""
    return 1.0 / (1.0 + 10.0 ** ((rating_b - rating_a) / 400.0))


def compute_all_elo_ratings():
    """
    Process every FINISHED match in chronological order and compute Elo.

    Returns a dict: {team_name: final_elo_rating}
    """
    db = SessionLocal()
    try:
        # Build a lookup: competition_id -> competition_name
        competitions = {c.id: c.name for c in db.query(Competition).all()}

        # Build a lookup: team_id -> team_name
        teams = {t.id: t.name for t in db.query(Team).filter(Team.gender == 'MEN').all()}

        # Load all finished matches ordered by date
        matches = (
            db.query(Match)
            .filter(Match.status == "FINISHED")
            .filter(Match.home_score.isnot(None))
            .filter(Match.away_score.isnot(None))
            .order_by(asc(Match.utc_date))
            .all()
        )
        logger.info(f"Loaded {len(matches)} finished matches for Elo computation")

        # Elo ratings dict: team_name -> current rating
        elo = defaultdict(lambda: float(INITIAL_ELO))
        matches_processed = 0

        for m in matches:
            home_name = teams.get(m.home_team_id)
            away_name = teams.get(m.away_team_id)
            if not home_name or not away_name:
                continue

            comp_name = competitions.get(m.competition_id, "")
            k = K_FACTORS.get(comp_name, DEFAULT_K)

            home_elo = elo[home_name]
            away_elo = elo[away_name]

            # Actual scores
            home_goals = m.home_score
            away_goals = m.away_score
            goal_diff = home_goals - away_goals

            if goal_diff > 0:
                w_home, w_away = 1.0, 0.0
            elif goal_diff < 0:
                w_home, w_away = 0.0, 1.0
            else:
                w_home, w_away = 0.5, 0.5

            # Expected scores
            e_home = expected_score(home_elo, away_elo)
            e_away = 1.0 - e_home

            # Goal difference multiplier
            g = goal_diff_multiplier(goal_diff)

            # Update ratings
            elo[home_name] = home_elo + k * g * (w_home - e_home)
            elo[away_name] = away_elo + k * g * (w_away - e_away)
            matches_processed += 1

        logger.info(f"Processed {matches_processed} matches, computed Elo for {len(elo)} teams")

        # Print top 20 teams
        sorted_elo = sorted(elo.items(), key=lambda x: x[1], reverse=True)
        logger.info("--- Top 20 Elo Ratings ---")
        for rank, (name, rating) in enumerate(sorted_elo[:20], 1):
            logger.info(f"  {rank:3d}. {name:30s}  {rating:.1f}")

        # Print bottom 5
        logger.info("--- Bottom 5 Elo Ratings ---")
        for rank, (name, rating) in enumerate(sorted_elo[-5:], len(sorted_elo) - 4):
            logger.info(f"  {rank:3d}. {name:30s}  {rating:.1f}")

        return dict(elo)

    finally:
        db.close()


def save_elo_to_db(elo_ratings: dict):
    """
    Upsert all computed Elo ratings into the team_elo table.
    Uses ON CONFLICT (team_name) DO UPDATE.
    """
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        rows = [
            {
                "team_name": name,
                "elo_rating": int(round(rating)),
                "country": name,  # For national teams, country = team name
                "last_updated": now,
            }
            for name, rating in elo_ratings.items()
        ]

        if not rows:
            logger.error("No Elo ratings to save")
            return

        stmt = pg_insert(TeamElo).values(rows)
        upsert = stmt.on_conflict_do_update(
            index_elements=["team_name"],
            set_={
                "elo_rating": stmt.excluded.elo_rating,
                "country": stmt.excluded.country,
                "last_updated": stmt.excluded.last_updated,
            },
        )
        db.execute(upsert)
        db.commit()
        logger.info(f"Saved {len(rows)} Elo ratings to team_elo table")

        # Verify
        count = db.query(TeamElo).count()
        logger.info(f"Verification: team_elo row count = {count}")

    except Exception as e:
        db.rollback()
        logger.error(f"Error saving Elo ratings: {e}")
        raise
    finally:
        db.close()


def save_elo_ranks_to_teams(elo_ratings: dict):
    """
    Populate Team.fifa_ranking from Elo rank order.
    Team with the highest Elo gets rank 1, second gets rank 2, etc.
    This provides real variance in fifa_diff without needing the blocked fifa.com scraper.
    """
    db = SessionLocal()
    try:
        # Sort teams by Elo descending
        sorted_teams = sorted(elo_ratings.items(), key=lambda x: x[1], reverse=True)
        logger.info(f"Assigning Elo-derived FIFA ranks to {len(sorted_teams)} teams...")

        updated = 0
        for rank, (team_name, _) in enumerate(sorted_teams, start=1):
            # Match by exact name first, then ilike fallback
            team = db.query(Team).filter(Team.name == team_name, Team.gender == "MEN").first()
            if not team:
                clean = team_name.lower().replace("fc", "").strip()
                team = db.query(Team).filter(Team.name.ilike(f"%{clean}%"), Team.gender == "MEN").first()
            if team:
                team.fifa_ranking = rank
                updated += 1

        db.commit()
        logger.info(f"Updated fifa_ranking for {updated} teams in teams table")

        # Verify sample
        for name in ["Spain", "France", "Argentina", "Brazil", "England"]:
            t = db.query(Team).filter(Team.name == name, Team.gender == "MEN").first()
            if t:
                logger.info(f"  {name}: fifa_ranking={t.fifa_ranking}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving Elo-derived ranks: {e}")
        raise
    finally:
        db.close()


def main():
    logger.info("=== Elo Rating Computation Start ===")
    elo_ratings = compute_all_elo_ratings()
    save_elo_to_db(elo_ratings)
    save_elo_ranks_to_teams(elo_ratings)
    logger.info("=== Elo Rating Computation Complete ===")


if __name__ == "__main__":
    main()
