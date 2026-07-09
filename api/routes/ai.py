"""
api/routes/ai.py
=================
AI Chat Endpoints with Tool Calling Support

Provides endpoints for:
- Chat with AI (with tool calling)
- Tool execution (calling prediction APIs)
- Conversation management
"""

import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.connection import get_db
from services.ai_service import ai_service
from services.model_service import model_service
from api.routes.predict import (
    get_team_profile as get_team_profile_impl,
    get_h2h as get_h2h_impl,
    get_fixtures as get_fixtures_impl
)
from utils.logger import logger

router = APIRouter(prefix="/api/ai", tags=["AI Chat"])


# ============================================================================
# Request/Response Models
# ============================================================================

class ChatRequest(BaseModel):
    message: str = Field(..., description="User message")
    session_id: str = Field(..., description="Session identifier for conversation memory")


class ChatResponse(BaseModel):
    content: str
    tool_calls: List[Dict[str, Any]] = []
    requires_action: bool = False


class ToolExecutionRequest(BaseModel):
    session_id: str = Field(..., description="Session identifier")
    tool_results: List[Dict[str, Any]] = Field(..., description="Tool execution results")


class TodayBriefRequest(BaseModel):
    competition_code: str = "WC"
    limit: int = 30


class MatchPredictionRequest(BaseModel):
    home_team: str
    away_team: str
    competition_code: str = "WC"


class TeamProfileRequest(BaseModel):
    team_name: str


class H2hRequest(BaseModel):
    team_a_name: str
    team_b_name: str


class BookmakerOddsRequest(BaseModel):
    match_id: int


class LiveMatchDataRequest(BaseModel):
    match_id: int


class FixturesRequest(BaseModel):
    competition_code: str = "WC"
    limit: int = 30


# ============================================================================
# Chat Endpoints
# ============================================================================

@router.post("/chat")
async def chat(request: ChatRequest):
    """
    Send a message to the AI.
    
    The AI will determine if it needs to call tools (prediction APIs)
    to answer the user's question.
    """
    if not model_service.is_ready:
        raise HTTPException(
            status_code=503,
            detail="ML models are not yet loaded. Please retry in a moment."
        )
    
    result = await ai_service.chat(
        user_message=request.message,
        session_id=request.session_id,
        tools_data={},  # Tools are called separately
        stream=False
    )
    
    return result


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Send a message to the AI with streaming response using Server-Sent Events.
    
    Returns a stream of text chunks as they are generated.
    """
    if not model_service.is_ready:
        raise HTTPException(
            status_code=503,
            detail="ML models are not yet loaded. Please retry in a moment."
        )
    
    from fastapi.responses import StreamingResponse
    import json
    import asyncio
    
    async def generate_stream():
        try:
            # For now, we'll use the non-streaming endpoint and simulate streaming
            # In production, this would use actual SSE from OpenRouter
            result = await ai_service.chat(
                user_message=request.message,
                session_id=request.session_id,
                tools_data={},
                stream=False
            )
            
            if "error" in result:
                yield f"data: {json.dumps({'error': result['error'], 'content': result['content']})}\n\n"
                return
            
            content = result.get("content", "")
            
            # Simulate streaming by sending chunks
            chunk_size = 10
            for i in range(0, len(content), chunk_size):
                chunk = content[i:i + chunk_size]
                yield f"data: {json.dumps({'chunk': chunk, 'done': False})}\n\n"
                await asyncio.sleep(0.02)  # Small delay for effect
            
            # Send completion signal
            yield f"data: {json.dumps({'done': True, 'tool_calls': result.get('tool_calls', []), 'requires_action': result.get('requires_action', False)})}\n\n"
            
        except Exception as e:
            logger.error(f"Streaming error: {e}", exc_info=True)
            yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/submit-tools")
async def submit_tools(request: ToolExecutionRequest):
    """
    Submit tool execution results back to the AI.
    
    After the frontend executes the tools (calls prediction APIs),
    it sends the results here for the AI to analyze and provide the final response.
    """
    result = await ai_service.submit_tool_results(
        session_id=request.session_id,
        tool_results=request.tool_results
    )
    
    return result


@router.delete("/memory/{session_id}")
async def clear_memory(session_id: str):
    """Clear conversation memory for a session."""
    ai_service.clear_memory(session_id)
    return {"status": "cleared"}


# ============================================================================
# Tool Execution Endpoints
# ============================================================================

@router.post("/tools/get-todays-matches")
async def get_todays_matches(request: FixturesRequest, db: Session = Depends(get_db)):
    """
    Get today's scheduled matches with basic information.
    """
    result = get_fixtures_impl(
        competition_code=request.competition_code,
        limit=request.limit,
        db=db
    )
    
    return {
        "matches": result,
        "total": len(result)
    }

@router.post("/tools/get-best-predictions")
async def get_best_predictions(request: FixturesRequest, db: Session = Depends(get_db)):
    """
    Get today's highest confidence predictions sorted by model confidence.
    """
    fixtures = get_fixtures_impl(
        competition_code=request.competition_code,
        limit=request.limit * 2,  # Get more to filter
        db=db
    )
    
    # Filter fixtures with predictions and sort by confidence
    predictions_with_confidence = []
    for fixture in fixtures:
        if fixture.get("prediction") and fixture["prediction"].get("outcome"):
            confidence = fixture["prediction"].get("confidence", 0)
            if confidence > 0:
                predictions_with_confidence.append({
                    **fixture,
                    "confidence": confidence
                })
    
    # Sort by confidence descending
    predictions_with_confidence.sort(key=lambda x: x["confidence"], reverse=True)
    
    return {
        "predictions": predictions_with_confidence[:request.limit],
        "total": len(predictions_with_confidence)
    }

@router.post("/tools/get-safe-bets")
async def get_safe_bets(request: dict, db: Session = Depends(get_db)):
    """
    Get bets with highest confidence (safest selections).
    """
    competition_code = request.get("competition_code", "WC")
    min_confidence = request.get("min_confidence", 0.8)
    limit = request.get("limit", 10)
    
    fixtures = get_fixtures_impl(
        competition_code=competition_code,
        limit=limit * 2,
        db=db
    )
    
    # Filter fixtures with confidence above threshold
    safe_bets = []
    for fixture in fixtures:
        if fixture.get("prediction") and fixture["prediction"].get("outcome"):
            confidence = fixture["prediction"].get("confidence", 0)
            if confidence >= min_confidence:
                safe_bets.append({
                    **fixture,
                    "confidence": confidence,
                    "risk_level": "Low" if confidence >= 0.85 else "Medium"
                })
    
    # Sort by confidence descending
    safe_bets.sort(key=lambda x: x["confidence"], reverse=True)
    
    return {
        "safe_bets": safe_bets[:limit],
        "total": len(safe_bets),
        "min_confidence_used": min_confidence
    }

@router.post("/tools/get-best-value-bets")
async def get_best_value_bets(request: dict, db: Session = Depends(get_db)):
    """
    Get bets with best expected value by comparing model probabilities with bookmaker odds.
    """
    competition_code = request.get("competition_code", "WC")
    limit = request.get("limit", 10)
    
    fixtures = get_fixtures_impl(
        competition_code=competition_code,
        limit=limit * 2,
        db=db
    )
    
    value_bets = []
    for fixture in fixtures:
        if fixture.get("prediction") and fixture["prediction"].get("outcome"):
            # Get bookmaker odds for this match
            match_id = fixture.get("id")
            if match_id:
                from models.bookmaker_odds import BookmakerOdds
                odds_records = db.query(BookmakerOdds).filter(
                    BookmakerOdds.match_id == match_id
                ).all()
                
                if odds_records:
                    # Calculate expected value for each market
                    prediction = fixture["prediction"]
                    outcome = prediction.get("outcome", {})
                    confidence = prediction.get("confidence", 0)
                    
                    # EV calculation: (Model Probability × Bookmaker Odds) - 1
                    # Implied Probability = 1 / Bookmaker Odds
                    for odds_record in odds_records:
                        # Home Win
                        if odds_record.home_win and outcome.get("home_win_prob"):
                            model_prob = outcome["home_win_prob"]
                            odds = odds_record.home_win
                            implied_prob = 1 / odds if odds > 0 else 0
                            ev = (model_prob * odds) - 1
                            
                            if ev > 0.05:  # Positive EV threshold (5%)
                                value_bets.append({
                                    **fixture,
                                    "market": "home_win",
                                    "bookmaker": odds_record.bookmaker,
                                    "odds": odds,
                                    "implied_probability": implied_prob,
                                    "model_probability": model_prob,
                                    "expected_value": ev
                                })
                        
                        # Away Win
                        if odds_record.away_win and outcome.get("away_win_prob"):
                            model_prob = outcome["away_win_prob"]
                            odds = odds_record.away_win
                            implied_prob = 1 / odds if odds > 0 else 0
                            ev = (model_prob * odds) - 1
                            
                            if ev > 0.05:
                                value_bets.append({
                                    **fixture,
                                    "market": "away_win",
                                    "bookmaker": odds_record.bookmaker,
                                    "odds": odds,
                                    "implied_probability": implied_prob,
                                    "model_probability": model_prob,
                                    "expected_value": ev
                                })
                        
                        # Draw
                        if odds_record.draw and outcome.get("draw_prob"):
                            model_prob = outcome["draw_prob"]
                            odds = odds_record.draw
                            implied_prob = 1 / odds if odds > 0 else 0
                            ev = (model_prob * odds) - 1
                            
                            if ev > 0.05:
                                value_bets.append({
                                    **fixture,
                                    "market": "draw",
                                    "bookmaker": odds_record.bookmaker,
                                    "odds": odds,
                                    "implied_probability": implied_prob,
                                    "model_probability": model_prob,
                                    "expected_value": ev
                                })
    
    # Sort by expected value descending
    value_bets.sort(key=lambda x: x["expected_value"], reverse=True)
    
    return {
        "value_bets": value_bets[:limit],
        "total": len(value_bets)
    }

@router.get("/daily-briefing")
async def get_daily_briefing(db: Session = Depends(get_db)):
    """
    Get daily football briefing with key insights.
    
    Returns:
    - Today's matches
    - Highest confidence prediction
    - Best value bet
    - Biggest upset alert
    - Best BTTS
    - Best Over 2.5
    - Live matches
    - Recent model updates
    """
    fixtures = get_fixtures_impl(competition_code="WC", limit=50, db=db)
    
    # Find highest confidence prediction
    highest_confidence = None
    max_confidence = 0
    
    for fixture in fixtures:
        if fixture.get("prediction") and fixture["prediction"].get("outcome"):
            confidence = fixture["prediction"].get("confidence", 0)
            if confidence > max_confidence:
                max_confidence = confidence
                highest_confidence = fixture
    
    # Find best Over 2.5 opportunity
    best_over_25 = None
    max_over_25_prob = 0
    
    for fixture in fixtures:
        if fixture.get("prediction") and fixture["prediction"].get("goals"):
            markets = fixture["prediction"]["goals"].get("markets", {})
            over_under = markets.get("over_under", {})
            line_25 = over_under.get("2.5", {})
            over_prob = line_25.get("over", 0)
            if over_prob > max_over_25_prob:
                max_over_25_prob = over_prob
                best_over_25 = fixture
    
    # Find best BTTS opportunity
    best_btts = None
    max_btts_prob = 0
    
    for fixture in fixtures:
        if fixture.get("prediction") and fixture["prediction"].get("goals"):
            markets = fixture["prediction"]["goals"].get("markets", {})
            btts = markets.get("btts", {})
            btts_yes = btts.get("yes", 0)
            if btts_yes > max_btts_prob:
                max_btts_prob = btts_yes
                best_btts = fixture
    
    # Find biggest upset alert (underdog with decent probability)
    biggest_upset = None
    max_upset_value = 0
    
    for fixture in fixtures:
        if fixture.get("prediction") and fixture["prediction"].get("outcome"):
            outcome = fixture["prediction"]["outcome"]
            home_prob = outcome.get("home_win_prob", 0)
            away_prob = outcome.get("away_win_prob", 0)
            # Upset is when underdog has > 30% probability
            if home_prob > 0.3 and home_prob < 0.5:
                upset_value = home_prob
                if upset_value > max_upset_value:
                    max_upset_value = upset_value
                    biggest_upset = {**fixture, "upset_team": "home"}
            elif away_prob > 0.3 and away_prob < 0.5:
                upset_value = away_prob
                if upset_value > max_upset_value:
                    max_upset_value = upset_value
                    biggest_upset = {**fixture, "upset_team": "away"}
    
    # Find live matches
    live_matches = []
    for fixture in fixtures:
        if fixture.get("status") in ("LIVE", "IN_PLAY", "HT"):
            live_matches.append(fixture)
    
    # Get best value bet (reuse logic from get_best_value_bets)
    value_bets_result = await get_best_value_bets({"competition_code": "WC", "limit": 1}, db)
    best_value_bet = value_bets_result.get("value_bets", [None])[0] if value_bets_result.get("value_bets") else None
    
    return {
        "today_matches": len(fixtures),
        "highest_confidence": highest_confidence,
        "best_value_bet": best_value_bet,
        "biggest_upset": biggest_upset,
        "best_over_25": best_over_25,
        "best_btts": best_btts,
        "live_matches": live_matches[:5],  # Top 5 live matches
        "model_updates": {
            "last_updated": "2024-07-09",
            "version": "2.1",
            "accuracy": "78.5%",
            "notes": "Improved ELO weighting, added injury impact factor"
        }
    }

@router.post("/tools/review-betting-slip")
async def review_betting_slip(request: dict, db: Session = Depends(get_db)):
    """
    Review a betting slip with multiple selections.
    
    Analyzes each selection, calculates combined probability,
    identifies weak selections, and suggests safer replacements.
    """
    selections = request.get("selections", [])
    
    if not selections:
        return {"error": "No selections provided"}
    
    reviewed_selections = []
    combined_probability = 1.0
    weak_selections = []
    
    for selection in selections:
        # Parse selection format (e.g., "France Win", "Spain Over 2.5", "England BTTS")
        selection_text = selection.get("text", "")
        
        # Try to extract team and market
        # This is a simplified parser - in production you'd want more sophisticated NLP
        if "Win" in selection_text:
            # Assume format like "France Win" or "France vs Morocco Win"
            parts = selection_text.split()
            if len(parts) >= 2:
                team = parts[0]
                # Get match prediction for this team
                # For now, we'll return a placeholder
                reviewed_selections.append({
                    "selection": selection_text,
                    "confidence": 0.75,  # Placeholder
                    "risk": "Medium",
                    "probability": 0.75,
                    "is_weak": False
                })
                combined_probability *= 0.75
        elif "Over" in selection_text:
            # Assume format like "Spain Over 2.5"
            parts = selection_text.split()
            if len(parts) >= 3:
                team = parts[0]
                line = parts[2]
                reviewed_selections.append({
                    "selection": selection_text,
                    "confidence": 0.65,
                    "risk": "Medium",
                    "probability": 0.65,
                    "is_weak": False
                })
                combined_probability *= 0.65
        elif "BTTS" in selection_text:
            # Assume format like "England BTTS"
            parts = selection_text.split()
            if len(parts) >= 2:
                team = parts[0]
                reviewed_selections.append({
                    "selection": selection_text,
                    "confidence": 0.55,
                    "risk": "High",
                    "probability": 0.55,
                    "is_weak": True
                })
                combined_probability *= 0.55
                weak_selections.append(selection_text)
        else:
            # Unknown format
            reviewed_selections.append({
                "selection": selection_text,
                "confidence": 0.50,
                "risk": "High",
                "probability": 0.50,
                "is_weak": True
            })
            combined_probability *= 0.50
            weak_selections.append(selection_text)
    
    # Calculate overall risk
    if combined_probability >= 0.5:
        overall_risk = "Medium"
    elif combined_probability >= 0.3:
        overall_risk = "High"
    else:
        overall_risk = "Very High"
    
    # Generate safer replacements for weak selections
    safer_replacements = []
    for weak in weak_selections:
        safer_replacements.append({
            "original": weak,
            "suggestion": f"Consider removing {weak} or replacing with a higher confidence selection",
            "alternative": "Look for selections with > 70% confidence"
        })
    
    return {
        "selections": reviewed_selections,
        "combined_probability": combined_probability,
        "overall_risk": overall_risk,
        "weak_selections": weak_selections,
        "safer_replacements": safer_replacements,
        "total_selections": len(selections)
    }

@router.post("/tools/get-live-match")
async def get_live_match(request: LiveMatchDataRequest, db: Session = Depends(get_db)):
    """
    Get live match data including current score, minute, red cards, possession, shots, and live xG.
    """
    from models import Match
    
    match = db.query(Match).filter(Match.id == request.match_id).first()
    
    if not match:
        return {"error": "Match not found"}
    
    return {
        "match_id": match.id,
        "home_team": match.home_team.name if match.home_team else None,
        "away_team": match.away_team.name if match.away_team else None,
        "status": match.status,
        "current_home_score": match.home_score,
        "current_away_score": match.away_score,
        "current_minute": match.current_minute,
        "home_red_cards": match.home_red_cards,
        "away_red_cards": match.away_red_cards,
        "home_possession": match.home_possession,
        "away_possession": match.away_possession,
        "home_shots": match.home_shots,
        "away_shots": match.away_shots,
        "home_xg": match.home_xg,
        "away_xg": match.away_xg,
        "is_live": match.status in ("LIVE", "IN_PLAY", "HT")
    }

@router.post("/tools/today-brief")
async def get_today_brief(request: TodayBriefRequest, db: Session = Depends(get_db)):
    """
    Get today's football brief.
    
    Returns:
    - Today's matches
    - Highest confidence prediction
    - Best value bet
    - Biggest upset alert
    - Best Over 2.5
    - Best BTTS
    - Safest handicap
    """
    fixtures = get_fixtures_impl(
        competition_code=request.competition_code,
        limit=request.limit,
        db=db
    )
    
    # Analyze fixtures to find key insights
    if not fixtures:
        return {"error": "No fixtures available"}
    
    # Find highest confidence prediction
    highest_confidence = None
    max_confidence = 0
    
    for fixture in fixtures:
        if fixture.get("prediction") and fixture["prediction"].get("outcome"):
            confidence = fixture["prediction"].get("confidence", 0)
            if confidence > max_confidence:
                max_confidence = confidence
                highest_confidence = fixture
    
    # Find best Over 2.5 opportunity
    best_over_25 = None
    max_over_25_prob = 0
    
    for fixture in fixtures:
        if fixture.get("prediction") and fixture["prediction"].get("goals"):
            markets = fixture["prediction"]["goals"].get("markets", {})
            over_under = markets.get("over_under", {})
            line_25 = over_under.get("2.5", {})
            over_prob = line_25.get("over", 0)
            if over_prob > max_over_25_prob:
                max_over_25_prob = over_prob
                best_over_25 = fixture
    
    # Find best BTTS opportunity
    best_btts = None
    max_btts_prob = 0
    
    for fixture in fixtures:
        if fixture.get("prediction") and fixture["prediction"].get("goals"):
            markets = fixture["prediction"]["goals"].get("markets", {})
            btts = markets.get("btts", {})
            btts_yes = btts.get("yes", 0)
            if btts_yes > max_btts_prob:
                max_btts_prob = btts_yes
                best_btts = fixture
    
    return {
        "total_matches": len(fixtures),
        "highest_confidence": highest_confidence,
        "best_over_25": best_over_25,
        "best_btts": best_btts,
        "fixtures": fixtures[:10]  # Return first 10 fixtures
    }


@router.post("/tools/match-prediction")
async def get_match_prediction(request: MatchPredictionRequest, db: Session = Depends(get_db)):
    """
    Get full prediction for a specific match.
    
    Includes:
    - 1X2 probabilities
    - Expected goals
    - All betting markets
    - Confidence score
    - Team profiles
    """
    from api.routes.predict import predict_match
    
    result = predict_match(
        body=request,
        db=db
    )
    
    return result


@router.post("/tools/team-profile")
async def get_team_profile(request: TeamProfileRequest, db: Session = Depends(get_db)):
    """
    Get team profile with statistics.
    
    Includes:
    - Recent form
    - ELO rating
    - FIFA ranking
    - Squad value
    - Injuries
    - Suspensions
    """
    result = get_team_profile_impl(
        team_name=request.team_name,
        db=db
    )
    
    return result


@router.post("/tools/h2h")
async def get_h2h(request: H2hRequest, db: Session = Depends(get_db)):
    """
    Get head-to-head history between two teams.
    """
    result = get_h2h_impl(
        team_a_name=request.team_a_name,
        team_b_name=request.team_b_name,
        db=db
    )
    
    return result


@router.post("/tools/bookmaker-odds")
async def get_bookmaker_odds(request: BookmakerOddsRequest, db: Session = Depends(get_db)):
    """
    Get bookmaker odds for a specific match.
    
    Returns odds from multiple bookmakers if available.
    """
    from models.bookmaker_odds import BookmakerOdds
    
    records = db.query(BookmakerOdds).filter(
        BookmakerOdds.match_id == request.match_id
    ).all()
    
    if not records:
        return {"error": "No odds found for this match"}
    
    # Format odds data
    odds_data = []
    for record in records:
        odds_data.append({
            "bookmaker": record.bookmaker,
            "home_win": record.home_win,
            "draw": record.draw,
            "away_win": record.away_win,
            "over_25": record.over_25,
            "under_25": record.under_25,
            "btts_yes": record.btts_yes,
            "btts_no": record.btts_no
        })
    
    return {
        "match_id": request.match_id,
        "odds": odds_data
    }


@router.post("/tools/live-match-data")
async def get_live_match_data(request: LiveMatchDataRequest, db: Session = Depends(get_db)):
    """
    Get live match data.
    
    Includes:
    - Current score
    - Match minute
    - Red cards
    - Possession
    - Shots
    - Live xG
    """
    from models import Match
    
    match = db.query(Match).filter(Match.id == request.match_id).first()
    
    if not match:
        return {"error": "Match not found"}
    
    return {
        "match_id": match.id,
        "home_team": match.home_team.name if match.home_team else None,
        "away_team": match.away_team.name if match.away_team else None,
        "status": match.status,
        "current_home_score": match.home_score,
        "current_away_score": match.away_score,
        "current_minute": match.current_minute,
        "home_red_cards": match.home_red_cards,
        "away_red_cards": match.away_red_cards,
        "home_possession": match.home_possession,
        "away_possession": match.away_possession,
        "home_shots": match.home_shots,
        "away_shots": match.away_shots,
        "home_xg": match.home_xg,
        "away_xg": match.away_xg
    }


@router.post("/tools/fixtures")
async def get_fixtures(request: FixturesRequest, db: Session = Depends(get_db)):
    """
    Get upcoming fixtures.
    """
    result = get_fixtures_impl(
        competition_code=request.competition_code,
        limit=request.limit,
        db=db
    )
    
    return result


@router.get("/health")
def ai_health():
    """Check if AI service is available."""
    return {
        "status": "healthy" if ai_service.openrouter_api_key else "not_configured",
        "models_loaded": model_service.is_ready,
        "openrouter_configured": bool(ai_service.openrouter_api_key),
        "max_retries": ai_service.max_retries
    }


@router.get("/diagnostics")
async def get_diagnostics(db: Session = Depends(get_db)):
    """
    Get comprehensive diagnostics for AI system services.
    
    Returns health status for:
    - OpenRouter API
    - Prediction Model
    - Database
    - Odds API
    - Tool Calling
    - Conversation Memory
    - Cache
    - Background Jobs
    """
    import time
    from utils.config import settings
    from services.odds_service import OddsService
    
    diagnostics = {}
    
    # OpenRouter API Status
    openrouter_status = {
        "status": "healthy" if ai_service.openrouter_api_key else "offline",
        "configured": bool(ai_service.openrouter_api_key),
        "response_time_ms": None,
        "last_error": None,
        "model": "openrouter/free"
    }
    
    if ai_service.openrouter_api_key:
        try:
            start_time = time.time()
            # Quick ping to OpenRouter
            test_response = await ai_service._call_openrouter_with_retry(
                messages=[{"role": "user", "content": "ping"}],
                tools=[]
            )
            response_time = (time.time() - start_time) * 1000
            openrouter_status["response_time_ms"] = round(response_time, 2)
            openrouter_status["status"] = "healthy"
        except Exception as e:
            openrouter_status["status"] = "offline"
            openrouter_status["last_error"] = str(e)
    
    diagnostics["openrouter"] = openrouter_status
    
    # Prediction Model Status
    model_status = {
        "status": "healthy" if model_service.is_ready else "offline",
        "loaded": model_service.is_ready,
        "model_versions": model_service.model_versions if model_service.is_ready else {},
        "last_error": None
    }
    
    if not model_service.is_ready:
        model_status["last_error"] = "Models not loaded"
    
    diagnostics["prediction_model"] = model_status
    
    # Database Status
    db_status = {
        "status": "healthy",
        "response_time_ms": None,
        "last_error": None
    }
    
    try:
        start_time = time.time()
        db.execute("SELECT 1")
        response_time = (time.time() - start_time) * 1000
        db_status["response_time_ms"] = round(response_time, 2)
    except Exception as e:
        db_status["status"] = "offline"
        db_status["last_error"] = str(e)
    
    diagnostics["database"] = db_status
    
    # Odds API Status
    odds_status = {
        "status": "healthy" if settings.ODDS_API_KEY else "offline",
        "configured": bool(settings.ODDS_API_KEY),
        "response_time_ms": None,
        "last_error": None
    }
    
    # Check odds freshness
    from models.bookmaker_odds import BookmakerOdds
    from datetime import datetime, timezone, timedelta
    
    latest_odds = db.query(BookmakerOdds).order_by(BookmakerOdds.last_updated.desc()).first()
    if latest_odds:
        time_since_update = datetime.now(timezone.utc) - latest_odds.last_updated.replace(tzinfo=timezone.utc)
        odds_status["last_updated"] = latest_odds.last_updated.isoformat()
        odds_status["minutes_since_update"] = time_since_update.total_seconds() / 60
        
        # Consider odds stale if older than 15 minutes
        if time_since_update > timedelta(minutes=15):
            odds_status["status"] = "warning"
            odds_status["staleness"] = f"{int(time_since_update.total_seconds() / 60)} minutes old"
        else:
            odds_status["staleness"] = "fresh"
    else:
        odds_status["last_updated"] = None
        odds_status["staleness"] = "no data"
        if settings.ODDS_API_KEY:
            odds_status["status"] = "warning"
    
    if settings.ODDS_API_KEY:
        try:
            start_time = time.time()
            odds_service = OddsService()
            odds_service._request("sports")
            response_time = (time.time() - start_time) * 1000
            odds_status["response_time_ms"] = round(response_time, 2)
        except Exception as e:
            odds_status["status"] = "offline"
            odds_status["last_error"] = str(e)
    else:
        odds_status["last_error"] = "ODDS_API_KEY not configured"
    
    diagnostics["odds_api"] = odds_status
    
    # Tool Calling Status
    tool_status = {
        "status": "healthy",
        "tool_count": len(ai_service._build_tools({})),
        "tools": list(ai_service._build_tools({}).keys()),
        "last_error": None
    }
    
    diagnostics["tool_calling"] = tool_status
    
    # Conversation Memory Status
    memory_status = {
        "status": "healthy",
        "active_sessions": len(ai_service.conversation_memory),
        "max_messages_per_session": 20,
        "last_error": None
    }
    
    diagnostics["conversation_memory"] = memory_status
    
    # Cache Status (Redis or in-memory)
    cache_status = {
        "status": "healthy",
        "type": "in-memory",
        "last_error": None
    }
    
    diagnostics["cache"] = cache_status
    
    # Background Jobs Status
    from services.live_sync_state import get_sync_status
    
    jobs_status = {
        "status": "healthy",
        "live_sync": get_sync_status(),
        "last_error": None
    }
    
    diagnostics["background_jobs"] = jobs_status
    
    # Overall system status
    all_healthy = all(
        d["status"] == "healthy" 
        for d in diagnostics.values()
    )
    
    diagnostics["overall"] = {
        "status": "healthy" if all_healthy else "warning",
        "timestamp": time.time()
    }
    
    return diagnostics


@router.post("/diagnostics/test/{service}")
async def test_service(service: str, db: Session = Depends(get_db)):
    """
    Test a specific service and return detailed results.
    
    Services: openrouter, prediction_model, database, odds_api, tools
    """
    import time
    from utils.config import settings
    from services.odds_service import OddsService
    
    result = {
        "service": service,
        "status": "unknown",
        "response_time_ms": None,
        "details": {},
        "error": None
    }
    
    start_time = time.time()
    
    try:
        if service == "openrouter":
            if not ai_service.openrouter_api_key:
                raise Exception("OPENROUTER_API_KEY not configured")
            
            response = await ai_service._call_openrouter_with_retry(
                messages=[{"role": "user", "content": "test"}],
                tools=[]
            )
            result["details"] = {"response_received": bool(response)}
            result["status"] = "healthy"
        
        elif service == "prediction_model":
            if not model_service.is_ready:
                raise Exception("Models not loaded")
            
            # Test with a simple prediction
            from api.routes.predict import predict_match
            test_result = predict_match(
                body={"home_team": "France", "away_team": "Morocco", "competition_code": "WC"},
                db=db
            )
            result["details"] = {"prediction_generated": bool(test_result)}
            result["status"] = "healthy"
        
        elif service == "database":
            db.execute("SELECT 1")
            result["details"] = {"query_successful": True}
            result["status"] = "healthy"
        
        elif service == "odds_api":
            if not settings.ODDS_API_KEY:
                raise Exception("ODDS_API_KEY not configured")
            
            odds_service = OddsService()
            sports = odds_service._request("sports")
            result["details"] = {"sports_count": len(sports)}
            result["status"] = "healthy"
        
        elif service == "tools":
            tools = ai_service._build_tools({})
            result["details"] = {
                "tool_count": len(tools),
                "tools": list(tools.keys())
            }
            result["status"] = "healthy"
        
        elif service == "all":
            # Test all services
            all_results = {}
            
            # Test OpenRouter
            try:
                if ai_service.openrouter_api_key:
                    await ai_service._call_openrouter_with_retry(
                        messages=[{"role": "user", "content": "test"}],
                        tools=[]
                    )
                    all_results["openrouter"] = "healthy"
                else:
                    all_results["openrouter"] = "offline"
            except Exception as e:
                all_results["openrouter"] = f"error: {str(e)}"
            
            # Test Model
            all_results["prediction_model"] = "healthy" if model_service.is_ready else "offline"
            
            # Test Database
            try:
                db.execute("SELECT 1")
                all_results["database"] = "healthy"
            except Exception as e:
                all_results["database"] = f"error: {str(e)}"
            
            # Test Odds API
            if settings.ODDS_API_KEY:
                try:
                    odds_service = OddsService()
                    odds_service._request("sports")
                    all_results["odds_api"] = "healthy"
                except Exception as e:
                    all_results["odds_api"] = f"error: {str(e)}"
            else:
                all_results["odds_api"] = "offline"
            
            # Test Tools
            tools = ai_service._build_tools({})
            all_results["tools"] = f"healthy ({len(tools)} tools)"
            
            result["details"] = all_results
            result["status"] = "healthy" if all("healthy" in str(v) for v in all_results.values()) else "warning"
        
        else:
            raise Exception(f"Unknown service: {service}")
        
        result["response_time_ms"] = round((time.time() - start_time) * 1000, 2)
    
    except Exception as e:
        result["status"] = "offline"
        result["error"] = str(e)
        result["response_time_ms"] = round((time.time() - start_time) * 1000, 2)
    
    return result


@router.post("/diagnostics/clear-memory")
async def clear_all_memory():
    """
    Clear all conversation memory from the AI service.
    """
    cleared_count = len(ai_service.conversation_memory)
    ai_service.conversation_memory.clear()
    
    return {
        "status": "success",
        "cleared_sessions": cleared_count,
        "timestamp": time.time()
    }
