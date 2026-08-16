import asyncio
import time
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from api.routes import injuries, matches, players, predictions, teams, tournament
from api.routes import predict as predict_router
from database.base import Base
from database.connection import engine
from services.model_service import model_service
from utils.logger import logger

# Automatically bootstrap schema: Alembic migrations first, then create_all fallback.
# Note: Alembic migrations disabled due to startup timeout issues. Using create_all fallback.
try:
    from database.migrate import verify_matches_schema

    logger.info("Skipping Alembic migrations - using create_all fallback")
    # run_migrations()
    # verify_matches_schema()

    logger.info("Initializing database schema tables creation (create_all fallback)...")
    Base.metadata.create_all(bind=engine)
    verify_matches_schema()
    logger.info("Database schema sync completed successfully.")
except Exception as err:
    logger.error(
        f"Critical: Database migration or schema sync failed: {err}", exc_info=True
    )

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(
    title="Football Prediction Platform",
    description="Production-grade sports predictions backend engine utilizing FastAPI and PostgreSQL.",
    version="1.0.0",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Enable CORS for standard web environments
# Allow production Vercel domain, all Vercel preview deployments, and localhost
import os

def get_allowed_origins():
    """Get allowed origins from environment or use defaults for development/production."""
    env_origins = os.getenv("ALLOWED_ORIGINS")
    if env_origins:
        return [origin.strip() for origin in env_origins.split(",")]
    
    # Default origins for development and production
    default_origins = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
        "https://offline-world-cup-predictor-f0uf6e116-kingrazgs-projects.vercel.app",
        "https://offline-world-cup-predictor-5e4g9xmid-kingzrags-projects.vercel.app",
        "https://offline-world-cup-predictor-4qw0p16ch-kingzrags-projects.vercel.app",
        "https://offline-world-cup-predictor-kingrazgs-projects.vercel.app",
        "https://offline-world-cup-predictor-kingzrags-projects.vercel.app",
        "https://offline-world-cup-predictor.vercel.app",
    ]
    
    # Add production/preview Vercel domain if specified via env vars
    for env_var in ["VERCEL_DOMAIN", "VERCEL_URL"]:
        v_url = os.getenv(env_var)
        if v_url:
            v_url = v_url.replace("https://", "").replace("http://", "").strip("/")
            default_origins.append(f"https://{v_url}")
            default_origins.append(f"https://www.{v_url}")
    
    return default_origins

ALLOWED_ORIGINS = get_allowed_origins()

# Regex to match all Vercel preview and project deployments (*.vercel.app)
ALLOWED_ORIGIN_REGEX = r"https://.*\.vercel\.app"

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=ALLOWED_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
    expose_headers=["Content-Length", "X-Request-ID"],
    max_age=600,  # Cache preflight requests for 10 minutes
)

# Enable GZip compression for all responses
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Request duration metrics + request log tracking middleware
@app.middleware("http")
async def log_requests_and_latency(request: Request, call_next):
    start_time = time.time()
    path = request.url.path
    method = request.method
    logger.info(f"Incoming Request: {method} {path}")

    try:
        response = await call_next(request)
        duration = time.time() - start_time
        logger.info(
            f"Response: {method} {path} - Status: {response.status_code} - Completed in {duration:.4f}s"
        )
        return response
    except Exception as exc:
        duration = time.time() - start_time
        logger.error(
            f"Request Failure: {method} {path} - Completed with exception in {duration:.4f}s - {str(exc)}"
        )
        raise exc


# Centralized error handler
@app.exception_handler(Exception)
def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        f"Unhandled Exception raised on {request.url.path}: {str(exc)}", exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "An internal system error occurred. Please contact administrator.",
            "details": str(exc),
        },
    )


# Basic health-check route
@app.get("/health")
@limiter.limit("100/minute")
def health_check(request: Request):
    return {
        "status": "healthy",
        "system": "football_prediction_platform_backend",
        "models_loaded": model_service.is_ready,
        "model_versions": model_service.model_versions,
        "timestamp": time.time(),
    }


@app.get("/debug/db-test")
@limiter.limit("10/minute")
def debug_db_test(request: Request):
    """Simple database test endpoint."""
    try:
        from database.connection import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        result = db.execute(text("SELECT 1")).scalar()
        db.close()
        return {
            "status": "success",
            "db_connection": result == 1,
            "message": "Database connection successful"
        }
    except Exception as e:
        logger.error(f"Database test failed: {e}", exc_info=True)
        return {
            "status": "error",
            "db_connection": False,
            "message": str(e)
        }


@app.get("/api/fixtures-test")
def fixtures_test(request: Request):
    """Simple test endpoint to verify routing works without rate limiting."""
    return {
        "status": "success",
        "message": "Routing works at main app level",
        "timestamp": time.time()
    }


@app.get("/debug/simple")
@limiter.limit("10/minute")
def debug_simple(request: Request):
    """Simple test endpoint without database."""
    return {
        "status": "success",
        "message": "Routing works",
        "timestamp": time.time()
    }


# Register primary API sub-routers
app.include_router(matches.router, prefix="/api/v1")
app.include_router(teams.router, prefix="/api/v1")
app.include_router(players.router, prefix="/api/v1")
app.include_router(injuries.router, prefix="/api/v1")
app.include_router(predictions.router, prefix="/api/v1")

# ── New ML prediction API (ModelService-backed) ───────────────────────────────
app.include_router(predict_router.router, prefix="/api")

# ── Tournament Progression Routing ──────────────────────────────────────────
app.include_router(tournament.router)

# ── Admin endpoints (match seeding, ELO recompute, DB stats) ───────────────
from api.routes.admin import router as admin_router

app.include_router(admin_router)

# ── Analytics endpoints (prediction tracking and metrics) ───────────────────
from api.routes.analytics import router as analytics_router

app.include_router(analytics_router)

# ── AI Chat endpoints (OpenRouter integration) ───────────────────────────────
from api.routes.ai import router as ai_router

app.include_router(ai_router)


async def run_live_match_sync():
    """
    Poll football-data.org and API-Football every 30 seconds
    so live scores stay current during matches.
    """
    from services.live_sync_state import (
        mark_task_initialized,
        record_sync_complete,
        record_sync_error,
        record_sync_start,
    )

    mark_task_initialized()
    logger.info("Live match sync background task initialized (30s interval).")
    await asyncio.sleep(5)  # let startup finish before first sync

    while True:
        started_at = datetime.now(timezone.utc)
        record_sync_start()
        logger.info("Live sync started")

        try:
            from database.connection import SessionLocal
            from services.collection_service import CollectionService

            db = SessionLocal()
            try:
                service = CollectionService()
                # First, ingest from football-data.org as before
                # Sync all active domestic league competitions for live score/status updates
                LIVE_SYNC_COMPETITIONS = ["PL", "PD", "SA", "BL1", "FL1", "DED", "BSA", "WC"]
                fd_summary = {"matches": 0, "updated_count": 0}
                for _sync_code in LIVE_SYNC_COMPETITIONS:
                    try:
                        _s = await service.ingest_matches(db, _sync_code)
                        fd_summary["matches"] = fd_summary.get("matches", 0) + _s.get("matches", 0)
                        fd_summary["updated_count"] = fd_summary.get("updated_count", 0) + _s.get("updated_count", 0)
                    except Exception as _sync_err:
                        logger.warning(f"Live sync: ingest_matches({_sync_code}) failed: {_sync_err}")
                    await asyncio.sleep(0.05)  # Yield to event loop between competitions
                logger.info(
                    f"Football-Data sync completed - processed={fd_summary.get('matches', 0)} "
                    f"updated={fd_summary.get('updated_count', 0)} "
                )

                # Now, ingest live data from API-Football
                af_summary = await service.ingest_api_football_live(db)
                logger.info(
                    f"API-Football sync completed - "
                    f"live matches fetched: {af_summary.get('live_matches_fetched', 0)}, "
                    f"matches updated: {af_summary.get('matches_updated', 0)}, "
                    f"red cards found: {af_summary.get('red_cards_found', 0)}, "
                    f"minutes updated: {af_summary.get('minutes_updated', 0)}, "
                    f"statistics updated: {af_summary.get('statistics_updated', 0)}, "
                    f"lineups updated: {af_summary.get('lineups_updated', 0)}, "
                    f"events updated: {af_summary.get('events_updated', 0)}"
                )

                # Combine all summaries
                combined_summary = {
                    **fd_summary,
                    **af_summary,
                }

                record_sync_complete(started_at, combined_summary)

            except Exception as e:
                record_sync_error(str(e))
                logger.error(f"Live sync failed: {e}", exc_info=True)
            finally:
                db.close()
        except asyncio.CancelledError:
            logger.info("Live match sync task cancelled.")
            break
        except Exception as e:
            record_sync_error(str(e))
            logger.error(f"Live sync unexpected error: {e}", exc_info=True)

        await asyncio.sleep(30)


async def run_odds_sync():
    """
    Fetch bookmaker odds from The Odds API every 5 minutes.
    This ensures odds are kept current for value betting analysis.
    """
    from utils.config import settings
    
    if not settings.ODDS_API_KEY:
        logger.warning("Odds sync task disabled: ODDS_API_KEY not configured")
        return
    
    logger.info("Odds sync background task initialized (5-minute interval).")
    await asyncio.sleep(10)  # let startup finish before first sync

    while True:
        started_at = datetime.now(timezone.utc)
        logger.info("Odds sync started")

        try:
            from database.connection import SessionLocal
            from services.odds_service import OddsService

            db = SessionLocal()
            try:
                odds_service = OddsService()
                raw_odds = odds_service.fetch_upcoming_odds()
                
                if not raw_odds:
                    logger.warning("No odds data retrieved from The Odds API")
                else:
                    odds_service.store_odds(db, raw_odds)
                    duration = (datetime.now(timezone.utc) - started_at).total_seconds()
                    logger.info(
                        f"Odds sync completed successfully - "
                        f"fetched {len(raw_odds)} odds entries in {duration:.2f}s"
                    )
            except Exception as e:
                logger.error(f"Odds sync failed: {e}", exc_info=True)
            finally:
                db.close()
        except asyncio.CancelledError:
            logger.info("Odds sync task cancelled.")
            break
        except Exception as e:
            logger.error(f"Odds sync unexpected error: {e}", exc_info=True)

        await asyncio.sleep(300)  # 5 minutes


# Active domestic league competitions for daily data sync
ACTIVE_LEAGUE_COMPETITIONS = [
    "PL",   # Premier League
    "PD",   # La Liga
    "SA",   # Serie A
    "BL1",  # Bundesliga
    "FL1",  # Ligue 1
    "DED",  # Eredivisie
    "BSA",  # Brasileirão
]

# International competitions for daily data sync (CL excluded: 2024-25 season complete, 2025-26 not yet published)
SCHEDULED_INTERNATIONAL_COMPETITIONS = [
    "WC",
    "EC",
    "CA",
    "UNL",
    "WCQ",
]

# Combined list for the daily full-pipeline scheduler
SCHEDULED_ALL_COMPETITIONS = ACTIVE_LEAGUE_COMPETITIONS + SCHEDULED_INTERNATIONAL_COMPETITIONS


async def run_daily_scheduler():
    """
    Asynchronous background loop to run data ingestion at 02:00 AM IST daily.
    """
    ist_tz = timezone(timedelta(hours=5, minutes=30))
    logger.info("Daily scheduler background task initialized.")

    while True:
        try:
            now = datetime.now(ist_tz)
            target = now.replace(hour=2, minute=0, second=0, microsecond=0)
            if now >= target:
                target += timedelta(days=1)

            seconds_to_sleep = (target - now).total_seconds()
            logger.info(
                f"Scheduler: next run scheduled at {target.isoformat()} (sleeping for {seconds_to_sleep:.1f} seconds)"
            )
            await asyncio.sleep(seconds_to_sleep)

            logger.info("Scheduler: Triggering scheduled daily data collection job...")
            from database.connection import SessionLocal
            from services.collection_service import CollectionService

            db = SessionLocal()
            try:
                service = CollectionService()
                scheduler_summary = {}
                for competition_code in SCHEDULED_ALL_COMPETITIONS:
                    logger.info(
                        f"Scheduler: Running automated provider pipeline for {competition_code}..."
                    )
                    scheduler_summary[
                        competition_code
                    ] = await service.ingest_football_data(db, competition_code)
                    db.expire_all()

                try:
                    logger.info(
                        "Scheduler: Running optional SofaScore sync at end of provider chain..."
                    )
                    scheduler_summary[
                        "SofaScore"
                    ] = await service.ingest_sofascore_live(db)
                except Exception as sofascore_err:
                    logger.warning(
                        f"Scheduler: SofaScore sync skipped/failed: {sofascore_err}"
                    )
                    scheduler_summary["SofaScore"] = {
                        "status": "failed",
                        "error": str(sofascore_err),
                    }

                logger.info(
                    f"Scheduler: Daily collection job completed successfully: {scheduler_summary}"
                )

                # --- New: Automatic ELO Refresh Pipeline ---
                try:
                    logger.info(
                        "Scheduler: Starting automatic ELO ratings and FIFA rankings refresh..."
                    )
                    start_time = datetime.now()

                    from ml.compute_elo_ratings import (
                        compute_all_elo_ratings,
                        save_elo_ranks_to_teams,
                        save_elo_to_db,
                    )

                    # 1. Compute Elo ratings chronologically
                    elo_ratings = compute_all_elo_ratings()

                    # Validation: check that we received calculated ratings
                    if not elo_ratings or len(elo_ratings) == 0:
                        raise ValueError("Computed ELO ratings dictionary is empty.")

                    # 2. Save Elo ratings to database
                    save_elo_to_db(elo_ratings)

                    # 3. Save Elo ranks to teams table
                    save_elo_ranks_to_teams(elo_ratings)

                    # Validation: verify that the team_elo table is populated
                    from models.team_elo import TeamElo

                    elo_count = db.query(TeamElo).count()
                    if elo_count == 0:
                        raise ValueError(
                            "Database validation failed: team_elo table contains 0 records after update."
                        )

                    end_time = datetime.now()
                    duration = (end_time - start_time).total_seconds()

                    # Log Top 10 rankings
                    sorted_elo = sorted(
                        elo_ratings.items(), key=lambda x: x[1], reverse=True
                    )
                    top_10 = sorted_elo[:10]
                    top_10_str = "\n".join(
                        [
                            f"    {rank}. {name}: {rating:.1f}"
                            for rank, (name, rating) in enumerate(top_10, 1)
                        ]
                    )

                    logger.info(
                        f"Scheduler: ELO refresh completed successfully in {duration:.2f}s.\n"
                        f"  - Start Time: {start_time.isoformat()}\n"
                        f"  - End Time: {end_time.isoformat()}\n"
                        f"  - Teams Updated: {len(elo_ratings)}\n"
                        f"  - New Top 10 Rankings:\n{top_10_str}"
                    )
                except Exception as elo_err:
                    logger.error(
                        f"Scheduler: Automatic ELO refresh failed: {elo_err}",
                        exc_info=True,
                    )
                # -------------------------------------------

                # --- Automatic Prediction Generation (post-ingestion) ---
                try:
                    logger.info(
                        "Scheduler: Triggering bulk prediction generation for upcoming fixtures..."
                    )
                    from services.prediction_service import PredictionService

                    pred_service = PredictionService()
                    preds = pred_service.generate_predictions_for_fixtures(db)
                    logger.info(
                        f"Scheduler: Prediction generation completed — {len(preds)} predictions upserted."
                    )
                    enriched = pred_service.generate_enrichment_for_fixtures(db)
                    logger.info(
                        f"Scheduler: Enrichment generation completed — {enriched} fixtures enriched."
                    )
                except Exception as pred_err:
                    logger.error(
                        f"Scheduler: Automatic prediction generation failed: {pred_err}",
                        exc_info=True,
                    )
                # -------------------------------------------------------

            except Exception as e:
                logger.error(f"Scheduler: Daily collection job failed: {e}")
            finally:
                db.close()

        except asyncio.CancelledError:
            logger.info("Scheduler background task cancelled.")
            break
        except Exception as e:
            logger.error(f"Scheduler encountered an unexpected error: {e}")
            await asyncio.sleep(60)


@app.on_event("startup")
async def startup_event():
    # ── Log environment variables and configuration ───────────────────────────────
    logger.info("=" * 80)
    logger.info("STARTUP: Football Prediction Platform Backend")
    logger.info("=" * 80)
    
    # Log critical environment variables (masked)
    from utils.config import settings
    logger.info(f"STARTUP: DATABASE_URL configured: {'YES' if settings.DATABASE_URL else 'NO'}")
    logger.info(f"STARTUP: FOOTBALL_DATA_API_KEY configured: {'YES' if settings.FOOTBALL_DATA_API_KEY else 'NO'}")
    logger.info(f"STARTUP: API_FOOTBALL_KEY configured: {'YES' if settings.API_FOOTBALL_KEY else 'NO'}")
    logger.info(f"STARTUP: ODDS_API_KEY configured: {'YES' if settings.ODDS_API_KEY else 'NO'}")
    logger.info(f"STARTUP: OPENROUTER_API_KEY configured: {'YES' if settings.OPENROUTER_API_KEY else 'NO'}")
    
    # Log allowed origins
    logger.info(f"STARTUP: ALLOWED_ORIGINS: {ALLOWED_ORIGINS}")
    logger.info(f"STARTUP: ALLOWED_ORIGIN_REGEX: {ALLOWED_ORIGIN_REGEX}")
    logger.info(f"STARTUP: VERCEL_DOMAIN: {os.getenv('VERCEL_DOMAIN', 'NOT SET')}")
    
    # ── Test database connection ───────────────────────────────────────────────
    try:
        from database.connection import SessionLocal
        from sqlalchemy import text
        test_db = SessionLocal()
        test_db.execute(text("SELECT 1"))
        test_db.close()
        logger.info("STARTUP: Database connection successful ✓")
    except Exception as e:
        logger.error(f"STARTUP: Database connection FAILED: {e}", exc_info=True)

    # ── Load ML models once at startup ───────────────────────────────────────
    try:
        logger.info("Startup: loading ML models via ModelService...")
        model_service.load_models()
        logger.info("Startup: ML models loaded successfully ✓")
        logger.info(f"STARTUP: Models ready: {model_service.is_ready}")
        logger.info(f"STARTUP: Model versions: {model_service.model_versions}")
    except Exception as e:
        logger.error(f"Startup: FAILED to load ML models — {e}", exc_info=True)
        # Do NOT crash the server; predictions will return 503 until fixed.

    # ── Seed ELO ratings if the table is empty ────────────────────────────────
    try:
        logger.info("Startup: checking team_elo table for seed data …")
        from database.connection import SessionLocal
        from ml.seed_elo import seed_elo_ratings

        _db = SessionLocal()
        try:
            seed_elo_ratings(_db)
        finally:
            _db.close()
    except Exception as e:
        logger.error(f"Startup: ELO seed step failed — {e}", exc_info=True)

    # ── Bootstrap predictions for any TIMED fixtures missing predictions ───────
    # DISABLED: Long-running process causing startup timeout. Predictions will be generated by scheduler.
    # try:
    #     logger.info("Startup: bootstrapping predictions for upcoming fixtures...")
    #     from database.connection import SessionLocal
    #     from services.prediction_service import PredictionService

    #     async def _bootstrap_predictions():
    #         await asyncio.sleep(10)  # allow all startup tasks to settle first
    #         _db = SessionLocal()
    #         try:
    #             pred_service = PredictionService()
    #             preds = pred_service.generate_predictions_for_fixtures(_db)
    #             logger.info(
    #                 f"Startup: bootstrap predictions complete — {len(preds)} predictions upserted."
    #             )
    #             enriched = pred_service.generate_enrichment_for_fixtures(_db)
    #             logger.info(
    #                 f"Startup: bootstrap enrichment complete — {enriched} fixtures enriched."
    #             )
    #         except Exception as _e:
    #             logger.error(
    #                 f"Startup: prediction bootstrap failed — {_e}", exc_info=True
    #             )
    #         finally:
    #             _db.close()

    #     asyncio.create_task(_bootstrap_predictions())
    # except Exception as e:
    #     logger.error(
    #         f"Startup: failed to schedule prediction bootstrap — {e}", exc_info=True
    #     )
    logger.info("Startup: Prediction bootstrap disabled - will be handled by scheduler")

    logger.info("Starting background scheduler task...")
    asyncio.create_task(run_daily_scheduler())
    asyncio.create_task(run_live_match_sync())
    asyncio.create_task(run_odds_sync())
