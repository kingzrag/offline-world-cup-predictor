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

def calculate_dixon_coles_tau(h: int, a: int, lam_h: float, lam_a: float, rho: float) -> float:
    """Calculates Dixon-Coles low-score interdependence adjustment tau."""
    if rho == 0.0:
        return 1.0
    if h == 0 and a == 0:
        return 1.0 - lam_h * lam_a * rho
    elif h == 1 and a == 0:
        return 1.0 + lam_a * rho
    elif h == 0 and a == 1:
        return 1.0 + lam_h * rho
    elif h == 1 and a == 1:
        return 1.0 - rho
    return 1.0

def calculate_probability_matrix(
    expected_home_goals: float,
    expected_away_goals: float,
    max_goals: int = 10,
    rho: float = -0.0646
) -> Dict[str, float]:
    """
    Generate joint score probabilities for home and away goals up to max_goals,
    applying Dixon-Coles low-score tau adjustment.
    Returns a normalized dictionary mapping score strings (e.g. "2-1") to probability float.
    """
    # Ensure non-negative lambdas
    lam_h = max(0.0001, expected_home_goals)
    lam_a = max(0.0001, expected_away_goals)
    
    matrix = {}
    total_prob = 0.0
    for h in range(max_goals + 1):
        p_h = get_poisson_probability(lam_h, h)
        for a in range(max_goals + 1):
            p_a = get_poisson_probability(lam_a, a)
            tau = calculate_dixon_coles_tau(h, a, lam_h, lam_a, rho)
            prob = max(0.0, p_h * p_a * tau)
            matrix[f"{h}-{a}"] = prob
            total_prob += prob
            
    # Normalize probabilities to sum exactly to 1.0
    if total_prob > 0:
        for k in matrix:
            matrix[k] /= total_prob
            
    return matrix

def calculate_elo_1x2(home_elo: float, away_elo: float) -> Dict[str, float]:
    """
    Calculates direct 1X2 win/draw/away probabilities from home and away Elo ratings.
    """
    elo_diff = home_elo - away_elo
    e_h = 1.0 / (1.0 + math.pow(10.0, -elo_diff / 400.0))
    p_draw = 0.26 * math.exp(-((elo_diff / 150.0) ** 2))
    p_draw = max(0.10, min(0.35, p_draw))
    rem = 1.0 - p_draw
    p_home = rem * e_h
    p_away = rem * (1.0 - e_h)
    
    # Normalize to 4 decimal places
    h = round(p_home, 4)
    d = round(p_draw, 4)
    a = round(p_away, 4)
    tot = h + d + a
    diff = 1.0 - tot
    if h >= d and h >= a:
        h += diff
    elif d >= h and d >= a:
        d += diff
    else:
        a += diff
        
    return {
        "home_win_probability": round(h, 4),
        "draw_probability": round(d, 4),
        "away_win_probability": round(a, 4)
    }


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

def _calculate_asian_handicap_cover_probability(
    matrix: Dict[str, float],
    line: float,
    is_home_fav: bool
) -> float:
    """
    Helper function to calculate cover probability for a single Asian Handicap line.
    
    Args:
        matrix: Poisson probability matrix
        line: Handicap line (e.g., -0.5, 0.25, etc.)
        is_home_fav: Whether home team is favored
        
    Returns:
        Cover probability (0.0 to 1.0)
    """
    cover_prob = 0.0
    for score_str, prob in matrix.items():
        h, a = map(int, score_str.split('-'))
        fav_score = h if is_home_fav else a
        dog_score = a if is_home_fav else h
        goal_diff = fav_score - dog_score
        
        # Calculate cover probability based on line type
        if line == 0:
            # Draw No Bet: win if goal_diff > 0, push if goal_diff == 0
            if goal_diff > 0:
                cover_prob += prob
            elif goal_diff == 0:
                cover_prob += prob * 0.5
        elif line < 0:
            # Negative handicap (favored team)
            abs_line = abs(line)
            if abs_line == 0.25:
                if goal_diff >= 1:
                    cover_prob += prob
                elif goal_diff == 0:
                    cover_prob += prob * 0.5
            elif abs_line == 0.5:
                if goal_diff >= 1:
                    cover_prob += prob
            elif abs_line == 0.75:
                if goal_diff >= 2:
                    cover_prob += prob
                elif goal_diff == 1:
                    cover_prob += prob * 0.5
            elif abs_line == 1.0:
                if goal_diff >= 2:
                    cover_prob += prob
                elif goal_diff == 1:
                    cover_prob += prob
            elif abs_line == 1.25:
                if goal_diff >= 2:
                    cover_prob += prob
                elif goal_diff == 1:
                    cover_prob += prob * 0.5
            elif abs_line == 1.5:
                if goal_diff >= 2:
                    cover_prob += prob
                elif goal_diff == 1:
                    cover_prob += prob * 0.5
            elif abs_line == 1.75:
                if goal_diff >= 3:
                    cover_prob += prob
                elif goal_diff == 2:
                    cover_prob += prob * 0.5
            elif abs_line == 2.0:
                if goal_diff >= 3:
                    cover_prob += prob
                elif goal_diff == 2:
                    cover_prob += prob
            elif abs_line == 2.25:
                if goal_diff >= 3:
                    cover_prob += prob
                elif goal_diff == 2:
                    cover_prob += prob * 0.5
            elif abs_line == 2.5:
                if goal_diff >= 3:
                    cover_prob += prob
                elif goal_diff == 2:
                    cover_prob += prob * 0.5
            elif abs_line == 2.75:
                if goal_diff >= 4:
                    cover_prob += prob
                elif goal_diff == 3:
                    cover_prob += prob * 0.5
            elif abs_line == 3.0:
                if goal_diff >= 4:
                    cover_prob += prob
                elif goal_diff == 3:
                    cover_prob += prob
        else:
            # Positive handicap (underdog team)
            if line == 0.25:
                if goal_diff >= 0:
                    cover_prob += prob
                elif goal_diff == -1:
                    cover_prob += prob * 0.5
            elif line == 0.5:
                if goal_diff >= 0:
                    cover_prob += prob
            elif line == 0.75:
                if goal_diff >= 0:
                    cover_prob += prob
                elif goal_diff == -1:
                    cover_prob += prob * 0.5
            elif line == 1.0:
                if goal_diff >= -1:
                    cover_prob += prob
            elif line == 1.25:
                if goal_diff >= -1:
                    cover_prob += prob
                elif goal_diff == -2:
                    cover_prob += prob * 0.5
            elif line == 1.5:
                if goal_diff >= -1:
                    cover_prob += prob
                elif goal_diff == -2:
                    cover_prob += prob * 0.5
            elif line == 1.75:
                if goal_diff >= -2:
                    cover_prob += prob
                elif goal_diff == -3:
                    cover_prob += prob * 0.5
            elif line == 2.0:
                if goal_diff >= -2:
                    cover_prob += prob
            elif line == 2.25:
                if goal_diff >= -2:
                    cover_prob += prob
                elif goal_diff == -3:
                    cover_prob += prob * 0.5
            elif line == 2.5:
                if goal_diff >= -2:
                    cover_prob += prob
                elif goal_diff == -3:
                    cover_prob += prob * 0.5
            elif line == 2.75:
                if goal_diff >= -3:
                    cover_prob += prob
                elif goal_diff == -4:
                    cover_prob += prob * 0.5
            elif line == 3.0:
                if goal_diff >= -3:
                    cover_prob += prob
    
    return cover_prob

def _get_expected_goal_difference(matrix: Dict[str, float]) -> Tuple[float, bool]:
    """
    Helper function to calculate expected goal difference from matrix.
    
    Returns:
        (diff, is_home_fav) where diff is expected_home - expected_away
    """
    exp_home = 0.0
    exp_away = 0.0
    for score_str, prob in matrix.items():
        h, a = map(int, score_str.split('-'))
        exp_home += h * prob
        exp_away += a * prob
    
    diff = exp_home - exp_away
    is_home_fav = diff >= 0
    return diff, is_home_fav

def get_asian_handicap_probabilities_from_matrix(matrix: Dict[str, float]) -> Dict[str, Any]:
    """
    Calculates the suggested Asian Handicap lines and probability of covering each line from a final score matrix.
    
    Reuses helper functions to avoid code duplication.
    """
    diff, is_home_fav = _get_expected_goal_difference(matrix)
    prefix = "Home" if is_home_fav else "Away"
    
    # Lines to generate (legacy limited set)
    lines = [-0.25, -0.5, -0.75, -1.0]
    
    results = {}
    for line in lines:
        cover_prob = _calculate_asian_handicap_cover_probability(matrix, line, is_home_fav)
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

def get_double_chance_probabilities(matrix: Dict[str, float]) -> Dict[str, float]:
    """
    Calculates Double Chance probabilities by summing appropriate scoreline probabilities.
    
    - 1X: Home Win or Draw = P(home wins) + P(draw)
    - 12: Home Win or Away Win = P(home wins) + P(away wins)
    - X2: Draw or Away Win = P(draw) + P(away wins)
    
    Reuses get_1x2_probabilities to avoid duplicate matrix iteration.
    """
    outcome_probs = get_1x2_probabilities(matrix)
    home_win = outcome_probs["home_win_probability"]
    draw = outcome_probs["draw_probability"]
    away_win = outcome_probs["away_win_probability"]
    
    # Calculate double chance probabilities
    one_x = home_win + draw  # Home Win or Draw
    one_two = home_win + away_win  # Home Win or Away Win
    x_two = draw + away_win  # Draw or Away Win
    
    return {
        "1x": round(one_x, 4),
        "12": round(one_two, 4),
        "x2": round(x_two, 4),
    }

def get_draw_no_bet_probabilities(matrix: Dict[str, float]) -> Dict[str, float]:
    """
    Calculates Draw No Bet (DNB) probabilities by excluding draw probability and normalizing.
    
    Home DNB = Home Win / (Home Win + Away Win)
    Away DNB = Away Win / (Home Win + Away Win)
    
    Reuses get_1x2_probabilities to avoid duplicate matrix iteration.
    """
    outcome_probs = get_1x2_probabilities(matrix)
    home_win = outcome_probs["home_win_probability"]
    away_win = outcome_probs["away_win_probability"]
    
    # Normalize excluding draw probability
    total_non_draw = home_win + away_win
    
    if total_non_draw > 0:
        home_dnb = home_win / total_non_draw
        away_dnb = away_win / total_non_draw
    else:
        # Edge case: all draws
        home_dnb = 0.5
        away_dnb = 0.5
    
    return {
        "home": round(home_dnb, 4),
        "away": round(away_dnb, 4),
    }

def get_win_to_nil_probabilities(matrix: Dict[str, float]) -> Dict[str, float]:
    """
    Calculates Win To Nil probabilities using the existing Poisson score matrix.
    
    P(Home wins AND Away scores 0) = Sum of probabilities where home > away AND away = 0
    P(Away wins AND Home scores 0) = Sum of probabilities where away > home AND home = 0
    """
    home_win_to_nil = 0.0
    away_win_to_nil = 0.0
    
    for score, p in matrix.items():
        parts = score.split('-')
        h = int(parts[0])
        a = int(parts[1])
        
        # Home wins and away scores 0
        if h > a and a == 0:
            home_win_to_nil += p
        
        # Away wins and home scores 0
        if a > h and h == 0:
            away_win_to_nil += p
    
    return {
        "home": round(home_win_to_nil, 4),
        "away": round(away_win_to_nil, 4),
    }

def get_winning_margin_probabilities(matrix: Dict[str, float]) -> Dict[str, Dict[str, float]]:
    """
    Calculates Winning Margin probabilities for home and away teams.
    
    Returns probabilities for:
    - 1_goal: win by exactly 1 goal
    - 2_goals: win by exactly 2 goals
    - 3_plus: win by 3 or more goals
    """
    home_1_goal = 0.0
    home_2_goals = 0.0
    home_3_plus = 0.0
    away_1_goal = 0.0
    away_2_goals = 0.0
    away_3_plus = 0.0
    
    for score, p in matrix.items():
        parts = score.split('-')
        h = int(parts[0])
        a = int(parts[1])
        margin = h - a
        
        if margin == 1:
            home_1_goal += p
        elif margin == 2:
            home_2_goals += p
        elif margin >= 3:
            home_3_plus += p
        elif margin == -1:
            away_1_goal += p
        elif margin == -2:
            away_2_goals += p
        elif margin <= -3:
            away_3_plus += p
    
    return {
        "home": {
            "1_goal": round(home_1_goal, 4),
            "2_goals": round(home_2_goals, 4),
            "3_plus": round(home_3_plus, 4),
        },
        "away": {
            "1_goal": round(away_1_goal, 4),
            "2_goals": round(away_2_goals, 4),
            "3_plus": round(away_3_plus, 4),
        },
    }

def get_goal_range_probabilities(matrix: Dict[str, float]) -> Dict[str, float]:
    """
    Calculates Goal Range probabilities based on total goals in every scoreline.
    
    Returns:
    - 0_goals: P(total goals = 0)
    - 1_goal: P(total goals = 1)
    - 2_goals: P(total goals = 2)
    - 3_goals: P(total goals = 3)
    - 4_goals: P(total goals = 4)
    - 5_plus: P(total goals >= 5)
    """
    goal_ranges = {
        "0_goals": 0.0,
        "1_goal": 0.0,
        "2_goals": 0.0,
        "3_goals": 0.0,
        "4_goals": 0.0,
        "5_plus": 0.0,
    }
    
    for score, p in matrix.items():
        parts = score.split('-')
        h = int(parts[0])
        a = int(parts[1])
        total = h + a
        
        if total == 0:
            goal_ranges["0_goals"] += p
        elif total == 1:
            goal_ranges["1_goal"] += p
        elif total == 2:
            goal_ranges["2_goals"] += p
        elif total == 3:
            goal_ranges["3_goals"] += p
        elif total == 4:
            goal_ranges["4_goals"] += p
        elif total >= 5:
            goal_ranges["5_plus"] += p
    
    return {k: round(v, 4) for k, v in goal_ranges.items()}

def get_full_correct_score_matrix(matrix: Dict[str, float]) -> List[Dict[str, Any]]:
    """
    Returns the full correct score matrix from 0-0 through 6-6, sorted by probability descending.
    
    This includes every scoreline in the matrix, not just the top 5.
    """
    # Filter scores within 0-6 range for both teams
    filtered_scores = []
    for score_str, prob in matrix.items():
        parts = score_str.split('-')
        h = int(parts[0])
        a = int(parts[1])
        if h <= 6 and a <= 6:
            filtered_scores.append({
                "score": score_str,
                "probability": round(prob, 4)
            })
    
    # Sort by probability descending
    filtered_scores.sort(key=lambda x: x["probability"], reverse=True)
    
    return filtered_scores

def get_expanded_asian_handicap_probabilities(matrix: Dict[str, float]) -> Dict[str, Any]:
    """
    Calculates expanded Asian Handicap lines from -3.0 to +3.0 in 0.25 increments.
    
    Returns probabilities for every line using the existing score probability matrix.
    Reuses helper functions to avoid code duplication.
    """
    diff, is_home_fav = _get_expected_goal_difference(matrix)
    prefix = "Home" if is_home_fav else "Away"
    
    # Expanded lines from -3.0 to +3.0 in 0.25 increments
    lines = [-3.0, -2.75, -2.5, -2.25, -2.0, -1.75, -1.5, -1.25, -1.0, -0.75, -0.5, -0.25, 0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0]
    
    results = {}
    for line in lines:
        cover_prob = _calculate_asian_handicap_cover_probability(matrix, line, is_home_fav)
        results[f"{prefix} {line}"] = round(cover_prob, 4)
    
    return {
        "favored_team_prefix": prefix,
        "suggested_lines": results
    }

def get_expanded_over_under_probabilities(matrix: Dict[str, float]) -> Dict[str, Dict[str, float]]:
    """
    Calculates expanded Over/Under probabilities for 0.5 through 7.5 lines.
    
    For a line like 1.5:
    - Under: total goals < 1.5 (i.e., 0 or 1 goals)
    - Over: total goals >= 1.5 (i.e., 2 or more goals)
    """
    results = {}
    for line in (0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5):
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
    over_under      = get_expanded_over_under_probabilities(matrix)  # Use expanded version
    asian_handicap  = get_expanded_asian_handicap_probabilities(matrix)  # Use expanded version
    team_goals      = get_team_goals_probabilities_from_matrix(matrix, current_home_score, current_away_score)
    clean_sheet     = get_clean_sheet_probabilities_from_matrix(matrix, current_home_score, current_away_score)
    outcome_probs   = get_1x2_probabilities(matrix)
    
    # New derived markets
    double_chance   = get_double_chance_probabilities(matrix)
    draw_no_bet     = get_draw_no_bet_probabilities(matrix)
    win_to_nil      = get_win_to_nil_probabilities(matrix)
    winning_margin  = get_winning_margin_probabilities(matrix)
    goal_range      = get_goal_range_probabilities(matrix)
    full_correct_score_matrix = get_full_correct_score_matrix(matrix)

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
        # New derived markets
        "double_chance":      double_chance,
        "draw_no_bet":        draw_no_bet,
        "win_to_nil":         win_to_nil,
        "winning_margin":     winning_margin,
        "goal_range":         goal_range,
        "correct_score_matrix": full_correct_score_matrix,
    }
