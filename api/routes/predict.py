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
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.connection import get_db
from services.model_service import model_service
from utils.logger import logger

router = APIRouter(prefix="/api", tags=["Predictions API"])


def _compile_team_injuries_and_suspensions(db, team_id: int) -> tuple[list[str], list[str]]:
    """Load injury/suspension records for a team."""
    from models import Injury, Suspension

    injuries: list[str] = []
    suspensions: list[str] = []
    seen_injuries: set[tuple[str, str]] = set()
    seen_suspensions: set[tuple[str, str]] = set()

    def _add_injury(player_name: str, description: str) -> None:
        key = (player_name, description)
        if key not in seen_injuries:
            seen_injuries.add(key)
            injuries.append(f"{player_name} ({description})")

    def _add_suspension(player_name: str, reason: str) -> None:
        key = (player_name, reason)
        if key not in seen_suspensions:
            seen_suspensions.add(key)
            suspensions.append(f"{player_name} ({reason})")

    for inj in db.query(Injury).filter_by(team_id=team_id).all():
        description = inj.injury_type or "Injured"
        _add_injury(inj.player_name, description)

    for susp in db.query(Suspension).filter_by(team_id=team_id).all():
        reason = susp.suspension_reason or "Suspended"
        _add_suspension(susp.player_name, reason)

    return injuries, suspensions


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
    match_id: Optional[str] = Field(
        default=None,
        description="Optional client fixture id echoed back for reliable frontend mapping",
    )


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
# Key: match_id (int)   Value: (enrichment_dict, expiry_ts) — populated by /predict-batch
_enrichment_cache_by_match_id: Dict[int, Tuple[Any, float]] = {}


def _build_enrichment_from_xg(
    h_xg: float,
    a_xg: float,
    *,
    most_likely_score: Optional[str] = None,
) -> Dict[str, Any]:
    """Build response enrichment from stored xG using fast Poisson math (no ML)."""
    from services.poisson_engine import evaluate_poisson_engine

    poisson = evaluate_poisson_engine(max(h_xg, 0.01), max(a_xg, 0.01))
    return {
        "goals": {
            "home_xg":  h_xg,
            "away_xg":  a_xg,
            "total_xg": round(h_xg + a_xg, 4),
        },
        "markets": {
            "btts":              poisson["btts"],
            "over_under":        poisson["over_under"],
            "clean_sheet":       poisson["clean_sheet"],
            "most_likely_score": most_likely_score or poisson["most_likely_score"],
            "top_5_scorelines":  poisson["top_5_scorelines"],
            "team_goals":        poisson["team_goals"],
        },
    }


def _build_enrichment_from_prediction(pred_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Map a full model_service.predict() payload to fixtures-enriched enrichment."""
    goals = pred_dict["goals"]
    markets = pred_dict["markets"]
    return {
        "goals": {
            "home_xg":  goals["expected_home_goals"],
            "away_xg":  goals["expected_away_goals"],
            "total_xg": goals["total_expected_goals"],
        },
        "markets": {
            "btts":              markets["btts"],
            "over_under":        markets["over_under"],
            "clean_sheet":       markets.get("clean_sheet"),
            "most_likely_score": markets["most_likely_score"],
            "top_5_scorelines":  markets["top_5_scorelines"],
            "team_goals":        markets["team_goals"],
        },
    }


def _lookup_cached_enrichment(
    match_id: int,
    home_name: str,
    away_name: str,
    competition_code: str,
    now: float,
) -> Optional[Dict[str, Any]]:
    """Return in-memory cached enrichment if still valid (fallback when DB xG absent)."""
    cached_by_id = _enrichment_cache_by_match_id.get(match_id)
    if cached_by_id:
        enrichment, expiry = cached_by_id
        if now <= expiry:
            return enrichment
        del _enrichment_cache_by_match_id[match_id]

    cache_key = f"{home_name.strip()}|{away_name.strip()}|{competition_code}"
    cached_entry = _prediction_cache.get(cache_key)
    if cached_entry:
        pred_dict, expiry = cached_entry
        if now <= expiry:
            return _build_enrichment_from_prediction(pred_dict)
    return None


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
                "match_id":   item.match_id,
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
            enrichment_payload = _build_enrichment_from_prediction(prediction)
            if item.match_id is not None:
                try:
                    mid = int(item.match_id)
                    _enrichment_cache_by_match_id[mid] = (
                        enrichment_payload,
                        now + PREDICTION_CACHE_TTL_SECONDS,
                    )
                except (TypeError, ValueError):
                    pass
            results.append({
                "home_team":  item.home_team,
                "away_team":  item.away_team,
                "match_id":   item.match_id,
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
                "match_id":   item.match_id,
                "status":     "error",
                "error":      str(e),
                "cached":     False,
                "latency_ms": latency_ms,
            })

    total_ms = round((time.perf_counter() - batch_start) * 1000, 1)
    cache_hits  = sum(1 for r in results if r.get("cached"))
    success_count = sum(1 for r in results if r.get("status") == "success")
    error_count   = sum(1 for r in results if r.get("status") == "error")
    logger.info(
        f"POST /api/predict-batch  ←  {len(results)} results in {total_ms} ms "
        f"(success: {success_count}, errors: {error_count}, cache hits: {cache_hits})"
    )

    return {
        "status":        "success",
        "total_ms":      total_ms,
        "count":         len(results),
        "success_count": success_count,
        "error_count":   error_count,
        "results":       results,
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
    from sqlalchemy.orm import selectinload

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
    _team_load_options = (
        selectinload(Team.injuries),
        selectinload(Team.suspensions),
        selectinload(Team.national_team_injuries),
        selectinload(Team.national_team_suspensions),
        selectinload(Team.players),
    )

    def _find_team(name_filter):
        return (
            db.query(Team)
            .options(*_team_load_options)
            .filter(name_filter)
            .first()
        )

    team = (
        _find_team(Team.name.ilike(resolved_name))
        or _find_team(Team.tla.ilike(resolved_name))
        or _find_team(Team.short_name.ilike(resolved_name))
        or _find_team(Team.name.ilike(f"%{resolved_name}%"))
    )
    if not team:
        raise HTTPException(status_code=404, detail=f"Team '{team_name}' not found.")

    # ELO rating
    elo_record = (
        db.query(TeamElo).filter(TeamElo.team_name == team.name).first()
        or db.query(TeamElo).filter(TeamElo.team_name.ilike(f"%{team.name}%")).first()
    )
    elo_rating = elo_record.elo_rating if elo_record else None

    # Last 10 finished matches
    from sqlalchemy import or_ as sql_or, desc
    recent_matches_10 = (
        db.query(Match)
        .filter(
            sql_or(Match.home_team_id == team.id, Match.away_team_id == team.id),
            Match.status == "FINISHED",
        )
        .order_by(desc(Match.utc_date))
        .limit(10)
        .all()
    )

    btts_count = 0
    clean_sheet_count = 0
    played_count = len(recent_matches_10)
    for m in recent_matches_10:
        if m.home_score is not None and m.away_score is not None:
            if m.home_score > 0 and m.away_score > 0:
                btts_count += 1
            is_home = m.home_team_id == team.id
            conceded = m.away_score if is_home else m.home_score
            if conceded == 0:
                clean_sheet_count += 1

    btts_rate = round((btts_count / played_count) * 100, 1) if played_count > 0 else 0.0
    clean_sheet_rate = round((clean_sheet_count / played_count) * 100, 1) if played_count > 0 else 0.0

    recent_matches = recent_matches_10[:5]
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
            "date":     m.utc_date.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z") if m.utc_date else None,
            "opponent": opp.name if opp else "Unknown",
            "home":     is_home,
            "score":    f"{m.home_score}-{m.away_score}" if m.home_score is not None else None,
            "result":   result,
        })

    # Calculate ELO rank (None when no ELO data rather than a fake default)
    elo_rank = None
    if elo_rating is not None:
        elo_rank = db.query(TeamElo).filter(TeamElo.elo_rating > elo_rating).count() + 1

    # Format squad market value (N/A when genuinely missing rather than a fake €250M)
    val_m = team.squad_market_value or team.market_value or 0
    if val_m >= 1000:
        val_str = f"€{val_m/1000:.2f}B"
    elif val_m > 0:
        val_str = f"€{val_m:.1f}M"
    else:
        val_str = "N/A"

    injuries_list, suspensions_list = _compile_team_injuries_and_suspensions(db, team.id)

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
            "fifa_rank":   team.fifa_ranking,   # None when not set — no fake default
            "squad_value": val_str,
            "injuries":    injuries_list,
            "suspensions": suspensions_list,
            "squad_size":  len(team.players) if hasattr(team, "players") else None,
            "recent_form": form,
            "btts_rate":   btts_rate,
            "clean_sheet_rate": clean_sheet_rate,
        },
    }


@router.get("/h2h/{team_a_name}/{team_b_name}", summary="Head-to-head record between two teams")
def get_h2h(
    team_a_name: str,
    team_b_name: str,
    db: Session = Depends(get_db),
):
    """
    Returns head-to-head match history between two teams.

    **Response includes:**
    - Total previous meetings
    - Wins for team A, wins for team B, draws
    - Total goals scored by each team across all historical matches
    """
    from models import Team, Match
    from sqlalchemy import or_, and_, desc as sql_desc

    # Alias resolution
    aliases = {
        "USA": "United States",
        "US": "United States",
        "UNITED STATES OF AMERICA": "United States"
    }

    def resolve_team(name: str):
        clean = name.strip().upper()
        resolved = aliases.get(clean, name)
        team = (
            db.query(Team).filter(Team.name.ilike(resolved)).first()
            or db.query(Team).filter(Team.tla.ilike(resolved)).first()
            or db.query(Team).filter(Team.short_name.ilike(resolved)).first()
            or db.query(Team).filter(Team.name.ilike(f"%{resolved}%")).first()
        )
        return team

    team_a = resolve_team(team_a_name)
    if not team_a:
        raise HTTPException(status_code=404, detail=f"Team '{team_a_name}' not found.")
    team_b = resolve_team(team_b_name)
    if not team_b:
        raise HTTPException(status_code=404, detail=f"Team '{team_b_name}' not found.")

    # Query all finished head-to-head matches
    h2h_matches = (
        db.query(Match)
        .filter(
            and_(
                or_(
                    and_(Match.home_team_id == team_a.id, Match.away_team_id == team_b.id),
                    and_(Match.home_team_id == team_b.id, Match.away_team_id == team_a.id),
                ),
                Match.status == "FINISHED",
            )
        )
        .order_by(sql_desc(Match.utc_date))
        .limit(20)
        .all()
    )

    a_wins = 0
    b_wins = 0
    draws = 0
    a_goals = 0
    b_goals = 0

    recent_matches = []
    for m in h2h_matches:
        is_a_home = m.home_team_id == team_a.id
        if is_a_home:
            ga = m.home_score or 0
            gb = m.away_score or 0
        else:
            ga = m.away_score or 0
            gb = m.home_score or 0

        a_goals += ga
        b_goals += gb

        if m.winner == "DRAW":
            draws += 1
            result = "D"
        elif (m.winner == "HOME_TEAM" and is_a_home) or (m.winner == "AWAY_TEAM" and not is_a_home):
            a_wins += 1
            result = "W"
        else:
            b_wins += 1
            result = "L"

        recent_matches.append({
            "date": m.utc_date.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z") if m.utc_date else None,
            "home_team": m.home_team.name if m.home_team else None,
            "away_team": m.away_team.name if m.away_team else None,
            "score": f"{m.home_score}-{m.away_score}" if m.home_score is not None else None,
            "winner": m.winner,
            "result_for_a": result,
        })

    return {
        "status": "success",
        "team_a": team_a.name,
        "team_b": team_b.name,
        "previous_meetings": len(h2h_matches),
        "team_a_wins": a_wins,
        "team_b_wins": b_wins,
        "draws": draws,
        "team_a_goals": a_goals,
        "team_b_goals": b_goals,
        "recent_matches": recent_matches,
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
    from sqlalchemy import asc, desc, case, extract
    from sqlalchemy.orm import joinedload, selectinload

    t_start = time.perf_counter()

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
    # Eagerly load predictions, home_team, and away_team in one single batch to avoid N+1 queries.
    # We use joinedload for home/away teams (one-to-one) and selectinload for predictions (one-to-many/collection).
    query = (
        db.query(Match)
        .options(
            joinedload(Match.home_team),
            joinedload(Match.away_team),
            selectinload(Match.predictions)
        )
        .filter(Match.competition_id == comp.id)
    )

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

    if year:
        query = query.filter(extract('year', Match.utc_date) == year)
    elif not show_historical:
        # Default to only showing 2026 World Cup fixtures
        query = query.filter(extract('year', Match.utc_date) >= 2026)

    # ── SQL-Side Sorting ──────────────────────────────────────────────────────
    # Replicates Python sorting logic:
    # Tier 0: Live matches (status IN_PLAY, PAUSED)
    # Tier 1: Upcoming 2026+ matches (status != FINISHED and year >= 2026)
    # Tier 2: Finished 2026+ matches (status == FINISHED and year >= 2026)
    # Tier 3: Historical matches (year < 2026)
    m_year = extract('year', Match.utc_date)
    tier_case = case(
        (Match.status.in_({"IN_PLAY", "PAUSED"}), 0),
        ((m_year >= 2026) & (Match.status != "FINISHED"), 1),
        ((m_year >= 2026) & (Match.status == "FINISHED"), 2),
        else_=3
    )
    
    # Within Tier 0 and 1, sort ascending by kickoff date.
    # Within Tier 2 and 3, sort descending by kickoff date.
    asc_date = case(
        (tier_case.in_({0, 1}), Match.utc_date),
        else_=None
    )
    desc_date = case(
        (tier_case.in_({2, 3}), Match.utc_date),
        else_=None
    )

    query = query.order_by(
        tier_case.asc(),
        asc_date.asc(),
        desc_date.desc()
    )

    # ── Database Fetch ────────────────────────────────────────────────────────
    t_query_start = time.perf_counter()
    matches = query.limit(limit).all()
    t_query_end = time.perf_counter()
    query_ms = int((t_query_end - t_query_start) * 1000)

    # ── Serialise helpers ─────────────────────────────────────────────────────
    t_serialize_start = time.perf_counter()
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
            "kickoff_time": m.utc_date.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z") if m.utc_date else None,
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
            "live_minute":  m.live_minute,
        }
        for m in matches
    ]
    t_serialize_end = time.perf_counter()
    serialize_ms = int((t_serialize_end - t_serialize_start) * 1000)

    t_end = time.perf_counter()
    elapsed_ms = int((t_end - t_start) * 1000)

    logger.info(
        f"/fixtures completed in {elapsed_ms}ms "
        f"(query={query_ms}ms serialize={serialize_ms}ms)"
    )

    return {
        "status":      "success",
        "competition": comp.name,
        "count":       len(fixtures_out),
        "fixtures":    fixtures_out,
    }


@router.get("/debug/live-sync", summary="Debug: live sync state and current DB scores")
def debug_live_sync(db: Session = Depends(get_db)):
    """
    Temporary debug endpoint for verifying live score refresh pipeline.
    """
    from models import Match, Competition
    from services.live_sync_state import get_live_sync_state

    comp = db.query(Competition).filter_by(code="WC").first()
    live_matches = []
    if comp:
        live_rows = (
            db.query(Match)
            .filter(
                Match.competition_id == comp.id,
                Match.status.in_(["IN_PLAY", "PAUSED"]),
            )
            .order_by(Match.utc_date.asc())
            .all()
        )
        for m in live_rows:
            live_matches.append({
                "id": m.id,
                "api_id": m.api_id,
                "home_team": m.home_team.name if m.home_team else None,
                "away_team": m.away_team.name if m.away_team else None,
                "status": m.status,
                "home_score": m.home_score,
                "away_score": m.away_score,
                "live_minute": m.live_minute,
                "kickoff_time": m.utc_date.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z") if m.utc_date else None,
            })

    sync_state = get_live_sync_state()
    return {
        "status": "success",
        "sync_state": sync_state,
        "live_match_count": len(live_matches),
        "live_matches": live_matches,
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


@router.get("/fixtures-enriched", summary="Fixtures with pre-computed Poisson markets for all matches")
def get_fixtures_enriched(
    competition_code: str = Query("WC", description="Competition code"),
    limit: int = Query(200, ge=1, le=500, description="Max fixtures to return"),
    year: Optional[int] = Query(None, description="Filter by kickoff year, e.g. 2026"),
    show_historical: bool = Query(False, description="Include historical matches"),
    db: Session = Depends(get_db),
):
    """
    Returns fixtures with embedded Poisson-derived market data for every match.

    Enrichment is read from pre-computed Prediction rows (expected goals) or the
    in-memory cache populated by /predict-batch. ML inference is never run here.
    """
    from models import Match, Competition
    from sqlalchemy import extract
    from sqlalchemy.orm import joinedload, selectinload

    t_start = time.perf_counter()

    comp = db.query(Competition).filter_by(code=competition_code.upper()).first()
    if not comp:
        raise HTTPException(status_code=404, detail=f"Competition '{competition_code}' not found.")

    query = (
        db.query(Match)
        .options(joinedload(Match.home_team), joinedload(Match.away_team), selectinload(Match.predictions))
        .filter(Match.competition_id == comp.id)
    )

    if year:
        query = query.filter(extract("year", Match.utc_date) == year)
    elif not show_historical:
        query = query.filter(extract("year", Match.utc_date) >= 2026)

    from sqlalchemy import case
    m_year = extract("year", Match.utc_date)
    tier_case = case(
        (Match.status.in_({"IN_PLAY", "PAUSED"}), 0),
        ((m_year >= 2026) & (Match.status != "FINISHED"), 1),
        ((m_year >= 2026) & (Match.status == "FINISHED"), 2),
        else_=3,
    )
    asc_date  = case((tier_case.in_({0, 1}), Match.utc_date), else_=None)
    desc_date = case((tier_case.in_({2, 3}), Match.utc_date), else_=None)
    query = query.order_by(tier_case.asc(), asc_date.asc(), desc_date.desc())

    matches = query.limit(limit).all()
    t_query = time.perf_counter()
    query_time_ms = round((t_query - t_start) * 1000, 2)

    # ── Bulk-load injury/suspension data for all teams in fixture set ──────────
    # Collects all unique team IDs, then fires 4 queries total (no N+1).
    from models import Injury, Suspension
    from collections import defaultdict

    _team_ids: set = set()
    for _m in matches:
        if _m.home_team_id:
            _team_ids.add(_m.home_team_id)
        if _m.away_team_id:
            _team_ids.add(_m.away_team_id)

    _inj_map: dict  = defaultdict(list)   # team_id → ["Player (desc)", …]
    _susp_map: dict = defaultdict(list)   # team_id → ["Player (reason)", …]

    if _team_ids:
        for _i in db.query(Injury).filter(Injury.team_id.in_(_team_ids)).all():
            _desc = _i.injury_type or "Injured"
            _inj_map[_i.team_id].append(f"{_i.player_name} ({_desc})")
        for _s in db.query(Suspension).filter(Suspension.team_id.in_(_team_ids)).all():
            _reason = _s.suspension_reason or "Suspended"
            _susp_map[_s.team_id].append(f"{_s.player_name} ({_reason})")

    # Deduplicate while preserving order
    def _dedup(lst: list) -> list:
        return list(dict.fromkeys(lst))

    # ── Serialise helpers ──────────────────────────────────────────────────────
    def _team(t):
        if not t:
            return None
        return {
            "id":          t.id,
            "name":        t.name,
            "short_name":  t.short_name,
            "tla":         t.tla,
            "crest_url":   t.crest_url,
            "injuries":    _dedup(_inj_map.get(t.id, [])),
            "suspensions": _dedup(_susp_map.get(t.id, [])),
        }

    now_utc = datetime.now(timezone.utc)
    cache_now = time.time()
    live_statuses  = {"IN_PLAY", "PAUSED"}
    score_statuses = live_statuses | {"FINISHED"}

    fixtures_out = []
    errors = 0

    for m in matches:
        # ── Base fixture fields ───────────────────────────────────────────────
        kt = m.utc_date.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z") if m.utc_date else None

        home_t = m.home_team
        away_t = m.away_team

        live_score = None
        if m.status in score_statuses and m.home_score is not None and m.away_score is not None:
            live_score = {"home": m.home_score, "away": m.away_score, "is_live": m.status in live_statuses}

        stored_pred = m.predictions[0] if m.predictions else None
        fixture_pred = None
        if stored_pred:
            fixture_pred = {
                "predicted_outcome":  stored_pred.predicted_outcome,
                "home_probability":   stored_pred.home_probability,
                "away_probability":   stored_pred.away_probability,
                "draw_probability":   stored_pred.draw_probability,
            }

        # ── Compute enrichment ────────────────────────────────────────────────
        enrichment = None
        if home_t and away_t:
            try:
                if m.status == "FINISHED" and m.home_score is not None and m.away_score is not None:
                    h_xg = float(m.home_score)
                    a_xg = float(m.away_score)
                    enrichment = _build_enrichment_from_xg(
                        h_xg,
                        a_xg,
                        most_likely_score=f"{m.home_score}-{m.away_score}",
                    )
                elif (
                    stored_pred
                    and stored_pred.expected_home_goals is not None
                    and stored_pred.expected_away_goals is not None
                ):
                    enrichment = _build_enrichment_from_xg(
                        float(stored_pred.expected_home_goals),
                        float(stored_pred.expected_away_goals),
                    )
                else:
                    enrichment = _lookup_cached_enrichment(
                        m.id,
                        home_t.name,
                        away_t.name,
                        competition_code,
                        cache_now,
                    )
            except Exception as exc:
                logger.warning(f"[fixtures-enriched] enrichment failed for match {m.id}: {exc}")
                errors += 1

        fixture = {
            "id":            m.id,
            "kickoff_time":  kt,
            "status":        m.status,
            "stage":         m.stage,
            "group":         m.group,
            "venue":         home_t.venue if home_t else None,
            "competition":   comp.name,
            "home_team":     _team(home_t),
            "away_team":     _team(away_t),
            "live_score":    live_score,
            "winner":        m.winner,
            "live_minute":   m.live_minute,
            "prediction":    fixture_pred,
            "enrichment":    enrichment,  # null if teams unknown
        }
        fixtures_out.append(fixture)

    t_end = time.perf_counter()
    enrichment_time_ms = round((t_end - t_query) * 1000, 2)
    total_time_ms = round((t_end - t_start) * 1000, 2)

    logger.info(
        f"GET /fixtures-enriched  {len(fixtures_out)} fixtures in {total_time_ms}ms "
        f"(Query={query_time_ms}ms, Enrichment={enrichment_time_ms}ms, Errors={errors})"
    )

    return {
        "status":      "success",
        "competition": comp.name,
        "count":       len(fixtures_out),
        "elapsed_ms":  int(total_time_ms),
        "fixtures":    fixtures_out,
    }

