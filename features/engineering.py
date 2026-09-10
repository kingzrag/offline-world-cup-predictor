from sqlalchemy.orm import Session
from sqlalchemy import desc
from models import Match, Standing, Injury, Suspension, Player
from utils.logger import logger

def extract_match_features(db: Session, home_team_id: int, away_team_id: int, competition_id: int) -> dict:
    """
    Extracts statistical feature metrics for both home and away teams.
    Calculates PPG, Goal Differentials, and Active Injury impact indices.
    """
    # 1. Fetch standings metrics (Default values if no standings found)
    home_standing = db.query(Standing).filter_by(competition_id=competition_id, team_id=home_team_id).first()
    away_standing = db.query(Standing).filter_by(competition_id=competition_id, team_id=away_team_id).first()
    
    # Home Team Stats
    home_ppg = 1.0  # fallback baseline
    home_gd = 0
    if home_standing and home_standing.played_games > 0:
        home_ppg = home_standing.points / home_standing.played_games
        home_gd = home_standing.goals_difference / home_standing.played_games

    # Away Team Stats
    away_ppg = 1.0  # fallback baseline
    away_gd = 0
    if away_standing and away_standing.played_games > 0:
        away_ppg = away_standing.points / away_standing.played_games
        away_gd = away_standing.goals_difference / away_standing.played_games

    # 2. Fetch active injury counts
    home_injuries_count = db.query(Injury).filter_by(team_id=home_team_id).count()
    away_injuries_count = db.query(Injury).filter_by(team_id=away_team_id).count()

    # 3. Head to Head historical performance (last 5 games)
    h2h_matches = db.query(Match).filter(
        ((Match.home_team_id == home_team_id) & (Match.away_team_id == away_team_id)) |
        ((Match.home_team_id == away_team_id) & (Match.away_team_id == home_team_id))
    ).filter(Match.status == "FINISHED").order_by(desc(Match.utc_date)).limit(5).all()

    home_h2h_wins = 0
    away_h2h_wins = 0
    h2h_draws = 0
    
    for m in h2h_matches:
        if m.winner == "HOME_TEAM":
            if m.home_team_id == home_team_id:
                home_h2h_wins += 1
            else:
                away_h2h_wins += 1
        elif m.winner == "AWAY_TEAM":
            if m.away_team_id == home_team_id:
                home_h2h_wins += 1
            else:
                away_h2h_wins += 1
        elif m.winner == "DRAW":
            h2h_draws += 1

    h2h_factor = 0.5  # 0.5 is neutral
    total_h2h = home_h2h_wins + away_h2h_wins + h2h_draws
    if total_h2h > 0:
        # Calculate ratio of home team wins vs total matches
        home_h2h_score = (home_h2h_wins * 1.0) + (h2h_draws * 0.5)
        h2h_factor = home_h2h_score / total_h2h

    features = {
        "home_ppg": home_ppg,
        "away_ppg": away_ppg,
        "home_gd_per_game": home_gd,
        "away_gd_per_game": away_gd,
        "home_injury_count": home_injuries_count,
        "away_injury_count": away_injuries_count,
        "h2h_factor": h2h_factor
    }
    
    logger.debug(f"Extracted features for Match (Home ID: {home_team_id}, Away ID: {away_team_id}): {features}")
    return features

# -------------------------------------------------------------------
# Odds‑related feature utilities
# -------------------------------------------------------------------

from typing import Optional
from models.bookmaker_odds import BookmakerOdds

def implied_probability(odds: Optional[float]) -> Optional[float]:
    """Convert decimal odds to implied probability (0‑1).
    Returns ``None`` if odds are missing or non‑positive.
    """
    if odds is None or odds <= 0:
        return None
    # Round to 4 decimal places for stability
    return round(1.0 / odds, 4)

def add_odds_features(db: Session, match_id: int, base_features: dict) -> dict:
    """Fetch the best (lowest‑odds) bookmaker odds for a match and extend
    ``base_features`` with probability and difference columns.
    The function looks for any odds rows for the ``match_id`` and selects the
    record with the highest confidence (lowest ``home_odds``) as a simple heuristic.
    """
    odds_rows = db.query(BookmakerOdds).filter(BookmakerOdds.match_id == match_id).all()
    if not odds_rows:
        # No odds available – return features unchanged
        return base_features
    # Pick the row with the lowest combined odds (most favorable market) or first row
    best = min(odds_rows, key=lambda o: (o.home_odds or float('inf')) + (o.away_odds or float('inf')))
    # Compute implied probabilities
    base_features.update({
        "home_odds": best.home_odds,
        "draw_odds": best.draw_odds,
        "away_odds": best.away_odds,
        "implied_home_probability": implied_probability(best.home_odds),
        "implied_draw_probability": implied_probability(best.draw_odds),
        "implied_away_probability": implied_probability(best.away_odds),
        "odds_difference": (best.home_odds or 0) - (best.away_odds or 0),
    })
    return base_features


# -------------------------------------------------------------------
# Transfermarkt Missing Players Features
# -------------------------------------------------------------------

def names_match(name1: str, name2: str) -> bool:
    """Helper to compare player names flexibly."""
    n1 = name1.lower().replace("-", " ").strip()
    n2 = name2.lower().replace("-", " ").strip()
    if n1 == n2:
        return True
    words1 = set(n1.split())
    words2 = set(n2.split())
    if words1.issubset(words2) or words2.issubset(words1):
        return True
    return False

def get_missing_players_by_position(db: Session, team_id: int) -> dict:
    """Calculates missing player statistics grouped by position."""
    injured_names = db.query(Injury.player_name).filter(Injury.team_id == team_id).all()
    suspended_names = db.query(Suspension.player_name).filter(Suspension.team_id == team_id).all()
    names = {name[0] for name in injured_names + suspended_names}
    
    counts = {
        "attackers": 0,
        "midfielders": 0,
        "defenders": 0,
        "goalkeepers": 0,
        "total": len(names)
    }
    
    if not names:
        return counts
        
    players = db.query(Player).filter(Player.team_id == team_id).all()
    
    for missing_name in names:
        matched = None
        for p in players:
            if names_match(p.name, missing_name):
                matched = p
                break
        
        if matched and matched.position:
            pos = matched.position.lower()
            if "goalkeeper" in pos or "keeper" in pos or pos == "gk":
                counts["goalkeepers"] += 1
            elif "defender" in pos or "back" in pos or "lb" in pos or "rb" in pos or "cb" in pos or "fullback" in pos:
                counts["defenders"] += 1
            elif "midfielder" in pos or "midfield" in pos or "dmf" in pos or "cmf" in pos or "amf" in pos or "dm" in pos or "cm" in pos or "am" in pos:
                counts["midfielders"] += 1
            elif ("attacker" in pos or "forward" in pos or "winger" in pos or "striker" in pos or 
                  "wing" in pos or "fw" in pos or "cf" in pos or "lw" in pos or "rw" in pos or "centre-forward" in pos):
                counts["attackers"] += 1
                
    return counts

def missing_players_count(db: Session, team_id: int) -> int:
    """Returns the total number of missing players (injured + suspended)."""
    return get_missing_players_by_position(db, team_id)["total"]

def missing_attackers_count(db: Session, team_id: int) -> int:
    """Returns the number of missing attackers."""
    return get_missing_players_by_position(db, team_id)["attackers"]

def missing_midfielders_count(db: Session, team_id: int) -> int:
    """Returns the number of missing midfielders."""
    return get_missing_players_by_position(db, team_id)["midfielders"]

def missing_defenders_count(db: Session, team_id: int) -> int:
    """Returns the number of missing defenders."""
    return get_missing_players_by_position(db, team_id)["defenders"]

def missing_goalkeepers_count(db: Session, team_id: int) -> int:
    """Returns the number of missing goalkeepers."""
    return get_missing_players_by_position(db, team_id)["goalkeepers"]


# -------------------------------------------------------------------
# Phase 2 Feature Engineering & Data Freshness Classes
# -------------------------------------------------------------------
import numpy as np
import pandas as pd
from datetime import datetime, timezone

class FeatureEngineer:
    """Standardized feature extraction for model evaluation and production inference."""
    def extract_baseline_features(self, df: pd.DataFrame):
        feature_cols = [
            'elo_diff', 'rest_diff', 'h2h_home_wins', 'h2h_draws',
            'h2h_away_wins', 'home_form', 'away_form'
        ]
        # Fill missing with standard defaults
        for col in feature_cols:
            if col not in df.columns:
                df[col] = 0.0
        X = df[feature_cols].copy()
        if 'elo_diff' in X.columns and 'elo_home' in df.columns and 'elo_away' in df.columns:
            X['elo_diff'] = df['elo_home'] - df['elo_away']
        X = X.fillna(0.0).values
        return X, feature_cols

class DataFreshnessTracker:
    """Monitors data timestamps to prevent stale or post-kickoff data usage."""
    def check_freshness(self, feature_name: str, source: str, last_updated: datetime, prediction_time: datetime, max_allowed_age_hours: float = 24.0) -> dict:
        if last_updated is None:
            return {
                "feature": feature_name,
                "source": source,
                "status": "missing",
                "is_fresh": False,
                "age_hours": None
            }
        if last_updated.tzinfo is None:
            last_updated = last_updated.replace(tzinfo=timezone.utc)
        if prediction_time.tzinfo is None:
            prediction_time = prediction_time.replace(tzinfo=timezone.utc)
            
        age_hours = (prediction_time - last_updated).total_seconds() / 3600.0
        
        if age_hours < 0:
            status = "future_leakage_risk"
            is_fresh = False
        elif age_hours <= max_allowed_age_hours:
            status = "valid"
            is_fresh = True
        else:
            status = "stale"
            is_fresh = False
            
        return {
            "feature": feature_name,
            "source": source,
            "last_updated": last_updated.isoformat(),
            "prediction_timestamp": prediction_time.isoformat(),
            "age_hours": round(age_hours, 2),
            "max_allowed_age_hours": max_allowed_age_hours,
            "status": status,
            "is_fresh": is_fresh
        }

