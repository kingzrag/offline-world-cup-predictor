
#!/usr/bin/env python3
import os
import sys
from datetime import datetime, timezone
from sqlalchemy.orm import Session

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.connection import SessionLocal
from models import Match, Team, Competition


def get_team_by_name(db, name):
    """Get team by name with fuzzy matching."""
    team = db.query(Team).filter(Team.name.ilike(name)).first()
    if not team:
        team = db.query(Team).filter(Team.name.ilike(f"%{name}%")).first()
    return team


def get_last_n_matches(db, team_id, n=10):
    """Get last N matches for a team."""
    matches = (
        db.query(Match)
        .filter(
            Match.home_team_id == team_id,
            Match.status == "FINISHED"
        )
        .union_all(
            db.query(Match)
            .filter(
                Match.away_team_id == team_id,
                Match.status == "FINISHED"
            )
        )
        .order_by(Match.utc_date.desc())
        .limit(n)
        .all()
    )
    return matches


def get_competition_name(db, competition_id):
    """Get competition name from ID."""
    if not competition_id:
        return "Unknown"
    comp = db.query(Competition).filter_by(id=competition_id).first()
    return comp.name if comp else "Unknown"


def print_team_audit(db, team_name):
    """Audit a single team."""
    team = get_team_by_name(db, team_name)
    if not team:
        print(f"ERROR: Team '{team_name}' not found!")
        return

    print(f"\n{'='*80}")
    print(f"TEAM AUDIT: {team.name} (ID: {team.id})")
    print(f"{'='*80}")

    print(f"\nFIFA Ranking: {team.fifa_ranking}")
    print(f"Squad Market Value: €{team.squad_market_value}M")
    print("\n--- Last 10 FINISHED Matches (used in features:")

    matches = get_last_n_matches(db, team.id, n=20)
    for i, match in enumerate(matches, 1):
        home_team = db.query(Team).filter_by(id=match.home_team_id).first()
        away_team = db.query(Team).filter_by(id=match.away_team_id).first()
        comp_name = get_competition_name(db, match.competition_id)
        score_str = f"{match.home_score or '-'}-{match.away_score or '-'}"
        print(f"\n{i}. {home_team.name if home_team else 'Unknown'} vs {away_team.name if away_team else 'Unknown'}")
        print(f"   Date: {match.utc_date}")
        print(f"   Competition: {comp_name}")
        print(f"   Score: {score_str}")
        print(f"   Status: {match.status}")
        print(f"   Winner: {match.winner}")


def main():
    db = SessionLocal()
    try:
        teams = ["Germany", "Brazil", "Qatar", "Ecuador"]

        print("="*80)
        print("WORLD CUP MATCH RESULT AUDIT")
        print("="*80)

        for team in teams:
            print_team_audit(db, team)

        print("\n" + "="*80)
        print("CHECKING FOR 2026 FIFA WORLD CUP MATCHES IN DATABASE:")
        print("="*80)

        wc_comp = db.query(Competition).filter(Competition.code == "WC").first()
        if wc_comp:
            print(f"\nFound World Cup Competition: {wc_comp.name} (ID: {wc_comp.id})")
            wc_matches = db.query(Match).filter(Match.competition_id == wc_comp.id).all()
            print(f"\nTotal WC Matches: {len(wc_matches)} total")
            for i, match in enumerate(wc_matches, 1):
                home_team = db.query(Team).filter_by(id=match.home_team_id).first()
                away_team = db.query(Team).filter_by(id=match.away_team_id).first()
                print(f"\n{i}. {home_team.name if home_team else 'Unknown'} vs {away_team.name if away_team else 'Unknown'}")
                print(f"   Date: {match.utc_date}")
                print(f"   Status: {match.status}")
                print(f"   Score: {match.home_score or '-'}-{match.away_score or '-'}")
        else:
            print("\nNo World Cup competition found in database.")

    finally:
        db.close()


if __name__ == "__main__":
    main()

