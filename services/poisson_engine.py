# services/poisson_engine.py
"""
Poisson Probability Engine for Football Match Betting Markets.
Calculates Correct Score, BTTS, Over/Under, Asian Handicap, and Team Goals
probabilities using independent Poisson distributions on expected home/away goals.
"""

POISSON_ENGINE_VERSION = "Poisson Probability Engine v2"

import math
import scipy.stats
from typing import Dict, Any, List, Tuple

def get_poisson_probability(lmbda: float, k: int) -> float:
    """Calculates Poisson probability for k events with mean lmbda."""
    if lmbda <= 0:
        return 1.0 if k == 0 else 0.0
    try:
        return (math.pow(lmbda, k) * math.exp(-lmbda)) / math.factorial(k)
    except OverflowError:
        return 0.0

def calculate_probability_matrix(expected_home_goals: float, expected_away_goals: float, max_goals: int = 10) -> Dict[str, float]:
    """
    Generate joint score probabilities for home and away goals up to max_goals.
    Returns a dictionary mapping score strings (e.g. "2-1") to probability float (0.0 to 1.0).
    """
    # Ensure non-negative lambdas
    lam_h = max(0.0001, expected_home_goals)
    lam_a = max(0.0001, expected_away_goals)
    
    matrix = {}
    for h in range(max_goals + 1):
        p_h = get_poisson_probability(lam_h, h)
        for a in range(max_goals + 1):
            p_a = get_poisson_probability(lam_a, a)
            matrix[f"{h}-{a}"] = p_h * p_a
    return matrix

def calculate_conditional_probability_matrix(
    current_home_score: int,
    current_away_score: int,
    remaining_home_xg: float,
    remaining_away_xg: float,
    max_goals: int = 10
) -> Dict[str, float]:
    """
    Generate joint final score probabilities given a current score and remaining xG.
    
    Final Score = Current Score + Remaining Goals
    
    Args:
        current_home_score: Current home goals
        current_away_score: Current away goals
        remaining_home_xg: Expected remaining home goals
        remaining_away_xg: Expected remaining away goals
        max_goals: Maximum additional goals to consider
        
    Returns:
        Dictionary mapping final score strings to probabilities
    """
    # Ensure non-negative lambdas
    lam_h = max(0.0001, remaining_home_xg)
    lam_a = max(0.0001, remaining_away_xg)
    
    matrix = {}
    total_prob = 0.0
    
    # Calculate probabilities for all possible remaining goals
    for delta_h in range(max_goals + 1):
        p_h = get_poisson_probability(lam_h, delta_h)
        for delta_a in range(max_goals + 1):
            p_a = get_poisson_probability(lam_a, delta_a)
            final_h = current_home_score + delta_h
            final_a = current_away_score + delta_a
            score_str = f"{final_h}-{final_a}"
            matrix[score_str] = p_h * p_a
            total_prob += p_h * p_a
    
    # Re-normalize to ensure probabilities sum to 1
    if total_prob > 0:
        for score_str in matrix:
            matrix[score_str] /= total_prob
    
    return matrix

def get_correct_scores(matrix: Dict[str, float]) -> Dict[str, Any]:
    """
    Returns the most likely score and the top 5 scorelines.
    """
    sorted_scores = sorted(matrix.items(), key=lambda x: x[1], reverse=True)
    most_likely_score, prob = sorted_scores[0]
    
    top_5 = []
    for score, p in sorted_scores[:5]:
        top_5.append({
            "score": score,
            "probability": round(p, 4)
        })
        
    return {
        "most_likely_score": most_likely_score,
        "most_likely_score_probability": round(prob, 4),
        "top_5_scorelines": top_5
    }

# Backwards compatible functions for existing callers
def get_btts_probabilities(expected_home_goals: float, expected_away_goals: float) -> Dict[str, float]:
    """
    Calculates BTTS Yes and No probabilities (backwards compatible).
    """
    matrix = calculate_probability_matrix(expected_home_goals, expected_away_goals)
    return get_btts_probabilities_from_matrix(matrix, 0, 0)

def get_over_under_probabilities(expected_home_goals: float, expected_away_goals: float) -> Dict[str, Dict[str, float]]:
    """
    Calculates Over/Under probabilities (backwards compatible).
    """
    matrix = calculate_probability_matrix(expected_home_goals, expected_away_goals)
    return get_over_under_probabilities_from_matrix(matrix)

def get_asian_handicap_probabilities(expected_home_goals: float, expected_away_goals: float, matrix: Dict[str, float]) -> Dict[str, Any]:
    """
    Calculates the suggested Asian Handicap lines and probability of covering each line (backwards compatible).
    """
    return get_asian_handicap_probabilities_from_matrix(matrix)

def get_team_goals_probabilities(expected_home_goals: float, expected_away_goals: float) -> Dict[str, Dict[str, float]]:
    """
    Calculates Over probabilities for Team Goals (backwards compatible).
    """
    matrix = calculate_probability_matrix(expected_home_goals, expected_away_goals)
    return get_team_goals_probabilities_from_matrix(matrix, 0, 0)

def get_clean_sheet_probabilities(expected_home_goals: float, expected_away_goals: float) -> Dict[str, float]:
    """
    Calculates Clean Sheet probabilities (backwards compatible).
    """
    matrix = calculate_probability_matrix(expected_home_goals, expected_away_goals)
    return get_clean_sheet_probabilities_from_matrix(matrix, 0, 0)

def get_btts_probabilities_from_matrix(matrix: Dict[str, float], current_home_score: int, current_away_score: int) -> Dict[str, float]:
    """
    Calculates BTTS Yes and No probabilities from a final score matrix.
    """
    btts_yes = 0.0
    for score_str, prob in matrix.items():
        h, a = map(int, score_str.split('-'))
        if h > 0 and a > 0:
            btts_yes += prob
    
    # Also check if both teams have already scored
    if current_home_score > 0 and current_away_score > 0:
        btts_yes = 1.0
    
    btts_no = 1.0 - btts_yes
    
    # Return both formats for backward compatibility
    return {
        "yes": round(btts_yes, 4),
        "no": round(btts_no, 4),
        "btts_yes": round(btts_yes, 4),
        "btts_no": round(btts_no, 4)
    }

def get_over_under_probabilities_from_matrix(matrix: Dict[str, float]) -> Dict[str, Dict[str, float]]:
    """
    Calculates Over/Under probabilities for 0.5, 1.5, 2.5, 3.5, and 4.5 lines from a final score matrix.
    
    For a line like 1.5:
    - Under: total goals < 1.5 (i.e., 0 or 1 goals)
    - Over: total goals >= 1.5 (i.e., 2 or more goals)
    """
    results = {}
    for line in (0.5, 1.5, 2.5, 3.5, 4.5):
        under = 0.0
        for score_str, prob in matrix.items():
            h, a = map(int, score_str.split('-'))
            total = h + a
            # Use proper floating-point comparison for half-point lines
            if total < line:
                under += prob
        over = 1.0 - under
        results[str(line)] = {"over": round(over, 4), "under": round(under, 4)}

    return results

def get_asian_handicap_probabilities_from_matrix(matrix: Dict[str, float]) -> Dict[str, Any]:
    """
    Calculates the suggested Asian Handicap lines and probability of covering each line from a final score matrix.
    """
    # Calculate expected goal difference from matrix
    exp_home = 0.0
    exp_away = 0.0
    for score_str, prob in matrix.items():
        h, a = map(int, score_str.split('-'))
        exp_home += h * prob
        exp_away += a * prob
    
    diff = exp_home - exp_away
    is_home_fav = diff >= 0
    prefix = "Home" if is_home_fav else "Away"
    
    # Lines to generate
    lines = [-0.25, -0.5, -0.75, -1.0]
    
    results = {}
    # We will sum probabilities from the joint matrix
    # P(cover) calculations:
    for line in lines:
        cover_prob = 0.0
        for score_str, prob in matrix.items():
            h, a = map(int, score_str.split('-'))
            fav_score = h if is_home_fav else a
            dog_score = a if is_home_fav else h
            goal_diff = fav_score - dog_score
            
            # Evaluate covering based on line
            if line == -0.25:
                # Win if goal_diff >= 1. Half-loss (refund 0.5) if goal_diff == 0.
                if goal_diff >= 1:
                    cover_prob += prob
                elif goal_diff == 0:
                    cover_prob += prob * 0.5
            elif line == -0.5:
                # Win if goal_diff >= 1.
                if goal_diff >= 1:
                    cover_prob += prob
            elif line == -0.75:
                # Full win if goal_diff >= 2. Half win if goal_diff == 1.
                if goal_diff >= 2:
                    cover_prob += prob
                elif goal_diff == 1:
                    cover_prob += prob * 0.5
            elif line == -1.0:
                # Full win if goal_diff >= 2. Push if goal_diff == 1 (refunded/covered).
                if goal_diff >= 2:
                    cover_prob += prob
                elif goal_diff == 1:
                    cover_prob += prob
                    
        results[f"{prefix} {line}"] = round(cover_prob, 4)
        
    return {
        "favored_team_prefix": prefix,
        "suggested_lines": results
    }

def get_team_goals_probabilities_from_matrix(matrix: Dict[str, float], current_home_score: int, current_away_score: int) -> Dict[str, Dict[str, float]]:
    """
    Calculates Over probabilities for Team Goals (0.5, 1.5, 2.5) from a final score matrix.
    """
    home_over_0_5 = 0.0
    home_over_1_5 = 0.0
    home_over_2_5 = 0.0
    away_over_0_5 = 0.0
    away_over_1_5 = 0.0
    away_over_2_5 = 0.0
    
    for score_str, prob in matrix.items():
        h, a = map(int, score_str.split('-'))
        if h > 0:
            home_over_0_5 += prob
        if h > 1:
            home_over_1_5 += prob
        if h > 2:
            home_over_2_5 += prob
        if a > 0:
            away_over_0_5 += prob
        if a > 1:
            away_over_1_5 += prob
        if a > 2:
            away_over_2_5 += prob
    
    return {
        "home": {
            "over_0_5": round(home_over_0_5, 4),
            "over_1_5": round(home_over_1_5, 4),
            "over_2_5": round(home_over_2_5, 4)
        },
        "away": {
            "over_0_5": round(away_over_0_5, 4),
            "over_1_5": round(away_over_1_5, 4),
            "over_2_5": round(away_over_2_5, 4)
        }
    }

def get_clean_sheet_probabilities_from_matrix(matrix: Dict[str, float], current_home_score: int, current_away_score: int) -> Dict[str, float]:
    """
    Calculates Clean Sheet probabilities from a final score matrix.
    """
    home_cs = 0.0
    away_cs = 0.0
    
    for score_str, prob in matrix.items():
        h, a = map(int, score_str.split('-'))
        if a == 0:
            home_cs += prob
        if h == 0:
            away_cs += prob
    
    # If a team has already conceded, clean sheet is impossible
    if current_away_score > 0:
        home_cs = 0.0
    if current_home_score > 0:
        away_cs = 0.0
    
    return {
        "home_clean_sheet": round(home_cs, 4),
        "away_clean_sheet": round(away_cs, 4),
    }

def get_1x2_probabilities(matrix: Dict[str, float]) -> Dict[str, float]:
    """
    Computes 1X2 probabilities (home win, draw, away win) by summing the joint distribution matrix.
    
    The matrix already sums to 1.0, so no additional normalization is needed.
    """
    home_win = 0.0
    draw = 0.0
    away_win = 0.0
    for score, p in matrix.items():
        parts = score.split('-')
        h = int(parts[0])
        a = int(parts[1])
        if h > a:
            home_win += p
        elif h < a:
            away_win += p
        else:
            draw += p
    
    # Matrix already sums to 1.0, so no normalization needed
    # Just round for consistent output
    return {
        "home_win_probability": round(home_win, 4),
        "draw_probability":     round(draw, 4),
        "away_win_probability": round(away_win, 4),
    }


def evaluate_poisson_engine(
    expected_home_goals: float,
    expected_away_goals: float,
    current_home_score: int = 0,
    current_away_score: int = 0
) -> Dict[str, Any]:
    """
    Main entry point to calculate all markets from expected goals and current score.
    
    Args:
        expected_home_goals: Expected remaining home goals
        expected_away_goals: Expected remaining away goals
        current_home_score: Current home score (default: 0 for pre-match)
        current_away_score: Current away score (default: 0 for pre-match)
        
    Returns:
        All betting markets based on final score distribution
    """
    if current_home_score == 0 and current_away_score == 0:
        # Pre-match or 0-0 with no goals - use original method for backward compatibility
        matrix = calculate_probability_matrix(expected_home_goals, expected_away_goals)
    else:
        # Live match with goals - use conditional probability matrix
        matrix = calculate_conditional_probability_matrix(
            current_home_score,
            current_away_score,
            expected_home_goals,
            expected_away_goals
        )

    requested_scores = []
    # Generate requested scores based on current score
    max_current = max(current_home_score, current_away_score)
    for dh in range(0, 5):
        for da in range(0, 5):
            fh = current_home_score + dh
            fa = current_away_score + da
            requested_scores.append(f"{fh}-{fa}")
    
    rounded_matrix = {score: round(prob, 4) for score, prob in matrix.items()}

    correct_scores  = get_correct_scores(matrix)
    btts            = get_btts_probabilities_from_matrix(matrix, current_home_score, current_away_score)
    over_under      = get_over_under_probabilities_from_matrix(matrix)
    asian_handicap  = get_asian_handicap_probabilities_from_matrix(matrix)
    team_goals      = get_team_goals_probabilities_from_matrix(matrix, current_home_score, current_away_score)
    clean_sheet     = get_clean_sheet_probabilities_from_matrix(matrix, current_home_score, current_away_score)
    outcome_probs   = get_1x2_probabilities(matrix)

    return {
        "probability_matrix": rounded_matrix,
        "most_likely_score":  correct_scores["most_likely_score"],
        "top_5_scorelines":   correct_scores["top_5_scorelines"],
        "btts":               btts,
        "over_under":         over_under,
        "asian_handicap":     asian_handicap,
        "team_goals":         team_goals,
        "clean_sheet":        clean_sheet,
        "outcome_probabilities": outcome_probs,
    }
