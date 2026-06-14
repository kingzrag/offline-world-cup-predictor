"""
api/routes/predict.py
=====================
Production-ready prediction endpoints.

    POST  /api/predict              → Full prediction (1X2 + goals + all markets)
    POST  /api/predict-batch        → Batch predictions for multiple matches (15-min cache)
    GET   /api/teams                → All teams (searchable)
    GET   /api/team/{team_name}     → Team profile + stats
    GET   /api/fixtures             → Scheduled & Live World Cup matches
    GET   /api/health               → Model health check

All ML inference goes through the ModelService singleton.
"""

import time
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.connection import get_db
from services.model_service import model_service
from utils.logger import logger

router = APIRouter(prefix="/api", tags=["Predictions API"])


# ── Request / Response schemas ────────────────────────────────────────────────

class PredictRequest(BaseModel):
    home_team: str = Field(..., example="Brazil",  description="Name of the home team")
    away_team: str = Field(..., example="Germany", description="Name of the away team")
    competition_code: Optional[str] = Field(
        default="WC",
        example="WC",
        description="Competition code (WC = World Cup, PL = Premier League, etc.)"
    )


class BatchMatchItem(BaseModel):
    home_team: str = Field(..., example="Brazil")
    away_team: str = Field(..., example="Germany")
    competition_code: Optional[str] = Field(default="WC")


class BatchPredictRequest(BaseModel):
    matches: List[BatchMatchItem] = Field(
        ...,
        description="Array of match pairs to predict in one round-trip.",
        max_items=100,
    )


# ── In-memory prediction cache ─────────────────────────────────────────────────
# Key: "home_team|away_team|competition_code"   Value: (result_dict, expiry_ts)
PREDICTION_CACHE_TTL_SECONDS: int = 15 * 60   # 15 minutes
_prediction_cache: Dict[str, Tuple[Any, float]] = {}


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/predict", summary="Full match prediction – 1X2 + goals + all betting markets")
def predict_match(
    body: PredictRequest,
    db: Session = Depends(get_db),
):
    """
    Returns a complete prediction bundle for a head-to-head fixture.

    **Response includes:**
    - 1X2 outcome probabilities (Home Win / Draw / Away Win)
    - Predicted result + confidence
    - Expected home & away goals
    - Over/Under 1.5 / 2.5 / 3.5
    - BTTS Yes / No
    - Most likely scoreline + Top 5 scorelines
    - Asian Handicap lines
    - Team Goals Over 0.5 / 1.5 / 2.5
    - Full Poisson probability matrix
    """
    if not model_service.is_ready:
        raise HTTPException(
            status_code=503,
            detail="ML models are not yet loaded. Please retry in a moment."
        )

    t_start = time.perf_counter()
    logger.info(f"POST /api/predict  →  {body.home_team} vs {body.away_team} [{body.competition_code}]")

    try:
        result = model_service.predict(
            db=db,
            home_team_name=body.home_team,
            away_team_name=body.away_team,
            competition_code=body.competition_code,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Prediction failed for {body.home_team} vs {body.away_team}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Prediction engine error: {str(e)}")

    elapsed_ms = round((time.perf_counter() - t_start) * 1000, 1)
    logger.info(f"POST /api/predict  →  completed in {elapsed_ms} ms")

    return {
        "status":       "success",
        "latency_ms":   elapsed_ms,
        "prediction":   result,
    }


# ── Batch prediction endpoint ─────────────────────────────────────────────────

@router.post("/predict-batch", summary="Batch predictions for multiple matches (15-min cache)")
def predict_batch(
    body: BatchPredictRequest,
    db: Session = Depends(get_db),
):
    """
    Accepts an array of match pairs and returns predictions for all of them in a
    single HTTP round-trip.  Results are cached in-process for 15 minutes so that
    repeated page loads do not re-run expensive ML inference.

    **Response shape:**
    ```json
    {
      "status": "success",
      "total_ms": 1234.5,
      "count": 48,
      "results": [
        { "home_team": "Brazil", "away_team": "Germany",
          "status": "success", "prediction": {...}, "cached": false, "latency_ms": 45.2 },
        { "home_team": "Canada", "away_team": "Morocco",
          "status": "error",   "error": "Team not found", "cached": false, "latency_ms": 3.1 }
      ]
    }
    ```
    """
    if not model_service.is_ready:
        raise HTTPException(
            status_code=503,
            detail="ML models are not yet loaded. Please retry in a moment."
        )

    batch_start = time.perf_counter()
    now = time.time()
    results = []

    # Evict stale cache entries once per batch request (O(n) but n is small)
    expired_keys = [k for k, (_, exp) in _prediction_cache.items() if now > exp]
    for k in expired_keys:
        del _prediction_cache[k]

    logger.info(
        f"POST /api/predict-batch  →  {len(body.matches)} matches requested "
        f"({len(expired_keys)} stale cache entries evicted)"
    )

    for item in body.matches:
        cache_key = f"{item.home_team.strip()}|{item.away_team.strip()}|{item.competition_code or 'WC'}"
        t0 = time.perf_counter()

        # ── Cache hit ────────────────────────────────────────────────────────
        if cache_key in _prediction_cache:
            cached_result, _ = _prediction_cache[cache_key]
            latency_ms = round((time.perf_counter() - t0) * 1000, 1)
            results.append({
                "home_team":  item.home_team,
                "away_team":  item.away_team,
                "status":     "success",
                "prediction": cached_result,
                "cached":     True,
                "latency_ms": latency_ms,
            })
            continue

        # ── Cache miss — run inference ────────────────────────────────────────
        try:
            prediction = model_service.predict(
                db=db,
                home_team_name=item.home_team,
                away_team_name=item.away_team,
                competition_code=item.competition_code or "WC",
            )
            latency_ms = round((time.perf_counter() - t0) * 1000, 1)
            logger.info(
                f"  [{item.home_team} vs {item.away_team}] predicted in {latency_ms} ms"
            )
            # Store in cache
            _prediction_cache[cache_key] = (prediction, now + PREDICTION_CACHE_TTL_SECONDS)
            results.append({
                "home_team":  item.home_team,
                "away_team":  item.away_team,
                "status":     "success",
                "prediction": prediction,
                "cached":     False,
                "latency_ms": latency_ms,
            })
        except Exception as e:
            latency_ms = round((time.perf_counter() - t0) * 1000, 1)
            logger.warning(
                f"  [{item.home_team} vs {item.away_team}] prediction failed in {latency_ms} ms: {e}"
            )
            results.append({
                "home_team":  item.home_team,
                "away_team":  item.away_team,
                "status":     "error",
                "error":      str(e),
                "cached":     False,
                "latency_ms": latency_ms,
            })

    total_ms = round((time.perf_counter() - batch_start) * 1000, 1)
    cache_hits  = sum(1 for r in results if r.get("cached"))
    cache_miss  = len(results) - cache_hits
    logger.info(
        f"POST /api/predict-batch  ←  {len(results)} results in {total_ms} ms "
        f"(cache hits: {cache_hits}, misses: {cache_miss})"
    )

    return {
        "status":   "success",
        "total_ms": total_ms,
        "count":    len(results),
        "results":  results,
    }


@router.get("/teams", summary="List all teams (searchable)")
def get_teams(
    search: Optional[str] = Query(None, description="Filter by team name (partial match)"),
    limit:  int           = Query(100,  ge=1, le=500, description="Max teams to return"),
    db: Session = Depends(get_db),
):
    """
    Returns a list of all teams in the database.
    Optionally filter by partial name match via `?search=Brazil`.
    """
    from models import Team

    query = db.query(Team)
    if search:
        from sqlalchemy import or_ as sql_or
        query = query.filter(
            sql_or(
                Team.name.ilike(f"%{search}%"),
                Team.tla.ilike(f"%{search}%"),
                Team.short_name.ilike(f"%{search}%")
            )
        )

    teams = query.order_by(Team.name.asc()).limit(limit).all()

    return {
        "status": "success",
        "count":  len(teams),
        "teams": [
            {
                "id":         t.id,
                "name":       t.name,
                "short_name": t.short_name,
                "tla":        t.tla,
                "crest_url":  t.crest_url,
                "founded":    t.founded,
                "venue":      t.venue,
            }
            for t in teams
        ],
    }


@router.get("/team/{team_name}", summary="Team profile + recent form")
def get_team_profile(
    team_name: str,
    db: Session = Depends(get_db),
):
    """
    Returns a detailed team profile including:
    - Basic info (name, crest, venue, founded)
    - Current ELO rating
    - Last 5 match results (form)
    - Squad size
    """
    from models import Team, Match, TeamElo

    # Resolve team name aliases for United States
    aliases = {
        "USA": "United States",
        "US": "United States",
        "UNITED STATES OF AMERICA": "United States"
    }
    clean_search = team_name.strip().upper()
    resolved_name = aliases.get(clean_search, team_name)

    # Exact match first, then TLA/short_name/fuzzy fallback
    from sqlalchemy import or_ as sql_or
    team = (
        db.query(Team).filter(Team.name.ilike(resolved_name)).first()
        or db.query(Team).filter(Team.tla.ilike(resolved_name)).first()
        or db.query(Team).filter(Team.short_name.ilike(resolved_name)).first()
        or db.query(Team).filter(Team.name.ilike(f"%{resolved_name}%")).first()
    )
    if not team:
        raise HTTPException(status_code=404, detail=f"Team '{team_name}' not found.")

    # ELO rating
    elo_record = (
        db.query(TeamElo).filter(TeamElo.team_name == team.name).first()
        or db.query(TeamElo).filter(TeamElo.team_name.ilike(f"%{team.name}%")).first()
    )
    elo_rating = elo_record.elo_rating if elo_record else None

    # Last 5 finished matches
    from sqlalchemy import or_ as sql_or, desc
    recent_matches = (
        db.query(Match)
        .filter(
            sql_or(Match.home_team_id == team.id, Match.away_team_id == team.id),
            Match.status == "FINISHED",
        )
        .order_by(desc(Match.utc_date))
        .limit(5)
        .all()
    )

    form = []
    for m in recent_matches:
        is_home = m.home_team_id == team.id
        if m.winner == "HOME_TEAM":
            result = "W" if is_home else "L"
        elif m.winner == "AWAY_TEAM":
            result = "L" if is_home else "W"
        else:
            result = "D"

        opp = m.away_team if is_home else m.home_team
        form.append({
            "date":     m.utc_date.isoformat() if m.utc_date else None,
            "opponent": opp.name if opp else "Unknown",
            "home":     is_home,
            "score":    f"{m.home_score}-{m.away_score}" if m.home_score is not None else None,
            "result":   result,
        })

    # Calculate ELO rank
    elo_rank = 15
    if elo_rating is not None:
        elo_rank = db.query(TeamElo).filter(TeamElo.elo_rating > elo_rating).count() + 1

    # Format squad market value
    val_m = team.squad_market_value or team.market_value or 0
    if val_m >= 1000:
        val_str = f"€{val_m/1000:.2f}B"
    elif val_m > 0:
        val_str = f"€{val_m:.1f}M"
    else:
        val_str = "€250M"

    # Compile injuries
    injuries_list = []
    if hasattr(team, "national_team_injuries"):
        for inj in (team.national_team_injuries or []):
            injuries_list.append(f"{inj.player_name} ({inj.injury_description or inj.injury_status or 'Injured'})")
    if hasattr(team, "injuries"):
        for inj in (team.injuries or []):
            injuries_list.append(f"{inj.player_name} ({inj.reason or 'Injured'})")

    # Compile suspensions
    suspensions_list = []
    if hasattr(team, "national_team_suspensions"):
        for susp in (team.national_team_suspensions or []):
            suspensions_list.append(f"{susp.player_name} ({susp.suspension_reason or 'Suspended'})")
    if hasattr(team, "suspensions"):
        for susp in (team.suspensions or []):
            suspensions_list.append(f"{susp.player_name} ({susp.reason or 'Suspended'})")

    return {
        "status": "success",
        "team": {
            "id":          team.id,
            "name":        team.name,
            "short_name":  team.short_name,
            "tla":         team.tla,
            "crest_url":   team.crest_url,
            "founded":     team.founded,
            "venue":       team.venue,
            "elo_rating":  elo_rating,
            "elo_rank":    elo_rank,
            "fifa_rank":   team.fifa_ranking or 15,
            "squad_value": val_str,
            "injuries":    injuries_list,
            "suspensions": suspensions_list,
            "squad_size":  len(team.players) if hasattr(team, "players") else None,
            "recent_form": form,
        },
    }


@router.get("/fixtures", summary="FIFA World Cup fixtures — all statuses with live scores")
def get_fixtures(
    status:           Optional[str]  = Query(
        None,
        description=(
            "Filter by match status. "
            "Values: TIMED, SCHEDULED, IN_PLAY, PAUSED, FINISHED, POSTPONED. "
            "Omit to return all matches."
        ),
    ),
    stage:            Optional[str]  = Query(
        None,
        description="Filter by tournament stage, e.g. GROUP_STAGE, ROUND_OF_16, QUARTER_FINALS, SEMI_FINALS, FINAL.",
    ),
    group:            Optional[str]  = Query(
        None,
        description="Filter by group name, e.g. GROUP_A, GROUP_B … GROUP_L.",
    ),
    date_from:        Optional[date] = Query(
        None,
        description="Return only matches on or after this date (YYYY-MM-DD, UTC).",
    ),
    date_to:          Optional[date] = Query(
        None,
        description="Return only matches on or before this date (YYYY-MM-DD, UTC).",
    ),
    year:             Optional[int]  = Query(
        None,
        description="Filter matches by kickoff year, e.g. 2026.",
    ),
    show_historical:  bool           = Query(
        False,
        description="Whether to include historical matches (year < 2026).",
    ),
    competition_code: str            = Query(
        "WC",
        description="Competition code to query. Defaults to WC (FIFA World Cup).",
    ),
    limit:            int            = Query(
        200, ge=1, le=500,
        description="Maximum number of fixtures to return.",
    ),
    db: Session = Depends(get_db),
):
    """
    Returns FIFA World Cup fixtures sourced directly from the database
    populated via football-data.org.

    **Fields per fixture:**
    - `home_team` / `away_team` — id, name, short_name, tla, crest_url
    - `kickoff_time` — ISO-8601 UTC string
    - `status` — TIMED | SCHEDULED | IN_PLAY | PAUSED | FINISHED | POSTPONED
    - `stage` — tournament round (GROUP_STAGE, ROUND_OF_16 …)
    - `group` — group letter (GROUP_A … GROUP_L), null for knockout rounds
    - `venue` — stadium name from the home team record
    - `live_score` — `{home, away, is_live}` when IN_PLAY or PAUSED;
                     actual final score when FINISHED; null otherwise
    - `winner` — HOME_TEAM | AWAY_TEAM | DRAW | null

    Results are ordered by kick-off time ascending.
    """
    from models import Match, Competition
    from sqlalchemy import asc

    # ── Resolve competition ───────────────────────────────────────────────────
    comp = db.query(Competition).filter_by(code=competition_code.upper()).first()
    if not comp:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Competition '{competition_code}' not found in the database. "
                "Run the data collection pipeline first: "
                "POST /api/v1/predictions/collect?competition_code=WC"
            ),
        )

    # ── Build query ───────────────────────────────────────────────────────────
    query = db.query(Match).filter(Match.competition_id == comp.id)

    if status:
        query = query.filter(Match.status == status.upper())

    if stage:
        query = query.filter(Match.stage == stage.upper())

    if group:
        query = query.filter(Match.group == group.upper())

    if date_from:
        query = query.filter(Match.utc_date >= datetime.combine(date_from, datetime.min.time()))

    if date_to:
        query = query.filter(Match.utc_date <= datetime.combine(date_to, datetime.max.time()))

    from sqlalchemy import extract
    if year:
        query = query.filter(extract('year', Match.utc_date) == year)
    elif not show_historical:
        # Default to only showing 2026 World Cup fixtures
        query = query.filter(extract('year', Match.utc_date) >= 2026)

    # Fetch all matching results to sort properly in Python (to avoid LIMIT truncating 2026 matches)
    matches = query.all()

    # ── Sort matches in Python ────────────────────────────────────────────────
    # Priority rules:
    # 1. LIVE matches first (status IN_PLAY, PAUSED).
    # 2. Upcoming matches (status TIMED, SCHEDULED, POSTPONED, etc.) from 2026, sorted ascending by utc_date.
    # 3. Finished matches from 2026, sorted descending by utc_date.
    # 4. Historical matches (< 2026), sorted descending by utc_date.
    def match_sort_key(m):
        m_year = m.utc_date.year if m.utc_date else 2026
        is_2026 = m_year >= 2026
        
        # Sort priority tier
        if m.status in {"IN_PLAY", "PAUSED"}:
            tier = 0  # Live matches
        elif is_2026:
            if m.status != "FINISHED":
                tier = 1  # Upcoming 2026 matches
            else:
                tier = 2  # Finished 2026 matches
        else:
            tier = 3  # Historical matches
            
        ts = m.utc_date.timestamp() if m.utc_date else 0
        if tier in (0, 1):
            date_val = ts
        else:
            date_val = -ts
            
        return (tier, date_val)

    matches.sort(key=match_sort_key)
    matches = matches[:limit]

    # ── Serialise helpers ─────────────────────────────────────────────────────
    live_statuses  = {"IN_PLAY", "PAUSED"}
    score_statuses = live_statuses | {"FINISHED"}

    def _team(t):
        if not t:
            return None
        return {
            "id":         t.id,
            "name":       t.name,
            "short_name": t.short_name,
            "tla":        t.tla,
            "crest_url":  t.crest_url,
        }

    def _live_score(m):
        """Return score dict when data is available, else None."""
        if m.status in score_statuses and m.home_score is not None and m.away_score is not None:
            return {
                "home":    m.home_score,
                "away":    m.away_score,
                "is_live": m.status in live_statuses,
            }
        return None

    def _prediction(m):
        pred = m.predictions[0] if m.predictions else None
        if not pred:
            return None
        return {
            "predicted_outcome": pred.predicted_outcome,
            "home_probability": pred.home_probability,
            "away_probability": pred.away_probability,
            "draw_probability": pred.draw_probability,
        }

    fixtures_out = [
        {
            "id":           m.id,
            "kickoff_time": m.utc_date.isoformat() if m.utc_date else None,
            "status":       m.status,
            "stage":        m.stage,
            "group":        m.group,
            "venue":        m.home_team.venue if m.home_team else None,
            "competition":  comp.name,
            "home_team":    _team(m.home_team),
            "away_team":    _team(m.away_team),
            "live_score":   _live_score(m),
            "winner":       m.winner,
            "prediction":   _prediction(m),
        }
        for m in matches
    ]

    logger.info(
        f"GET /api/fixtures [{competition_code}] status={status} stage={stage} "
        f"group={group} → {len(fixtures_out)} fixtures"
    )

    return {
        "status":      "success",
        "competition": comp.name,
        "count":       len(fixtures_out),
        "fixtures":    fixtures_out,
    }


@router.get("/health", summary="Model health check")
def api_health():
    """
    Returns load status of both ML models and system readiness.
    """
    versions = model_service.model_versions
    return {
        "status":      "ready" if model_service.is_ready else "loading",
        "models_loaded": model_service.is_ready,
        "model_versions": versions,
        "timestamp":   time.time(),
    }
