from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from database.connection import get_db
from models import Match, MatchStatistic, MatchEvent, MatchLineup, PlayerMatchPerformance, Suspension, SuspensionHistory

router = APIRouter(prefix="/api/matches", tags=["SofaScore Match Data"])


@router.get("/{match_id}/statistics", response_model=Dict[str, Any])
def get_match_statistics(match_id: int, db: Session = Depends(get_db)):
    """
    Get match statistics for a specific match
    """
    statistics = db.query(MatchStatistic).filter_by(match_id=match_id).first()
    if not statistics:
        raise HTTPException(status_code=404, detail="Match statistics not found")
    return {
        "status": "success",
        "data": {
            "id": statistics.id,
            "match_id": statistics.match_id,
            "home_possession": statistics.home_possession,
            "away_possession": statistics.away_possession,
            "home_shots": statistics.home_shots,
            "away_shots": statistics.away_shots,
            "home_shots_on_target": statistics.home_shots_on_target,
            "away_shots_on_target": statistics.away_shots_on_target,
            "home_corners": statistics.home_corners,
            "away_corners": statistics.away_corners,
            "home_expected_goals": statistics.home_expected_goals,
            "away_expected_goals": statistics.away_expected_goals,
            "home_fouls": statistics.home_fouls,
            "away_fouls": statistics.away_fouls,
            "home_offsides": statistics.home_offsides,
            "away_offsides": statistics.away_offsides
        }
    }


@router.get("/{match_id}/events", response_model=Dict[str, Any])
def get_match_events(match_id: int, db: Session = Depends(get_db)):
    """
    Get match events (goals, cards, substitutions) for a specific match
    """
    events = db.query(MatchEvent).filter_by(match_id=match_id).order_by(MatchEvent.minute).all()
    return {
        "status": "success",
        "count": len(events),
        "data": [
            {
                "id": event.id,
                "type": event.type,
                "minute": event.minute,
                "extra_minute": event.extra_minute,
                "description": event.description,
                "player_name": event.player_name,
                "team_id": event.team_id
            }
            for event in events
        ]
    }


@router.get("/{match_id}/lineups", response_model=Dict[str, Any])
def get_match_lineups(match_id: int, db: Session = Depends(get_db)):
    """
    Get match lineups and formations for a specific match
    """
    lineups = db.query(MatchLineup).filter_by(match_id=match_id).all()
    return {
        "status": "success",
        "count": len(lineups),
        "data": [
            {
                "id": lineup.id,
                "team_id": lineup.team_id,
                "formation": lineup.formation,
                "starting_xi": lineup.starting_xi,
                "substitutes": lineup.substitutes,
                "coach_name": lineup.coach_name
            }
            for lineup in lineups
        ]
    }


@router.get("/{match_id}/player-ratings", response_model=Dict[str, Any])
def get_player_ratings(match_id: int, db: Session = Depends(get_db)):
    """
    Get player ratings and performance data for a specific match
    """
    performances = db.query(PlayerMatchPerformance).filter_by(match_id=match_id).all()
    return {
        "status": "success",
        "count": len(performances),
        "data": [
            {
                "id": perf.id,
                "team_id": perf.team_id,
                "player_id": perf.player_id,
                "player_name": perf.player_name,
                "rating": perf.rating,
                "sofa_score_rating": perf.sofa_score_rating,
                "position": perf.position,
                "is_starter": perf.is_starter,
                "minutes_played": perf.minutes_played,
                "goals": perf.goals,
                "assists": perf.assists,
                "shots": perf.shots,
                "shots_on_target": perf.shots_on_target,
                "passes": perf.passes,
                "pass_accuracy": perf.pass_accuracy,
                "tackles": perf.tackles,
                "interceptions": perf.interceptions,
                "saves": perf.saves,
                "yellow_cards": perf.yellow_cards,
                "red_cards": perf.red_cards
            }
            for perf in performances
        ]
    }


@router.get("/{match_id}/suspensions", response_model=Dict[str, Any])
def get_match_suspensions(match_id: int, db: Session = Depends(get_db)):
    """
    Get suspension data related to a match (placeholder)
    """
    # This is a placeholder endpoint - in real use, you'd query suspensions
    # related to players in this match
    return {
        "status": "success",
        "message": "Suspension endpoint is a placeholder",
        "data": []
    }
