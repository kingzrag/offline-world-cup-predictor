
#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from utils.config import settings
from models import (
    Match,
    Team,
    Competition
)
from services.collection_service import CollectionService
from collectors.sofascore import SofaScoreCollector
from datetime import datetime, timezone
import json

def setup_sample_data(db):
    print("Setting up sample data...")
    # Create competition
    competition = db.query(Competition).filter_by(code="WC").first()
    if not competition:
        competition = Competition(
            name="World Cup",
            code="WC",
            area="International"
        )
        db.add(competition)
        db.commit()
        db.refresh(competition)

    # Create teams
    home_team = db.query(Team).filter_by(name="Argentina").first()
    if not home_team:
        home_team = Team(name="Argentina", short_name="ARG")
        db.add(home_team)
    
    away_team = db.query(Team).filter_by(name="France").first()
    if not away_team:
        away_team = Team(name="France", short_name="FRA")
        db.add(away_team)
    
    db.commit()
    db.refresh(home_team)
    db.refresh(away_team)

    # Create match
    match = db.query(Match).filter_by(api_id="sample_match_123").first()
    if not match:
        match = Match(
            api_id="sample_match_123",
            competition_id=competition.id,
            home_team_id=home_team.id,
            away_team_id=away_team.id,
            utc_date=datetime.now(timezone.utc).replace(tzinfo=None),
            status="IN_PLAY"
        )
        db.add(match)
        db.commit()
        db.refresh(match)

    print(f"Sample data ready! Match ID: {match.id}")
    return match

def main():
    print("Testing SofaScore storage pipeline with sample data...")
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Set up sample data
        match = setup_sample_data(db)

        # Sample SofaScore data
        print("\nUsing sample SofaScore data...")
        sample_stats = {
            "statistics": [
                {
                    "period": "ALL",
                    "groups": [
                        {
                            "groupName": "Ball possession",
                            "statisticsItems": [
                                {"name": "Ball possession", "home": "58", "away": "42"}
                            ]
                        },
                        {
                            "groupName": "Shots",
                            "statisticsItems": [
                                {"name": "Total shots", "home": "15", "away": "10"},
                                {"name": "Shots on target", "home": "8", "away": "4"}
                            ]
                        },
                        {
                            "groupName": "Expected",
                            "statisticsItems": [
                                {"name": "Expected goals (xG)", "home": "1.8", "away": "0.7"}
                            ]
                        },
                        {
                            "groupName": "Goals",
                            "statisticsItems": [
                                {"name": "Corner kicks", "home": "6", "away": "3"}
                            ]
                        },
                        {
                            "groupName": "Fouls",
                            "statisticsItems": [
                                {"name": "Fouls", "home": "12", "away": "15"},
                                {"name": "Offsides", "home": "3", "away": "1"}
                            ]
                        }
                    ]
                }
            ]
        }

        sample_lineups = {
            "home": {
                "formation": "4-3-3",
                "players": [
                    {
                        "player": {"name": "Emiliano Martínez", "id": 1001},
                        "substitute": False,
                        "statistics": {"rating": 7.2}
                    },
                    {
                        "player": {"name": "Lionel Messi", "id": 1002},
                        "substitute": False,
                        "statistics": {"rating": 8.5}
                    }
                ]
            },
            "away": {
                "formation": "4-2-3-1",
                "players": [
                    {
                        "player": {"name": "Hugo Lloris", "id": 2001},
                        "substitute": False,
                        "statistics": {"rating": 7.0}
                    },
                    {
                        "player": {"name": "Kylian Mbappé", "id": 2002},
                        "substitute": False,
                        "statistics": {"rating": 8.8}
                    }
                ]
            }
        }

        sample_events = {
        "incidents": [
            {
                "id": 12345,
                "time": 23,
                "isHome": True,
                "incidentType": "goal",
                "playerName": "Lionel Messi",
                "reason": "Left-footed shot from inside the box"
            },
            {
                "id": 12346,
                "time": 52,
                "isHome": False,
                "incidentType": "card",
                "incidentClass": "red",
                "playerName": "Dayot Upamecano",
                "reason": "Rough tackle"
            },
            {
                "id": 12347,
                "time": 81,
                "isHome": False,
                "incidentType": "goal",
                "playerName": "Kylian Mbappé",
                "reason": "Penalty"
            }
        ]
    }

        # Use collector to parse data
        collector = SofaScoreCollector()
        parsed_stats = collector.parse_match_statistics(sample_stats)
        parsed_lineups = collector.parse_match_lineups(sample_lineups)
        parsed_events = collector.parse_match_events(sample_events)

        # Store the data
        service = CollectionService()
        print("\nStoring statistics...")
        import asyncio
        asyncio.run(service.store_match_statistics(db, match, parsed_stats))
        
        print("\nStoring lineups...")
        asyncio.run(service.store_match_lineups(db, match, parsed_lineups))
        
        print("\nStoring events...")
        asyncio.run(service.store_match_events(db, match, parsed_events))
        
        db.commit()

        print("\n✅ Storage test passed!")
        print("\nNow let's check the data in the database:")
        
        # Verify the data is there
        from models import MatchStatistic, MatchEvent, MatchLineup, PlayerMatchPerformance
        stats = db.query(MatchStatistic).filter_by(match_id=match.id).first()
        if stats:
            print("\nMatch Statistics:")
            print(f"  Home xG: {stats.home_expected_goals}")
            print(f"  Away xG: {stats.away_expected_goals}")

        events = db.query(MatchEvent).filter_by(match_id=match.id).all()
        print(f"\nMatch Events found: {len(events)}")
        for e in events:
            print(f"  - {e.type}: {e.player_name} ({e.minute}')")

        lineups = db.query(MatchLineup).filter_by(match_id=match.id).all()
        print(f"\nMatch Lineups found: {len(lineups)}")

        perfs = db.query(PlayerMatchPerformance).filter_by(match_id=match.id).all()
        print(f"\nPlayer Performances found: {len(perfs)}")
        for p in perfs:
            print(f"  - {p.player_name}: {p.sofa_score_rating}")

    except Exception as e:
        print(f"\nError: {type(e).__name__}: {e}")
        import traceback
        print(traceback.format_exc())
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
