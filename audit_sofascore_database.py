
#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from utils.config import settings
from models import (
    MatchStatistic,
    MatchEvent,
    MatchLineup,
    PlayerMatchPerformance,
    SuspensionHistory,
    Match
)
import json

def main():
    print("=" * 100)
    print("SOFASCORE INGESTION DATABASE AUDIT")
    print("=" * 100)

    # Connect to the database
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # 1. Check match_statistics
        print("\n" + "=" * 100)
        print("1. MATCH_STATISTICS TABLE")
        print("=" * 100)
        stats = db.query(MatchStatistic).all()
        print(f"\nTotal rows in match_statistics: {len(stats)}")
        if stats:
            print("\nSample rows:")
            for stat in stats[:3]:
                print(f"\n  ID: {stat.id}")
                print(f"  Match ID: {stat.match_id}")
                print(f"  Home Possession: {stat.home_possession}%")
                print(f"  Away Possession: {stat.away_possession}%")
                print(f"  Home Shots: {stat.home_shots}")
                print(f"  Away Shots: {stat.away_shots}")
                print(f"  Home xG: {stat.home_expected_goals}")
                print(f"  Away xG: {stat.away_expected_goals}")
        else:
            print("\nNo data found in match_statistics!")

        # 2. Check match_events
        print("\n" + "=" * 100)
        print("2. MATCH_EVENTS TABLE")
        print("=" * 100)
        events = db.query(MatchEvent).order_by(MatchEvent.minute).all()
        print(f"\nTotal rows in match_events: {len(events)}")
        if events:
            print("\nSample rows:")
            for event in events[:5]:
                print(f"\n  ID: {event.id}")
                print(f"  Match ID: {event.match_id}")
                print(f"  Type: {event.type}")
                print(f"  Minute: {event.minute}")
                print(f"  Is Home: {event.is_home if hasattr(event, 'is_home') else 'N/A'}")
                print(f"  Player: {event.player_name}")
                print(f"  Description: {event.description}")
                print(f"  SofaScore ID: {event.sofa_score_id}")
        else:
            print("\nNo data found in match_events!")

        # 3. Check match_lineups
        print("\n" + "=" * 100)
        print("3. MATCH_LINEUPS TABLE")
        print("=" * 100)
        lineups = db.query(MatchLineup).all()
        print(f"\nTotal rows in match_lineups: {len(lineups)}")
        if lineups:
            print("\nSample rows:")
            for lineup in lineups[:4]:
                print(f"\n  ID: {lineup.id}")
                print(f"  Match ID: {lineup.match_id}")
                print(f"  Team ID: {lineup.team_id}")
                print(f"  Formation: {lineup.formation}")
                print(f"  Starting XI: {lineup.starting_xi[:100]}..." if lineup.starting_xi else "  Starting XI: None")
        else:
            print("\nNo data found in match_lineups!")

        # 4. Check player_match_performances
        print("\n" + "=" * 100)
        print("4. PLAYER_MATCH_PERFORMANCES TABLE")
        print("=" * 100)
        performances = db.query(PlayerMatchPerformance).order_by(PlayerMatchPerformance.sofa_score_rating.desc()).all()
        print(f"\nTotal rows in player_match_performances: {len(performances)}")
        if performances:
            print("\nSample rows:")
            for perf in performances[:5]:
                print(f"\n  ID: {perf.id}")
                print(f"  Match ID: {perf.match_id}")
                print(f"  Team ID: {perf.team_id}")
                print(f"  Player Name: {perf.player_name}")
                print(f"  Position: {perf.position}")
                print(f"  Is Starter: {bool(perf.is_starter)}")
                print(f"  SofaScore Rating: {perf.sofa_score_rating}")
        else:
            print("\nNo data found in player_match_performances!")

        # 5. Check suspension_history
        print("\n" + "=" * 100)
        print("5. SUSPENSION_HISTORY TABLE")
        print("=" * 100)
        history = db.query(SuspensionHistory).all()
        print(f"\nTotal rows in suspension_history: {len(history)}")
        if history:
            print("\nSample rows:")
            for h in history[:3]:
                print(f"\n  ID: {h.id}")
                print(f"  Suspension ID: {h.suspension_id}")
                print(f"  Old Status: {h.old_status}")
                print(f"  New Status: {h.new_status}")
                print(f"  Changed By: {h.changed_by}")
                print(f"  Reason: {h.reason}")
        else:
            print("\nNo data found in suspension_history!")

        # 6. Check matches for SofaScore ID
        print("\n" + "=" * 100)
        print("6. MATCHES WITH SOFASCORE ID")
        print("=" * 100)
        matches = db.query(Match).filter(Match.sofa_score_id.isnot(None)).all()
        print(f"\nTotal matches with SofaScore ID: {len(matches)}")
        if matches:
            print("\nSample matches:")
            for match in matches[:3]:
                print(f"\n  Match ID: {match.id}")
                print(f"  SofaScore ID: {match.sofa_score_id}")
                print(f"  Home Formation: {match.home_formation}")
                print(f"  Away Formation: {match.away_formation}")
                print(f"  Home Possession: {match.home_possession}%")
                print(f"  Away Possession: {match.away_possession}%")

    except Exception as e:
        print(f"\nError querying database: {type(e).__name__}: {e}")
        import traceback
        print(traceback.format_exc())
    finally:
        db.close()

    print("\n" + "=" * 100)
    print("AUDIT COMPLETE")
    print("=" * 100)

if __name__ == "__main__":
    main()
