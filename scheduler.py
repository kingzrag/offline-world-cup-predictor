
import asyncio
import schedule
import time
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database.connection import SessionLocal
from models import Match, Team
from services.transfermarkt_service import TransfermarktService
from services.collection_service import CollectionService
from utils.logger import logger

def refresh_all_injuries_suspensions():
    logger.info("Starting full injury/suspension refresh")
    db = SessionLocal()
    try:
        service = CollectionService()
        # We need to run async functions here
        asyncio.run(service.ingest_injuries(db, "WC"))
        asyncio.run(service.ingest_suspensions(db, "WC"))
        logger.info("Full injury/suspension refresh completed")
    except Exception as e:
        logger.error(f"Error during injury/suspension refresh: {e}")
    finally:
        db.close()

def refresh_upcoming_match_teams():
    logger.info("Starting upcoming match teams refresh")
    db = SessionLocal()
    try:
        # Find all upcoming matches (next 48 hours)
        now = datetime.utcnow()
        cutoff = now + timedelta(hours=48)
        upcoming_matches = db.query(Match).filter(
            Match.utc_date >= now, Match.utc_date <= cutoff
        ).all()
        
        team_ids = set()
        for m in upcoming_matches:
            if m.home_team_id:
                team_ids.add(m.home_team_id)
            if m.away_team_id:
                team_ids.add(m.away_team_id)
        
        if not team_ids:
            logger.info("No upcoming matches found")
            return
        
        tm_service = TransfermarktService()
        for team_id in team_ids:
            team = db.query(Team).filter_by(id=team_id).first()
            if not team or not team.transfermarkt_url:
                continue
                
            logger.info(f"Refreshing team: {team.name}")
            
            # Refresh injuries and suspensions for this team specifically
            injuries, _ = tm_service._scrape_team_data(team.transfermarkt_url)
            _, suspensions = tm_service._scrape_team_data(team.transfermarkt_url)
            
            # Build player market value map
            from models import NationalTeamPlayer
            player_market_values = {
                p.player_name: p.market_value
                for p in db.query(NationalTeamPlayer).filter_by(team_id=team.id).all()
            }
            
            # Update injuries
            from models import Injury, Suspension
            db.query(Injury).filter_by(team_id=team.id).delete()
            for inj in injuries:
                player_name = inj["player_name"]
                player_mv = player_market_values.get(player_name, 0.0)
                injury_record = Injury(
                    player_name=player_name,
                    team_id=team.id,
                    team_name=team.name,
                    injury_type=inj["injury_type"],
                    expected_return_date=inj["expected_return_date"],
                    days_out=inj["days_out"],
                    player_market_value=player_mv
                )
                db.add(injury_record)
                
            db.query(Suspension).filter_by(team_id=team.id).delete()
            for susp in suspensions:
                player_name = susp["player_name"]
                player_mv = player_market_values.get(player_name, 0.0)
                suspension_record = Suspension(
                    player_name=player_name,
                    team_id=team.id,
                    team_name=team.name,
                    suspension_reason=susp["suspension_reason"],
                    matches_remaining=susp["matches_remaining"],
                    player_market_value=player_mv
                )
                db.add(suspension_record)
                
        db.commit()
        logger.info("Upcoming match teams refresh completed")
    except Exception as e:
        db.rollback()
        logger.error(f"Error during upcoming match teams refresh: {e}")
    finally:
        db.close()

def ingest_sofascore_live_data():
    logger.info("Starting SofaScore live data ingestion")
    db = SessionLocal()
    try:
        service = CollectionService()
        asyncio.run(service.ingest_sofascore_live(db))
        logger.info("SofaScore live data ingestion completed")
    except Exception as e:
        logger.error(f"Error during SofaScore live ingestion: {e}")
    finally:
        db.close()

def run_scheduler():
    # Daily refresh at 03:00 UTC
    schedule.every().day.at("03:00").do(refresh_all_injuries_suspensions)
    
    # Refresh every 6 hours
    schedule.every(6).hours.do(refresh_all_injuries_suspensions)
    
    # Additional checks for upcoming matches every hour
    schedule.every().hour.do(refresh_upcoming_match_teams)
    
    # SofaScore live ingestion every 5 minutes
    schedule.every(5).minutes.do(ingest_sofascore_live_data)
    
    logger.info("Scheduler started")
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    run_scheduler()
