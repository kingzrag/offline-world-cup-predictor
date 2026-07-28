import asyncio
import time
from datetime import datetime, timedelta

import schedule
from sqlalchemy.orm import Session

from config.competitions import get_supported_codes
from database.connection import SessionLocal
from models import Match, Team
from services.collection_service import CollectionService
from services.prediction_service import PredictionService
from services.prediction_tracking_service import prediction_tracking_service
from services.transfermarkt_service import TransfermarktService
from utils.logger import logger


def run_full_provider_pipeline():
    logger.info("Starting scheduled full provider pipeline for all supported competitions")
    db = SessionLocal()
    try:
        service = CollectionService()
        pred_service = PredictionService()
        summary = {}

        # 1. Dynamically ingest all supported competitions
        supported_codes = get_supported_codes()
        for competition_code in supported_codes:
            try:
                summary[competition_code] = asyncio.run(
                    service.ingest_football_data(db, competition_code)
                )
                db.expire_all()
            except Exception as ing_err:
                logger.warning(f"Ingestion failed for competition {competition_code}: {ing_err}")
                summary[competition_code] = {"status": "failed", "error": str(ing_err)}
        
        # 2. Generate ML predictions for all upcoming fixtures across all competitions
        try:
            predictions = pred_service.generate_predictions_for_fixtures(db)
            summary["predictions_generated"] = len(predictions)
        except Exception as pred_err:
            logger.warning(f"Prediction generation pipeline failed: {pred_err}")
            summary["predictions_generated"] = f"failed: {pred_err}"

        # 3. Ingest live SofaScore data
        try:
            summary["SofaScore"] = asyncio.run(service.ingest_sofascore_live(db))
        except Exception as sofascore_err:
            logger.warning(f"SofaScore scheduled sync failed: {sofascore_err}")
            summary["SofaScore"] = {"status": "failed", "error": str(sofascore_err)}

        # 4. Automatically evaluate accuracy for finished matches
        try:
            evaluated_count = prediction_tracking_service.evaluate_finished_matches(db)
            summary["evaluated_matches"] = evaluated_count
        except Exception as eval_err:
            logger.warning(f"Finished match evaluation failed: {eval_err}")
            summary["evaluated_matches"] = f"failed: {eval_err}"

        logger.info(f"Scheduled full provider pipeline completed: {summary}")
    except Exception as e:
        logger.error(f"Error during scheduled full provider pipeline: {e}")
    finally:
        db.close()


def refresh_upcoming_match_teams():
    logger.info("Starting upcoming match teams refresh")
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        cutoff = now + timedelta(hours=48)
        upcoming_matches = (
            db.query(Match)
            .filter(Match.utc_date >= now, Match.utc_date <= cutoff)
            .all()
        )

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
            injuries, _ = tm_service._scrape_team_data(team.transfermarkt_url)
            _, suspensions = tm_service._scrape_team_data(team.transfermarkt_url)

            from models import NationalTeamPlayer, Injury, Suspension

            player_market_values = {
                p.player_name: p.market_value
                for p in db.query(NationalTeamPlayer).filter_by(team_id=team.id).all()
            }

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
                    player_market_value=player_mv,
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
                    player_market_value=player_mv,
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
    schedule.every().day.at("03:00").do(run_full_provider_pipeline)
    schedule.every(12).hours.do(run_full_provider_pipeline)
    schedule.every().hour.do(refresh_upcoming_match_teams)
    schedule.every(2).minutes.do(ingest_sofascore_live_data)

    logger.info("Scheduler started")
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    run_scheduler()
