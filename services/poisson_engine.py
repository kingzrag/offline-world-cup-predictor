# services/poisson_engine.py
"""
Poisson Probability Engine for Football Match Betting Markets.
Calculates Correct Score, BTTS, Over/Under, Asian Handicap, and Team Goals
probabilities using independent Poisson distributions on expected home/away goals.
"""

import math
import scipy.stats
from typing import Dict, Any, List, Tuple

def get_poisson_probability(lmbda: float, k: int) -> float:
    """Calculates Poisson probability for k events with mean lmbda."""
    return float(scipy.stats.poisson.pmf(k, lmbda))

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

def get_btts_probabilities(expected_home_goals: float, expected_away_goals: float) -> Dict[str, float]:
    """
    Calculates BTTS Yes and No probabilities.
    """
    lam_h = max(0.0001, expected_home_goals)
    lam_a = max(0.0001, expected_away_goals)
    
    # P(H > 0) = 1 - P(H = 0)
    p_h_gt_0 = 1.0 - get_poisson_probability(lam_h, 0)
    p_a_gt_0 = 1.0 - get_poisson_probability(lam_a, 0)
    
    btts_yes = p_h_gt_0 * p_a_gt_0
    btts_no = 1.0 - btts_yes
    
    return {
        "btts_yes": round(btts_yes, 4),
        "btts_no": round(btts_no, 4)
    }

def get_over_under_probabilities(expected_home_goals: float, expected_away_goals: float) -> Dict[str, Dict[str, float]]:
    """
    Calculates Over/Under probabilities for 1.5, 2.5, and 3.5 lines.
    Using total expected goals as lambda since sum of independent Poissons is Poisson.
    """
    total_lambda = max(0.0001, expected_home_goals + expected_away_goals)
    
    # Under 1.5: H+A <= 1
    under_1_5 = float(scipy.stats.poisson.cdf(1, total_lambda))
    over_1_5 = 1.0 - under_1_5
    
    # Under 2.5: H+A <= 2
    under_2_5 = float(scipy.stats.poisson.cdf(2, total_lambda))
    over_2_5 = 1.0 - under_2_5
    
    # Under 3.5: H+A <= 3
    under_3_5 = float(scipy.stats.poisson.cdf(3, total_lambda))
    over_3_5 = 1.0 - under_3_5
    
    return {
        "1.5": {"over": round(over_1_5, 4), "under": round(under_1_5, 4)},
        "2.5": {"over": round(over_2_5, 4), "under": round(under_2_5, 4)},
        "3.5": {"over": round(over_3_5, 4), "under": round(under_3_5, 4)}
    }

def get_asian_handicap_probabilities(expected_home_goals: float, expected_away_goals: float, matrix: Dict[str, float]) -> Dict[str, Any]:
    """
    Calculates the suggested Asian Handicap lines and probability of covering each line.
    Suggested lines are based on expected goal difference.
    """
    diff = expected_home_goals - expected_away_goals
    is_home_fav = diff >= 0
    prefix = "Home" if is_home_fav else "Away"
    
    # Lines to generate
    lines = [-0.25, -0.5, -0.75, -1.0]
    
    results = {}
    # We will sum probabilities from the joint matrix
    # P(cover) calculations:
    for line in lines:
        cover_prob = 0.0
        # Line is negative (e.g. -0.25)
        # For a given score (h, a), the net difference for favorite team is:
        # If Home is favorite: net = h - a + line
        # If Away is favorite: net = a - h + line
        # Covers fully if net > 0. Covers half if net == 0.25 (which does not happen for -0.25, -0.5, -0.75, -1.0)
        # Wait, let's look at the payoffs:
        # -0.25: net = Diff - 0.25. If Diff >= 1, wins fully. If Diff == 0 (draw), half stake lost (refund half, lose half).
        #        Let's define cover probability as P(Diff >= 1) + 0.5 * P(Diff == 0) if we want expected payoff,
        #        or just P(Diff >= 1) for winning cover. Let's use P(Diff >= 1) as the strict cover, or expected payoff.
        #        Actually, the standard definition of cover probability is P(win the bet fully or half-win).
        #        Let's code it explicitly:
        #        For -0.25: Win if Diff >= 1.
        #        For -0.5: Win if Diff >= 1.
        #        For -0.75: Win if Diff >= 2. Half-win if Diff == 1. cover_prob = P(Diff >= 2) + 0.5 * P(Diff == 1).
        #        For -1.0: Win if Diff >= 2. Push if Diff == 1. cover_prob = P(Diff >= 2).
        
        for score_str, prob in matrix.items():
            h, a = map(int, score_str.split('-'))
            fav_score = h if is_home_fav else a
            dog_score = a if is_home_fav else h
            goal_diff = fav_score - dog_score
            
            # Evaluate covering based on line
            if line == -0.25:
                # Win if goal_diff >= 1. Half-loss (refund 0.5) if goal_diff == 0.
                # Let's count full win.
                if goal_diff >= 1:
                    cover_prob += prob
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
                # Full win if goal_diff >= 2. Push if goal_diff == 1 (refunded, so in terms of covering without losing, we could count it, but winning probability is goal_diff >= 2).
                if goal_diff >= 2:
                    cover_prob += prob
                    
        results[f"{prefix} {line}"] = round(cover_prob, 4)
        
    return {
        "favored_team_prefix": prefix,
        "suggested_lines": results
    }

def get_team_goals_probabilities(expected_home_goals: float, expected_away_goals: float) -> Dict[str, Dict[str, float]]:
    """
    Calculates Over probabilities for Team Goals (0.5, 1.5, 2.5).
    """
    lam_h = max(0.0001, expected_home_goals)
    lam_a = max(0.0001, expected_away_goals)
    
    # Home Team Over
    home_over_0_5 = 1.0 - float(scipy.stats.poisson.cdf(0, lam_h))
    home_over_1_5 = 1.0 - float(scipy.stats.poisson.cdf(1, lam_h))
    home_over_2_5 = 1.0 - float(scipy.stats.poisson.cdf(2, lam_h))
    
    # Away Team Over
    away_over_0_5 = 1.0 - float(scipy.stats.poisson.cdf(0, lam_a))
    away_over_1_5 = 1.0 - float(scipy.stats.poisson.cdf(1, lam_a))
    away_over_2_5 = 1.0 - float(scipy.stats.poisson.cdf(2, lam_a))
    
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

def evaluate_poisson_engine(expected_home_goals: float, expected_away_goals: float) -> Dict[str, Any]:
    """
    Main entry point to calculate all markets from expected goals.
    """
    matrix = calculate_probability_matrix(expected_home_goals, expected_away_goals)
    
    # Filter matrix to the requested scorelines for Step 7:
    requested_scores = [
        "0-0", "1-0", "1-1", "2-0", "2-1", "2-2", "3-0", "3-1", "3-2", "3-3", "4-0", "4-1", "4-2", "4-3", "4-4"
    ]
    prob_matrix_subset = {score: round(matrix.get(score, 0.0), 4) for score in requested_scores}
    
    correct_scores = get_correct_scores(matrix)
    btts = get_btts_probabilities(expected_home_goals, expected_away_goals)
    over_under = get_over_under_probabilities(expected_home_goals, expected_away_goals)
    asian_handicap = get_asian_handicap_probabilities(expected_home_goals, expected_away_goals, matrix)
    team_goals = get_team_goals_probabilities(expected_home_goals, expected_away_goals)
    
    return {
        "probability_matrix": prob_matrix_subset,
        "most_likely_score": correct_scores["most_likely_score"],
        "top_5_scorelines": correct_scores["top_5_scorelines"],
        "btts": btts,
        "over_under": over_under,
        "asian_handicap": asian_handicap,
        "team_goals": team_goals
    }
