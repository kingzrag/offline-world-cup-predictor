"""
run_ingest_and_predict.py
─────────────────────────
One-shot runner: ingests fixtures for every supported competition, then
generates predictions for all upcoming matches.

Usage:
    python3 run_ingest_and_predict.py
"""

import asyncio
import sys
import time
from datetime import datetime

from database.connection import SessionLocal
from services.collection_service import CollectionService
from services.prediction_service import PredictionService
from utils.logger import logger

# ── Same registry as scheduler.py ────────────────────────────────────────────
COMPETITIONS = [
    ("PL",  "Premier League"),
    ("PD",  "La Liga"),
    ("SA",  "Serie A"),
    ("BL1", "Bundesliga"),
    ("FL1", "Ligue 1"),
    ("CL",  "Champions League"),
    ("EL",  "Europa League"),
    ("WC",  "FIFA World Cup"),
    ("EC",  "UEFA Euro"),
    ("UNL", "UEFA Nations League"),
    ("CA",  "Copa América"),
    ("WCQ", "WC Qualifiers"),
]

SEPARATOR = "─" * 72

def main():
    print(f"\n{'═'*72}")
    print(f"  OFFLINE · Full Ingest + Predict Run")
    print(f"  Started : {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"{'═'*72}\n")

    db = SessionLocal()
    collection = CollectionService()
    pred_service = PredictionService()

    ingest_results: dict = {}
    total_start = time.time()

    # ── 1. Ingest all competitions ────────────────────────────────────────────
    print(f"{'STEP 1 — FIXTURE INGESTION':^72}")
    print(SEPARATOR)

    for code, label in COMPETITIONS:
        print(f"  [{code:<4}]  {label:<30}", end="", flush=True)
        t0 = time.time()
        try:
            summary = asyncio.run(collection.ingest_football_data(db, code))
            db.expire_all()
            elapsed = time.time() - t0
            ingest_results[code] = summary
            matches = summary.get("matches", summary.get("fixtures", "—"))
            teams   = summary.get("teams", "—")
            print(f"  ✓  matches={matches}  teams={teams}  ({elapsed:.1f}s)")
        except Exception as exc:
            elapsed = time.time() - t0
            ingest_results[code] = {"error": str(exc)}
            print(f"  ✗  {exc}  ({elapsed:.1f}s)")

    print(f"\n{SEPARATOR}\n")

    # ── 2. Generate predictions ───────────────────────────────────────────────
    print(f"{'STEP 2 — PREDICTION GENERATION':^72}")
    print(SEPARATOR)
    print("  Running FootballPredictor across all upcoming SCHEDULED/TIMED matches…\n")

    try:
        t0 = time.time()
        predictions = pred_service.generate_predictions_for_fixtures(db)
        elapsed = time.time() - t0
        print(f"  ✓  {len(predictions)} predictions generated  ({elapsed:.1f}s)")

        if predictions:
            print(f"\n  {'Match':<40} {'Outcome':<12} {'H%':>5} {'D%':>5} {'A%':>5}")
            print(f"  {'-'*40} {'-'*12} {'-'*5} {'-'*5} {'-'*5}")
            shown = 0
            for pred in predictions[:20]:
                try:
                    match = pred.match
                    home  = match.home_team.name[:18] if match.home_team else "?"
                    away  = match.away_team.name[:18] if match.away_team else "?"
                    label = f"{home} v {away}"
                    hp = f"{pred.home_probability*100:.1f}" if pred.home_probability is not None else "—"
                    dp = f"{pred.draw_probability*100:.1f}" if pred.draw_probability is not None else "—"
                    ap = f"{pred.away_probability*100:.1f}" if pred.away_probability is not None else "—"
                    print(f"  {label:<40} {pred.predicted_outcome:<12} {hp:>5} {dp:>5} {ap:>5}")
                    shown += 1
                except Exception:
                    pass
            if len(predictions) > 20:
                print(f"  … and {len(predictions) - shown} more")
    except Exception as exc:
        print(f"  ✗  Prediction pipeline failed: {exc}")
        import traceback
        traceback.print_exc()

    db.close()

    total_elapsed = time.time() - total_start
    print(f"\n{SEPARATOR}")
    print(f"  Completed in {total_elapsed:.1f}s")
    print(f"  Finished : {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"{'═'*72}\n")


if __name__ == "__main__":
    main()
