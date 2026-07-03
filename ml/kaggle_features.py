"""
Kaggle Feature Engineering Module
==================================
Extracts advanced features from Kaggle FIFA World Cup 2026 dataset.

This module provides feature engineering functions that leverage the rich
data available in the Kaggle dataset to enhance prediction accuracy.
"""

import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func

# Add root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Team, Match, NationalTeamPlayer, PlayerMatchPerformance
from utils.logger import logger

# Kaggle data paths
KAGGLE_DATA_DIR = Path("data/temp_download")


def load_kaggle_data() -> Dict[str, pd.DataFrame]:
    """
    Load all Kaggle CSV files into memory.
    Returns dictionary mapping filename to DataFrame.
    """
    data_files = {
        'player_stats': 'player_stats.csv',
        'match_team_stats': 'match_team_stats.csv',
        'referees': 'referees.csv',
        'squads_and_players': 'squads_and_players.csv',
        'match_lineups': 'match_lineups.csv',
        'match_events': 'match_events.csv',
        'teams': 'teams.csv',
    }
    
    data = {}
    for key, filename in data_files.items():
        filepath = KAGGLE_DATA_DIR / filename
        if filepath.exists():
            data[key] = pd.read_csv(filepath)
            logger.info(f"Loaded {filename}: {len(data[key])} rows")
        else:
            logger.warning(f"Kaggle file not found: {filename}")
            data[key] = pd.DataFrame()
    
    return data


# Global cache for Kaggle data
_kaggle_cache = None


def get_kaggle_data() -> Dict[str, pd.DataFrame]:
    """Get Kaggle data with caching."""
    global _kaggle_cache
    if _kaggle_cache is None:
        _kaggle_cache = load_kaggle_data()
    return _kaggle_cache


def calculate_player_form_score(
    player_id: int, 
    team_id: int,
    kaggle_data: Optional[Dict[str, pd.DataFrame]] = None
) -> float:
    """
    Calculate player form score based on recent performance metrics.
    
    Uses player_stats.csv to compute a weighted form score considering:
    - Average rating (primary factor)
    - Goals and assists
    - Minutes played consistency
    - Shot accuracy
    
    Returns score between 0.0 and 1.0, where 1.0 is excellent form.
    """
    if kaggle_data is None:
        kaggle_data = get_kaggle_data()
    
    player_stats = kaggle_data.get('player_stats', pd.DataFrame())
    
    if player_stats.empty:
        return 0.5  # Neutral default
    
    player_data = player_stats[player_stats['player_id'] == player_id]
    
    if player_data.empty:
        return 0.5
    
    player = player_data.iloc[0]
    
    # Rating is the most important factor (weight: 0.5)
    avg_rating = player.get('average_rating')
    if pd.isna(avg_rating) or avg_rating == 0:
        rating_score = 0.5  # Neutral default
    else:
        rating_score = min(avg_rating / 10.0, 1.0)
    
    # Goals and assists contribution (weight: 0.2)
    goals = player.get('goals', 0)
    assists = player.get('assists', 0)
    matches_played = player.get('matches_played', 1)
    goal_contribution = min((goals + assists) / max(matches_played * 0.5, 1), 1.0)
    
    # Shot accuracy (weight: 0.15)
    shots = player.get('shots', 0)
    shots_on_target = player.get('shots_on_target', 0)
    shot_accuracy = min(shots_on_target / max(shots, 1), 1.0) if shots > 0 else 0.5
    
    # Minutes played consistency (weight: 0.15)
    minutes_played = player.get('minutes_played', 0)
    matches_started = player.get('matches_started', 1)
    avg_minutes = minutes_played / max(matches_started, 1)
    minutes_score = min(avg_minutes / 90.0, 1.0)
    
    # Weighted combination
    form_score = (
        0.5 * rating_score +
        0.2 * goal_contribution +
        0.15 * shot_accuracy +
        0.15 * minutes_score
    )
    
    return round(form_score, 4)


def calculate_team_attack_rating(
    team_id: int,
    kaggle_data: Optional[Dict[str, pd.DataFrame]] = None
) -> float:
    """
    Calculate team attack rating using Kaggle match statistics.
    
    Uses match_team_stats.csv to compute:
    - Average shots per match
    - Shot on target percentage
    - Goals per match
    - Possession advantage
    
    Returns score between 0.0 and 1.0.
    """
    if kaggle_data is None:
        kaggle_data = get_kaggle_data()
    
    team_stats = kaggle_data.get('match_team_stats', pd.DataFrame())
    
    if team_stats.empty:
        return 0.5
    
    team_matches = team_stats[team_stats['team_id'] == team_id]
    
    if team_matches.empty:
        return 0.5
    
    # Calculate averages
    avg_shots = team_matches['total_shots'].mean()
    avg_shots_on_target = team_matches['shots_on_target'].mean()
    avg_possession = team_matches['possession_pct'].mean()
    
    # Shot accuracy (weight: 0.3)
    shot_accuracy = min(avg_shots_on_target / max(avg_shots, 1), 1.0) if avg_shots > 0 else 0.5
    
    # Shot volume (weight: 0.25) - normalize to expected ~15 shots per match
    shot_volume = min(avg_shots / 15.0, 1.0)
    
    # Possession (weight: 0.25)
    possession_score = avg_possession / 100.0
    
    # Corners as attacking indicator (weight: 0.2)
    avg_corners = team_matches['corners'].mean()
    corner_score = min(avg_corners / 7.0, 1.0)
    
    attack_rating = (
        0.3 * shot_accuracy +
        0.25 * shot_volume +
        0.25 * possession_score +
        0.2 * corner_score
    )
    
    return round(attack_rating, 4)


def calculate_team_defense_rating(
    team_id: int,
    kaggle_data: Optional[Dict[str, pd.DataFrame]] = None
) -> float:
    """
    Calculate team defense rating using Kaggle match statistics.
    
    Uses match_team_stats.csv and player_stats.csv to compute:
    - Saves per match
    - Fouls conceded (inverse)
    - Offsides forced
    - Clean sheet rate
    
    Returns score between 0.0 and 1.0.
    """
    if kaggle_data is None:
        kaggle_data = get_kaggle_data()
    
    team_stats = kaggle_data.get('match_team_stats', pd.DataFrame())
    player_stats = kaggle_data.get('player_stats', pd.DataFrame())
    
    if team_stats.empty:
        return 0.5
    
    team_matches = team_stats[team_stats['team_id'] == team_id]
    
    if team_matches.empty:
        return 0.5
    
    # Calculate team-level defensive stats
    avg_saves = team_matches['saves'].mean()
    avg_fouls = team_matches['fouls'].mean()
    avg_offsides = team_matches['offsides'].mean()
    
    # Goalkeeper performance (weight: 0.35)
    gk_score = min(avg_saves / 4.0, 1.0)
    
    # Discipline - fewer fouls is better (weight: 0.25)
    foul_score = max(1.0 - (avg_fouls / 15.0), 0.0)
    
    # Offside trap effectiveness (weight: 0.2)
    offside_score = min(avg_offsides / 3.0, 1.0)
    
    # Clean sheet rate from player stats (weight: 0.2)
    team_players = player_stats[player_stats['team_id'] == team_id]
    if not team_players.empty:
        avg_clean_sheets = team_players['clean_sheets'].mean()
        clean_sheet_score = min(avg_clean_sheets / max(team_players['matches_played'].mean(), 1), 1.0)
    else:
        clean_sheet_score = 0.5
    
    defense_rating = (
        0.35 * gk_score +
        0.25 * foul_score +
        0.2 * offside_score +
        0.2 * clean_sheet_score
    )
    
    return round(defense_rating, 4)


def calculate_discipline_score(
    team_id: int,
    kaggle_data: Optional[Dict[str, pd.DataFrame]] = None
) -> float:
    """
    Calculate team discipline score based on card accumulation.
    
    Uses player_stats.csv to compute:
    - Yellow cards per match
    - Red cards per match
    - Overall disciplinary record
    
    Returns score between 0.0 and 1.0, where 1.0 is perfectly disciplined.
    """
    if kaggle_data is None:
        kaggle_data = get_kaggle_data()
    
    player_stats = kaggle_data.get('player_stats', pd.DataFrame())
    
    if player_stats.empty:
        return 1.0  # Assume disciplined if no data
    
    team_players = player_stats[player_stats['team_id'] == team_id]
    
    if team_players.empty:
        return 1.0
    
    total_yellow = team_players['yellow_cards'].sum()
    total_red = team_players['red_cards'].sum()
    total_matches = team_players['matches_played'].sum()
    
    if total_matches == 0:
        return 1.0
    
    # Yellow cards per match (weight: 0.6) - expect ~2 per match
    yellow_per_match = total_yellow / total_matches
    yellow_score = max(1.0 - (yellow_per_match / 3.0), 0.0)
    
    # Red cards are much worse (weight: 0.4) - expect ~0.1 per match
    red_per_match = total_red / total_matches
    red_score = max(1.0 - (red_per_match / 0.5), 0.0)
    
    discipline_score = 0.6 * yellow_score + 0.4 * red_score
    
    return round(discipline_score, 4)


def calculate_suspension_risk(
    team_id: int,
    kaggle_data: Optional[Dict[str, pd.DataFrame]] = None
) -> float:
    """
    Calculate suspension risk based on card accumulation.
    
    Uses player_stats.csv to identify players at risk of suspension
    based on yellow card accumulation (typically 2 cards = suspension).
    
    Returns score between 0.0 and 1.0, where 1.0 is high risk.
    """
    if kaggle_data is None:
        kaggle_data = get_kaggle_data()
    
    player_stats = kaggle_data.get('player_stats', pd.DataFrame())
    
    if player_stats.empty:
        return 0.0
    
    team_players = player_stats[player_stats['team_id'] == team_id]
    
    if team_players.empty:
        return 0.0
    
    # Count players with 1+ yellow cards (at risk)
    at_risk_players = len(team_players[team_players['yellow_cards'] >= 1])
    
    # Count players with 2+ yellow cards (high risk)
    high_risk_players = len(team_players[team_players['yellow_cards'] >= 2])
    
    total_players = len(team_players)
    
    if total_players == 0:
        return 0.0
    
    # Risk based on proportion of squad at risk
    at_risk_ratio = at_risk_players / total_players
    high_risk_ratio = high_risk_players / total_players
    
    # Weighted risk score
    suspension_risk = 0.3 * at_risk_ratio + 0.7 * high_risk_ratio
    
    return round(suspension_risk, 4)


def calculate_starting_xi_strength(
    team_id: int,
    kaggle_data: Optional[Dict[str, pd.DataFrame]] = None
) -> float:
    """
    Calculate starting XI strength based on market value.
    
    Uses squads_and_players.csv and match_lineups.csv to compute
    the total market value of the starting XI.
    
    Returns normalized score between 0.0 and 1.0.
    """
    if kaggle_data is None:
        kaggle_data = get_kaggle_data()
    
    squads = kaggle_data.get('squads_and_players', pd.DataFrame())
    lineups = kaggle_data.get('match_lineups', pd.DataFrame())
    
    if squads.empty or lineups.empty:
        return 0.5
    
    # Get starting players for this team
    team_lineups = lineups[lineups['team_id'] == team_id]
    starting_players = team_lineups[team_lineups['is_starting_xi'] == 1]
    
    if starting_players.empty:
        return 0.5
    
    # Get market values for starting players
    starting_ids = starting_players['player_id'].unique()
    starting_squad = squads[squads['player_id'].isin(starting_ids)]
    
    if starting_squad.empty:
        return 0.5
    
    total_value = starting_squad['market_value_eur'].sum()
    
    # Normalize against typical top-tier squad value (~€500M)
    normalized_value = min(total_value / 500_000_000, 1.0)
    
    return round(normalized_value, 4)


def calculate_bench_strength(
    team_id: int,
    kaggle_data: Optional[Dict[str, pd.DataFrame]] = None
) -> float:
    """
    Calculate bench strength based on market value of substitutes.
    
    Uses squads_and_players.csv and match_lineups.csv to compute
    the total market value of bench players.
    
    Returns normalized score between 0.0 and 1.0.
    """
    if kaggle_data is None:
        kaggle_data = get_kaggle_data()
    
    squads = kaggle_data.get('squads_and_players', pd.DataFrame())
    lineups = kaggle_data.get('match_lineups', pd.DataFrame())
    
    if squads.empty or lineups.empty:
        return 0.5
    
    # Get bench players for this team
    team_lineups = lineups[lineups['team_id'] == team_id]
    bench_players = team_lineups[team_lineups['is_starting_xi'] == 0]
    
    if bench_players.empty:
        return 0.5
    
    # Get market values for bench players
    bench_ids = bench_players['player_id'].unique()
    bench_squad = squads[squads['player_id'].isin(bench_ids)]
    
    if bench_squad.empty:
        return 0.5
    
    total_value = bench_squad['market_value_eur'].sum()
    
    # Normalize against typical strong bench value (~€200M)
    normalized_value = min(total_value / 200_000_000, 1.0)
    
    return round(normalized_value, 4)


def calculate_referee_strictness(
    referee_id: int,
    kaggle_data: Optional[Dict[str, pd.DataFrame]] = None
) -> float:
    """
    Calculate referee strictness based on card statistics.
    
    Uses referees.csv to get average cards per game.
    
    Returns score between 0.0 and 1.0, where 1.0 is very strict.
    """
    if kaggle_data is None:
        kaggle_data = get_kaggle_data()
    
    referees = kaggle_data.get('referees', pd.DataFrame())
    
    if referees.empty:
        return 0.5  # Neutral default
    
    referee_data = referees[referees['referee_id'] == referee_id]
    
    if referee_data.empty:
        return 0.5
    
    avg_cards = referee_data.iloc[0].get('avg_cards_per_game', 4.0)
    
    # Normalize: typical range is 2-6 cards per match
    strictness = min((avg_cards - 2.0) / 4.0, 1.0)
    strictness = max(strictness, 0.0)
    
    return round(strictness, 4)


def get_team_kaggle_features(
    team_id: int,
    team_name: str = None,
    kaggle_data: Optional[Dict[str, pd.DataFrame]] = None
) -> Dict[str, float]:
    """
    Get all Kaggle-based features for a team.
    
    Returns dictionary with all engineered features.
    If team not found in Kaggle data, returns default neutral values.
    Uses team name matching for compatibility with database team IDs.
    """
    if kaggle_data is None:
        kaggle_data = get_kaggle_data()
    
    # Check if team exists in Kaggle data by name matching
    teams_df = kaggle_data.get('teams', pd.DataFrame())
    
    if teams_df.empty:
        logger.debug("Kaggle teams data not available, returning defaults")
        return _get_default_kaggle_features()
    
    # Try to find team by name if provided
    if team_name:
        # Case-insensitive name matching with normalization
        team_name_lower = team_name.lower().strip()
        
        # Normalize common name variations
        normalized_name = team_name_lower
        name_mappings = {
            'bosnia-herzegovina': 'bosnia and herzegovina',
            'ivory coast': "côte d'ivoire",
            'turkey': 'türkiye',
            'united states': 'usa',
            'iran': 'ir iran',
            'cape verde islands': 'cabo verde',
            'czech republic': 'czechia',
            'south korea': 'korea republic',
        }
        
        if normalized_name in name_mappings:
            normalized_name = name_mappings[normalized_name]
        
        matching_team = teams_df[
            teams_df['team_name'].str.lower().str.strip() == normalized_name
        ]
        
        # If still no match, try partial matching
        if matching_team.empty:
            matching_team = teams_df[
                teams_df['team_name'].str.lower().str.contains(team_name_lower.replace(' ', '|'))
            ]
        
        if not matching_team.empty:
            kaggle_team_id = matching_team.iloc[0]['team_id']
            kaggle_name = matching_team.iloc[0]['team_name']
            logger.info(f"Found Kaggle team ID {kaggle_team_id} ('{kaggle_name}') for '{team_name}'")
            return {
                'kaggle_attack_rating': calculate_team_attack_rating(kaggle_team_id, kaggle_data),
                'kaggle_defense_rating': calculate_team_defense_rating(kaggle_team_id, kaggle_data),
                'kaggle_discipline_score': calculate_discipline_score(kaggle_team_id, kaggle_data),
                'kaggle_suspension_risk': calculate_suspension_risk(kaggle_team_id, kaggle_data),
                'kaggle_starting_xi_strength': calculate_starting_xi_strength(kaggle_team_id, kaggle_data),
                'kaggle_bench_strength': calculate_bench_strength(kaggle_team_id, kaggle_data),
            }
        else:
            logger.warning(f"Team '{team_name}' not found in Kaggle data, returning defaults")
            return _get_default_kaggle_features()
    
    # Fallback to ID matching if no name provided
    if team_id in teams_df['team_id'].values:
        return {
            'kaggle_attack_rating': calculate_team_attack_rating(team_id, kaggle_data),
            'kaggle_defense_rating': calculate_team_defense_rating(team_id, kaggle_data),
            'kaggle_discipline_score': calculate_discipline_score(team_id, kaggle_data),
            'kaggle_suspension_risk': calculate_suspension_risk(team_id, kaggle_data),
            'kaggle_starting_xi_strength': calculate_starting_xi_strength(team_id, kaggle_data),
            'kaggle_bench_strength': calculate_bench_strength(team_id, kaggle_data),
        }
    else:
        logger.debug(f"Team ID {team_id} not found in Kaggle data, returning defaults")
        return _get_default_kaggle_features()


def _get_default_kaggle_features() -> Dict[str, float]:
    """Return default neutral Kaggle features when data is unavailable."""
    return {
        'kaggle_attack_rating': 0.5,
        'kaggle_defense_rating': 0.5,
        'kaggle_discipline_score': 1.0,
        'kaggle_suspension_risk': 0.0,
        'kaggle_starting_xi_strength': 0.5,
        'kaggle_bench_strength': 0.5,
    }


def get_match_kaggle_features(
    home_team_id: int,
    away_team_id: int,
    home_team_name: str = None,
    away_team_name: str = None,
    referee_id: Optional[int] = None,
    kaggle_data: Optional[Dict[str, pd.DataFrame]] = None
) -> Dict[str, float]:
    """
    Get all Kaggle-based features for a match.
    
    Returns dictionary with home/away differences and referee features.
    If Kaggle data is not available, returns default neutral values.
    Uses team name matching for compatibility with database team IDs.
    """
    if kaggle_data is None:
        kaggle_data = get_kaggle_data()
    
    # Check if Kaggle data is available
    if not kaggle_data or all(df.empty for df in kaggle_data.values()):
        logger.warning("Kaggle data not available, returning default values")
        return _get_default_match_features()
    
    home_features = get_team_kaggle_features(home_team_id, home_team_name, kaggle_data)
    away_features = get_team_kaggle_features(away_team_id, away_team_name, kaggle_data)
    
    features = {}
    
    # Add home team features
    for key, value in home_features.items():
        features[f'home_{key}'] = value
    
    # Add away team features
    for key, value in away_features.items():
        features[f'away_{key}'] = value
    
    # Add difference features
    for key in home_features.keys():
        features[f'{key}_diff'] = home_features[key] - away_features[key]
    
    # Add referee strictness
    if referee_id is not None:
        features['referee_strictness'] = calculate_referee_strictness(referee_id, kaggle_data)
    else:
        features['referee_strictness'] = 0.5
    
    return features


def _get_default_match_features() -> Dict[str, float]:
    """Return default neutral Kaggle match features when data is unavailable."""
    return {
        'home_kaggle_attack_rating': 0.5,
        'away_kaggle_attack_rating': 0.5,
        'kaggle_attack_rating_diff': 0.0,
        'home_kaggle_defense_rating': 0.5,
        'away_kaggle_defense_rating': 0.5,
        'kaggle_defense_rating_diff': 0.0,
        'home_kaggle_discipline_score': 1.0,
        'away_kaggle_discipline_score': 1.0,
        'kaggle_discipline_score_diff': 0.0,
        'home_kaggle_suspension_risk': 0.0,
        'away_kaggle_suspension_risk': 0.0,
        'kaggle_suspension_risk_diff': 0.0,
        'home_kaggle_starting_xi_strength': 0.5,
        'away_kaggle_starting_xi_strength': 0.5,
        'kaggle_starting_xi_strength_diff': 0.0,
        'home_kaggle_bench_strength': 0.5,
        'away_kaggle_bench_strength': 0.5,
        'kaggle_bench_strength_diff': 0.0,
        'referee_strictness': 0.5,
    }


def clear_kaggle_cache():
    """Clear the Kaggle data cache."""
    global _kaggle_cache
    _kaggle_cache = None
    logger.info("Kaggle data cache cleared")


if __name__ == "__main__":
    # Test the feature engineering functions
    logger.info("Testing Kaggle feature engineering...")
    
    data = load_kaggle_data()
    
    if data.get('player_stats') is not None and not data['player_stats'].empty:
        # Test with first team and player
        first_team_id = data['player_stats']['team_id'].iloc[0]
        first_player_id = data['player_stats']['player_id'].iloc[0]
        
        logger.info(f"Testing with team_id={first_team_id}, player_id={first_player_id}")
        
        player_form = calculate_player_form_score(first_player_id, first_team_id, data)
        logger.info(f"Player Form Score: {player_form}")
        
        team_attack = calculate_team_attack_rating(first_team_id, data)
        logger.info(f"Team Attack Rating: {team_attack}")
        
        team_defense = calculate_team_defense_rating(first_team_id, data)
        logger.info(f"Team Defense Rating: {team_defense}")
        
        discipline = calculate_discipline_score(first_team_id, data)
        logger.info(f"Discipline Score: {discipline}")
        
        suspension_risk = calculate_suspension_risk(first_team_id, data)
        logger.info(f"Suspension Risk: {suspension_risk}")
        
        xi_strength = calculate_starting_xi_strength(first_team_id, data)
        logger.info(f"Starting XI Strength: {xi_strength}")
        
        bench_strength = calculate_bench_strength(first_team_id, data)
        logger.info(f"Bench Strength: {bench_strength}")
        
        if data.get('referees') is not None and not data['referees'].empty:
            first_referee_id = data['referees']['referee_id'].iloc[0]
            referee_strictness = calculate_referee_strictness(first_referee_id, data)
            logger.info(f"Referee Strictness: {referee_strictness}")
    
    logger.info("Kaggle feature engineering test complete.")
