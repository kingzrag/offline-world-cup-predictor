import time
import asyncio
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from database.base import Base
from database.connection import engine
from api.routes import matches, teams, players, injuries, predictions
from api.routes import predict as predict_router
from services.model_service import model_service
from utils.logger import logger

# Automatically trigger database schema creation on startup.
# In a real environment, this operates as a fallback / bootstrapper
# alongside alembic migrations.
try:
    logger.info("Initializing database schema tables creation...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema sync completed successfully.")
except Exception as err:
    logger.error(f"Critical: Database connection failed during startup: {err}")

app = FastAPI(
    title="Football Prediction Platform",
    description="Production-grade sports predictions backend engine utilizing FastAPI and PostgreSQL.",
    version="1.0.0"
)

# Enable CORS for standard web environments
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        logger.info(f"Response: {method} {path} - Status: {response.status_code} - Completed in {duration:.4f}s")
        return response
    except Exception as exc:
        duration = time.time() - start_time
        logger.error(f"Request Failure: {method} {path} - Completed with exception in {duration:.4f}s - {str(exc)}")
        raise exc

# Centralized error handler
@app.exception_handler(Exception)
def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception raised on {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "An internal system error occurred. Please contact administrator.",
            "details": str(exc)
        }
    )

# Basic health-check route
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "system": "football_prediction_platform_backend",
        "models_loaded": model_service.is_ready,
        "model_versions": model_service.model_versions,
        "timestamp": time.time()
    }

# Register primary API sub-routers
app.include_router(matches.router, prefix="/api/v1")
app.include_router(teams.router, prefix="/api/v1")
app.include_router(players.router, prefix="/api/v1")
app.include_router(injuries.router, prefix="/api/v1")
app.include_router(predictions.router, prefix="/api/v1")

# ── New ML prediction API (ModelService-backed) ───────────────────────────────
app.include_router(predict_router.router)


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
            logger.info(f"Scheduler: next run scheduled at {target.isoformat()} (sleeping for {seconds_to_sleep:.1f} seconds)")
            await asyncio.sleep(seconds_to_sleep)
            
            logger.info("Scheduler: Triggering scheduled daily data collection job...")
            from database.connection import SessionLocal
            from services.collection_service import CollectionService
            
            db = SessionLocal()
            try:
                service = CollectionService()
                await service.ingest_football_data(db, "WC")
                logger.info("Scheduler: Daily collection job completed successfully.")
                
                # --- New: Automatic ELO Refresh Pipeline ---
                try:
                    logger.info("Scheduler: Starting automatic ELO ratings and FIFA rankings refresh...")
                    start_time = datetime.now()
                    
                    from ml.compute_elo_ratings import compute_all_elo_ratings, save_elo_to_db, save_elo_ranks_to_teams
                    
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
                        raise ValueError("Database validation failed: team_elo table contains 0 records after update.")
                    
                    end_time = datetime.now()
                    duration = (end_time - start_time).total_seconds()
                    
                    # Log Top 10 rankings
                    sorted_elo = sorted(elo_ratings.items(), key=lambda x: x[1], reverse=True)
                    top_10 = sorted_elo[:10]
                    top_10_str = "\n".join([f"    {rank}. {name}: {rating:.1f}" for rank, (name, rating) in enumerate(top_10, 1)])
                    
                    logger.info(
                        f"Scheduler: ELO refresh completed successfully in {duration:.2f}s.\n"
                        f"  - Start Time: {start_time.isoformat()}\n"
                        f"  - End Time: {end_time.isoformat()}\n"
                        f"  - Teams Updated: {len(elo_ratings)}\n"
                        f"  - New Top 10 Rankings:\n{top_10_str}"
                    )
                except Exception as elo_err:
                    logger.error(f"Scheduler: Automatic ELO refresh failed: {elo_err}", exc_info=True)
                # -------------------------------------------
                
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
    # ── Load ML models once at startup ───────────────────────────────────────
    try:
        logger.info("Startup: loading ML models via ModelService...")
        model_service.load_models()
        logger.info("Startup: ML models loaded successfully ✓")
    except Exception as e:
        logger.error(f"Startup: FAILED to load ML models — {e}", exc_info=True)
        # Do NOT crash the server; predictions will return 503 until fixed.

    logger.info("Starting background scheduler task...")
    asyncio.create_task(run_daily_scheduler())
