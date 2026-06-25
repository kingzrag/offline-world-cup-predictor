
#!/usr/bin/env python3
import os
import sys
from datetime import datetime, timezone
from sqlalchemy.orm import Session, joinedload

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


def get_last_n_matches_for_team(db, team_id, n=20):
    """Get last N matches for a team, ordered by date descending, with joined teams."""
    matches = (
        db.query(Match)
        .options(joinedload(Match.home_team), joinedload(Match.away_team), joinedload(Match.competition))
        .filter(
            (Match.home_team_id == team_id) | (Match.away_team_id == team_id),
            Match.status == "FINISHED"
        )
        .order_by(Match.utc_date.desc())
        .limit(n)
        .all()
    )
    return matches


def format_match_for_audit(match, team_id):
    """Format a single match for the audit report."""
    is_home = match.home_team_id == team_id
    opponent = match.away_team if is_home else match.home_team
    goals_for = match.home_score if is_home else match.away_score
    goals_against = match.away_score if is_home else match.home_score
    comp_name = match.competition.name if match.competition else "Unknown"
    result = ""
    if match.winner == "HOME_TEAM":
        result = "W" if is_home else "L"
    elif match.winner == "AWAY_TEAM":
        result = "L" if is_home else "W"
    else:
        result = "D"

    return {
        "date": match.utc_date,
        "opponent": opponent.name if opponent else "Unknown",
        "competition": comp_name,
        "score": f"{goals_for}-{goals_against}",
        "result": result,
        "is_home": is_home
    }


def print_team_audit_section(db, team_name):
    """Audit a single team's matches."""
    team = get_team_by_name(db, team_name)
    if not team:
        print(f"\n❌ Team '{team_name}' NOT FOUND in database!")
        return

    print(f"\n{'='*100}")
    print(f"📊 TEAM AUDIT: {team.name.upper()}")
    print(f"{'='*100}")
    print(f"  • FIFA Ranking: {team.fifa_ranking}")
    print(f"  • Squad Market Value: €{team.squad_market_value}M")
    print(f"  • Team ID: {team.id}")

    # Get matches for features
    matches_last20 = get_last_n_matches_for_team(db, team.id, n=20)

    print(f"\n--- LAST 10 MATCHES USED IN: form_diff, gs_diff, gc_diff ---")
    for i, match in enumerate(matches_last20[:10], 1):
        fmt = format_match_for_audit(match, team.id)
        print(f"\n  {i}. {fmt['date']} - {team.name} {fmt['score']} {fmt['opponent']} ({fmt['result']})")
        print(f"     Competition: {fmt['competition']}")

    print(f"\n--- LAST 20 MATCHES USED IN: attack_rating, defence_rating, clean_sheet_rate, btts_rate ---")
    for i, match in enumerate(matches_last20, 1):
        fmt = format_match_for_audit(match, team.id)
        # Indicate weighting: idx <5 (3x), 5-10 (2x), 10+ (1x)
        weight = "3x" if i <=5 else "2x" if i<=10 else "1x"
        print(f"  {i:2d}. [{weight}] {fmt['date']} - {team.name} {fmt['score']} {fmt['opponent']} ({fmt['result']})")


def print_wc_2026_matches(db):
    """Check if 2026 FIFA World Cup matches are present and used."""
    print(f"\n{'='*100}")
    print("🌍 CHECKING 2026 FIFA WORLD CUP MATCHES IN DATABASE")
    print(f"{'='*100}")

    wc_comp = db.query(Competition).filter(Competition.code == "WC").first()
    if not wc_comp:
        print("\n❌ NO World Cup competition (code: WC) found in database!")
        return

    print(f"\n✅ Found World Cup Competition: {wc_comp.name} (ID: {wc_comp.id})")

    all_wc_matches = (
        db.query(Match)
        .options(joinedload(Match.home_team), joinedload(Match.away_team))
        .filter(Match.competition_id == wc_comp.id)
        .order_by(Match.utc_date)
        .all()
    )

    print(f"\n  Total WC matches in DB: {len(all_wc_matches)}")

    wc_2026_matches = [m for m in all_wc_matches if m.utc_date and m.utc_date.year == 2026]
    print(f"  2026 WC matches in DB: {len(wc_2026_matches)}")

    if len(wc_2026_matches) >0:
        print(f"\n  --- 2026 WC Matches ---")
        for m in wc_2026_matches:
            home = m.home_team.name if m.home_team else "?"
            away = m.away_team.name if m.away_team else "?"
            print(f"    • {m.utc_date}: {home} vs {away} - Status: {m.status} - Score: {m.home_score}-{m.away_score}")

    # Check if any 2026 WC matches are in FINISHED status
    finished_wc_2026 = [m for m in wc_2026_matches if m.status == "FINISHED"]
    print(f"\n  FINISHED 2026 WC matches in DB: {len(finished_wc_2026)}")
    if len(finished_wc_2026) >0:
        print("    These matches would be included in feature calculations if their date is before match_date.")


def explain_prediction_probabilities():
    """Explain why Germany vs Ecuador and Scotland vs Brazil had those probabilities."""
    print(f"\n{'='*100}")
    print("📈 EXPLANATION OF PREDICTIONS (from previous audit)")
    print(f"{'='*100}")
    print("""
1. GERMANY vs ECUADOR:
   - Key factors from feature vector:
     • elo_diff: +123 (Germany has much higher Elo)
     • fifa_diff: +9 (Germany better FIFA rank)
     • form_diff: +1.8 (Germany much better recent form)
     • gs_diff: +3.0 (Germany way more goals scored lately)
     • h2h_factor: 1.0 (Germany won all recent H2H)
     • available_squad_diff: +211.45M€ (Germany's squad much more valuable)
   → Strongly favored Germany

2. SCOTLAND vs BRAZIL:
   - Key factors from feature vector:
     • elo_diff: -213 (Brazil way higher Elo)
     • fifa_diff: -30 (Brazil way better FIFA rank)
     • form_diff: -0.8 (Brazil better recent form)
     • gs_diff: -1.8 (Brazil scores way more)
     • available_squad_diff: -1015.33M€ (Brazil's squad vastly more valuable)
   → Strongly favored Brazil
""")


def main():
    db = SessionLocal()
    try:
        teams = ["Germany", "Brazil", "Qatar", "Ecuador"]

        print("="*100)
        print(" WORLD CUP PREDICTION FEATURE AUDIT REPORT 2026 ")
        print("="*100)

        # Audit each team
        for team_name in teams:
            print_team_audit_section(db, team_name)

        # Check 2026 WC matches
        print_wc_2026_matches(db)

        # Explain probabilities
        explain_prediction_probabilities()

    finally:
        db.close()


if __name__ == "__main__":
    main()

