import sys
import os

# Add root folder to sys.path
sys.path.append("/Users/anuragsaikia/prediction")

from database.connection import SessionLocal
from models import Match, Prediction, Competition
from services.model_service import model_service

def populate_all_wc_predictions():
    db = SessionLocal()
    try:
        # Initialize models
        if not model_service._initialized:
            model_service.load_models()

        comp = db.query(Competition).filter_by(code="WC").first()
        if not comp:
            print("WC Competition not found.")
            return

        matches = db.query(Match).filter(Match.competition_id == comp.id).all()
        print(f"Found {len(matches)} WC matches in database.")

        count = 0

        for match in matches:
            # Check if prediction already exists (we overwrite v1.0 predictions or populate if missing)
            existing = db.query(Prediction).filter_by(match_id=match.id).first()
            
            try:
                # Predict 1x2 using predict_1x2 (no FINISHED check)
                res = model_service.predict_1x2(
                    db=db,
                    home_team_id=match.home_team_id,
                    away_team_id=match.away_team_id,
                    match_date=match.utc_date,
                    competition_code="WC"
                )

                pred_winner_id = None
                if res["predicted_outcome"] == "HOME_WIN":
                    pred_winner_id = match.home_team_id
                elif res["predicted_outcome"] == "AWAY_WIN":
                    pred_winner_id = match.away_team_id

                if not existing:
                    existing = Prediction(
                        match_id=match.id,
                        predicted_winner_id=pred_winner_id,
                        predicted_outcome=res["predicted_outcome"],
                        home_probability=res["home_win_probability"],
                        away_probability=res["away_win_probability"],
                        draw_probability=res["draw_probability"],
                        model_version=res["model_version"]
                    )
                    db.add(existing)
                else:
                    existing.predicted_winner_id = pred_winner_id
                    existing.predicted_outcome = res["predicted_outcome"]
                    existing.home_probability = res["home_win_probability"]
                    existing.away_probability = res["away_win_probability"]
                    existing.draw_probability = res["draw_probability"]
                    existing.model_version = res["model_version"]

                count += 1
            except Exception as e:
                print(f"Error predicting match {match.id}: {e}")
                continue

        db.commit()
        print(f"Successfully generated/updated predictions for {count} matches.")

    finally:
        db.close()

if __name__ == "__main__":
    populate_all_wc_predictions()
