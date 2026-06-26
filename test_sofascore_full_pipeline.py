
#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from utils.config import settings
from services.collection_service import CollectionService
from collectors.sofascore import SofaScoreCollector
import asyncio
import json

async def main():
    print("=== Testing SofaScore Collector Pipeline ===")

    # Setup database connection
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Initialize services
        collection_service = CollectionService()
        sofa_collector = SofaScoreCollector()

        # Step 1: Fetch live matches
        print("\n1. Fetching live matches...")
        live_matches = sofa_collector.get_live_matches()
        if live_matches and live_matches.get("events"):
            print(f"   Found {len(live_matches['events'])} live matches!")
            # Print first match details
            first_match = live_matches["events"][0]
            print(f"   First match: {first_match.get('homeTeam', {}).get('name')} vs {first_match.get('awayTeam', {}).get('name')}")
            
            # Step 2: Fetch details for first match (if we have matches in DB)
            # Since we might not have real matches in DB, let's use sample data to test storage
            print("\n2. Testing storage pipeline with sample data...")
            from sample_sofascore_data import (
                SAMPLE_STATISTICS,
                SAMPLE_LINEUPS,
                SAMPLE_INCIDENTS
            )
            
            # Create a dummy match for testing (use existing if possible)
            from models import Match, Team, Competition
            test_competition = db.query(Competition).filter(Competition.code.ilike("WC")).first()
            if not test_competition:
                test_competition = Competition(name="Test Competition", code="WC", area="Test")
                db.add(test_competition)
                db.commit()
                db.refresh(test_competition)
            
            test_home_team = db.query(Team).filter(Team.name.ilike("Argentina")).first()
            if not test_home_team:
                test_home_team = Team(name="Argentina", short_name="ARG")
                db.add(test_home_team)
                
            test_away_team = db.query(Team).filter(Team.name.ilike("France")).first()
            if not test_away_team:
                test_away_team = Team(name="France", short_name="FRA")
                db.add(test_away_team)
                
            db.commit()
            db.refresh(test_home_team)
            db.refresh(test_away_team)
            
            test_match = db.query(Match).filter(
                Match.home_team_id == test_home_team.id,
                Match.away_team_id == test_away_team.id
            ).first()
            
            if not test_match:
                from datetime import datetime, timezone
                test_match = Match(
                    api_id="TEST_MATCH_001",
                    competition_id=test_competition.id,
                    home_team_id=test_home_team.id,
                    away_team_id=test_away_team.id,
                    utc_date=datetime.now(timezone.utc).replace(tzinfo=None),
                    status="IN_PLAY"
                )
                db.add(test_match)
                db.commit()
                db.refresh(test_match)
            
            print(f"   Using test match ID: {test_match.id}")
            
            # Parse sample data
            print("\n3. Parsing sample data...")
            parsed_stats = sofa_collector.parse_match_statistics(SAMPLE_STATISTICS)
            parsed_lineups = sofa_collector.parse_match_lineups(SAMPLE_LINEUPS)
            parsed_events = sofa_collector.parse_match_events(SAMPLE_INCIDENTS)
            
            # Store sample data
            print("\n4. Storing sample data...")
            await collection_service.store_match_statistics(db, test_match, parsed_stats)
            await collection_service.store_match_lineups(db, test_match, parsed_lineups)
            await collection_service.store_match_events(db, test_match, parsed_events)
            
            db.commit()
            print("   Sample data stored successfully!")
            
            # Step 3: Run audit script
            print("\n5. Running database audit...")
            # Reuse the audit script logic
            from models import MatchStatistic, MatchEvent, MatchLineup, PlayerMatchPerformance, SuspensionHistory
            print("\n--- Match Statistics ---")
            stats = db.query(MatchStatistic).all()
            print(f"Total rows: {len(stats)}")
            for stat in stats:
                print(f"  ID: {stat.id}, Match ID: {stat.match_id}, Home xG: {stat.home_expected_goals}")
                
            print("\n--- Match Events ---")
            events = db.query(MatchEvent).all()
            print(f"Total rows: {len(events)}")
            for event in events:
                print(f"  ID: {event.id}, Type: {event.type}, Player: {event.player_name}")
                
            print("\n--- Match Lineups ---")
            lineups = db.query(MatchLineup).all()
            print(f"Total rows: {len(lineups)}")
            for lineup in lineups:
                print(f"  ID: {lineup.id}, Formation: {lineup.formation}")
                
            print("\n--- Player Performances ---")
            perfs = db.query(PlayerMatchPerformance).all()
            print(f"Total rows: {len(perfs)}")
            for perf in perfs:
                print(f"  ID: {perf.id}, Player: {perf.player_name}, Rating: {perf.sofa_score_rating}")
                
            print("\n--- Suspension History ---")
            susp_hist = db.query(SuspensionHistory).all()
            print(f"Total rows: {len(susp_hist)}")
            for h in susp_hist:
                print(f"  ID: {h.id}, Old Status: {h.old_status}, New Status: {h.new_status}")
                
        else:
            print("   No live matches found, or API request failed!")
            print("\nTesting sample data storage instead...")
            
            # Test with sample data
            from sample_sofascore_data import (
                SAMPLE_STATISTICS,
                SAMPLE_LINEUPS,
                SAMPLE_INCIDENTS
            )
            
            # Create dummy match
            from models import Match, Team, Competition
            test_competition = db.query(Competition).filter(Competition.code.ilike("WC")).first()
            if not test_competition:
                test_competition = Competition(name="Test Competition", code="WC", area="Test")
                db.add(test_competition)
                db.commit()
                db.refresh(test_competition)
            
            test_home_team = db.query(Team).filter(Team.name.ilike("Argentina")).first()
            if not test_home_team:
                test_home_team = Team(name="Argentina", short_name="ARG")
                db.add(test_home_team)
                
            test_away_team = db.query(Team).filter(Team.name.ilike("France")).first()
            if not test_away_team:
                test_away_team = Team(name="France", short_name="FRA")
                db.add(test_away_team)
                
            db.commit()
            db.refresh(test_home_team)
            db.refresh(test_away_team)
            
            test_match = db.query(Match).filter(
                Match.home_team_id == test_home_team.id,
                Match.away_team_id == test_away_team.id
            ).first()
            
            if not test_match:
                from datetime import datetime, timezone
                test_match = Match(
                    api_id="TEST_MATCH_001",
                    competition_id=test_competition.id,
                    home_team_id=test_home_team.id,
                    away_team_id=test_away_team.id,
                    utc_date=datetime.now(timezone.utc).replace(tzinfo=None),
                    status="IN_PLAY"
                )
                db.add(test_match)
                db.commit()
                db.refresh(test_match)
            
            print(f"Using test match ID: {test_match.id}")
            
            parsed_stats = sofa_collector.parse_match_statistics(SAMPLE_STATISTICS)
            parsed_lineups = sofa_collector.parse_match_lineups(SAMPLE_LINEUPS)
            parsed_events = sofa_collector.parse_match_events(SAMPLE_INCIDENTS)
            
            await collection_service.store_match_statistics(db, test_match, parsed_stats)
            await collection_service.store_match_lineups(db, test_match, parsed_lineups)
            await collection_service.store_match_events(db, test_match, parsed_events)
            
            db.commit()
            
        print("\n=== SofaScore Collector Pipeline Test Complete ===")
        
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        import traceback
        print(traceback.format_exc())
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
