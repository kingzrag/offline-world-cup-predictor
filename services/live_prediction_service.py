"""
Dynamic Live Match Prediction Engine (Version 1)

This service provides live prediction adjustments based on match state.
It sits between the existing pre-match ML pipeline and the Poisson Engine.

Key Principles:
- No database writes (calculations are in-memory)
- No schema changes
- No ML model retraining
- Poisson Engine remains unchanged
- All configurable weights in one location
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from services.poisson_engine import evaluate_poisson_engine
from utils.logger import logger


@dataclass
class LiveMatchState:
    """
    Current live match state from the database.
    All fields are optional to handle missing data gracefully.
    """
    current_minute: int
    current_home_score: int
    current_away_score: int
    home_red_cards: int
    away_red_cards: int
    
    # Derived fields (computed in __post_init__)
    remaining_minutes: int = 0
    score_diff: int = 0
    red_cards_diff: int = 0
    
    def __post_init__(self):
        """Compute derived fields."""
        self.remaining_minutes = max(90 - self.current_minute, 1)
        self.score_diff = self.current_home_score - self.current_away_score
        self.red_cards_diff = self.home_red_cards - self.away_red_cards


@dataclass
class PreMatchContext:
    """
    Pre-match context from the database.
    Contains the original prediction and team strength information.
    """
    original_home_xg: float
    original_away_xg: float
    strength_diff: float  # Positive = home stronger, Negative = away stronger
    is_home_match: bool = True  # Always true from home team perspective


@dataclass
class MatchStateWeights:
    """
    All configurable weights for the Match State Engine.
    
    These weights control how much each factor influences the final match state score.
    All weights are centralized here for easy tuning.
    """
    # Component weights (must sum to 1.0 for normalization)
    time_weight: float = 0.30
    score_weight: float = 0.35
    card_weight: float = 0.20  # Calibrated: Increased from 0.15 for better red card impact
    strength_weight: float = 0.14  # Calibrated: Increased from 0.10 for better strength influence
    home_advantage_weight: float = 0.10
    
    # xG adjustment coefficients
    xg_adjustment_factor: float = 0.5  # How much match state affects xG
    min_xg: float = 0.05  # Minimum xG to prevent zero probabilities
    
    # Time-based xG decay
    time_decay_power: float = 1.2  # Power function for time decay curve
    # 1.0 = Gentle decay (linear)
    # 1.2 = Moderate decay (default)
    # 1.5 = Aggressive decay (exponential)
    
    # Component-specific coefficients
    goal_impact_base: float = 0.3  # Base xG adjustment per goal
    goal_time_sensitivity: float = 0.5  # How much time affects goal impact
    red_card_penalty: float = 0.25  # xG reduction per red card
    red_card_time_decay: float = 0.8  # How much red card impact decays over time
    
    # Score-aware xG reduction parameters
    # These control how the current score influences remaining attacking intent
    score_leading_protection: float = 0.3  # How much a lead protects xG from decay (0.0-1.0)
    score_trailing_boost: float = 0.2  # How much trailing increases attacking intent (0.0-1.0)
    score_margin_sensitivity: float = 0.5  # How sensitive the system is to score margin (0.0-1.0)
    
    # Strength influence on attacking intent
    strength_comeback_factor: float = 0.15  # How much strength helps comeback attempts (0.0-1.0)
    
    # Red card influence on attacking intent
    red_card_attacking_reduction: float = 0.2  # How much red cards reduce attacking intent (0.0-1.0)
    
    @classmethod
    def default(cls) -> "MatchStateWeights":
        """Return default weights."""
        return cls()
    
    @classmethod
    def conservative(cls) -> "MatchStateWeights":
        """Return more conservative weights (smaller adjustments)."""
        return cls(
            time_weight=0.25,
            score_weight=0.30,
            card_weight=0.15,  # Slightly lower than default
            strength_weight=0.12,  # Slightly lower than default
            home_advantage_weight=0.20,
            xg_adjustment_factor=0.3,
        )
    
    @classmethod
    def aggressive(cls) -> "MatchStateWeights":
        """Return more aggressive weights (larger adjustments)."""
        return cls(
            time_weight=0.35,
            score_weight=0.40,
            card_weight=0.25,  # Higher than default
            strength_weight=0.18,  # Higher than default
            home_advantage_weight=0.00,
            xg_adjustment_factor=0.7,
        )


@dataclass
class MatchStateScore:
    """
    Result of the central Match State Engine.
    
    total_score: Overall match state (-1.0 to 1.0)
      - Positive: Home team advantage increased
      - Negative: Away team advantage increased
      - Magnitude: How strong the advantage is
    
    Individual components are included for debugging and transparency.
    """
    total_score: float
    time_component: float
    score_component: float
    card_component: float
    strength_component: float
    home_advantage_component: float


# ============================================================================
# Component Functions (Pure, Testable)
# ============================================================================

def _calculate_time_component(elapsed_minutes: int, remaining_minutes: int) -> float:
    """
    Calculate time decay component (0.0 to 1.0).
    
    As the match progresses, time increases from 0.0 to 1.0.
    This reflects that later events have more impact on the final result.
    """
    if elapsed_minutes >= 90:
        return 1.0
    return elapsed_minutes / 90.0


def _calculate_score_component(score_diff: int, elapsed_minutes: int) -> float:
    """
    Calculate score difference component (0.0 to 1.0).
    
    Goals have more impact later in the match.
    A goal at 85' is more significant than a goal at 5'.
    """
    # Time factor: Goals have more impact later
    time_factor = elapsed_minutes / 90.0
    
    # Base impact based on score difference (capped at 3 goals)
    base_impact = min(abs(score_diff) / 3.0, 1.0)
    
    # Combine: Later goals amplify the impact
    return base_impact * (0.5 + 0.5 * time_factor)


def _calculate_card_component(red_cards_diff: int, elapsed_minutes: int) -> float:
    """
    Calculate red card component (0.0 to 1.0).
    
    Red cards have less impact later in the match because there's less time
    for the numerical advantage to translate into goals.
    """
    # Time factor: Red cards have less impact later
    time_factor = 1.0 - (elapsed_minutes / 90.0) * 0.5
    
    # Base impact based on red card difference (capped at 2 cards)
    base_impact = min(abs(red_cards_diff) / 2.0, 1.0)
    
    # Combine: Earlier red cards have more impact
    return base_impact * time_factor


def _calculate_strength_component(strength_diff: float) -> float:
    """
    Calculate team strength component (0.0 to 1.0).
    
    Strength difference is based on FIFA ranking, ELO, or squad value.
    Stronger teams are more resilient to setbacks.
    """
    # Normalize strength difference (capped at 20 FIFA ranking points)
    return min(abs(strength_diff) / 20.0, 1.0)


def _calculate_home_advantage_component(is_home_match: bool) -> float:
    """
    Calculate home advantage component (0.0 or 1.0).
    
    Always 1.0 from home team perspective in this implementation.
    """
    return 1.0 if is_home_match else 0.0


# ============================================================================
# Central Match State Engine (Single Brain Function)
# ============================================================================

def calculate_match_state(
    live_state: LiveMatchState,
    pre_match_context: PreMatchContext,
    weights: MatchStateWeights
) -> MatchStateScore:
    """
    Central function that combines all match factors into a single Match State Score.
    
    This is the single "brain" of the live prediction system.
    All football logic flows through this one function.
    
    Args:
        live_state: Current live match state
        pre_match_context: Pre-match context (original prediction, team strength)
        weights: Configurable weights for each component
    
    Returns:
        MatchStateScore with total score and individual components
    """
    # Calculate individual components
    time_component = _calculate_time_component(
        elapsed_minutes=live_state.current_minute,
        remaining_minutes=live_state.remaining_minutes
    )
    
    score_component = _calculate_score_component(
        score_diff=live_state.score_diff,
        elapsed_minutes=live_state.current_minute
    )
    
    card_component = _calculate_card_component(
        red_cards_diff=live_state.red_cards_diff,
        elapsed_minutes=live_state.current_minute
    )
    
    strength_component = _calculate_strength_component(
        strength_diff=pre_match_context.strength_diff
    )
    
    home_advantage_component = _calculate_home_advantage_component(
        is_home_match=pre_match_context.is_home_match
    )
    
    # Determine direction of each component
    # Positive components favor home, negative favor away
    score_direction = 1.0 if live_state.score_diff > 0 else -1.0 if live_state.score_diff < 0 else 0.0
    card_direction = -1.0 if live_state.red_cards_diff > 0 else 1.0 if live_state.red_cards_diff < 0 else 0.0
    strength_direction = 1.0 if pre_match_context.strength_diff > 0 else -1.0 if pre_match_context.strength_diff < 0 else 0.0
    
    # Combine using configurable weights
    total_score = (
        (time_component * 0.0) * weights.time_weight +  # Time is neutral, just affects magnitude
        (score_component * score_direction) * weights.score_weight +
        (card_component * card_direction) * weights.card_weight +
        (strength_component * strength_direction) * weights.strength_weight +
        (home_advantage_component * 0.1) * weights.home_advantage_weight  # Small home advantage bonus
    )
    
    return MatchStateScore(
        total_score=total_score,
        time_component=time_component,
        score_component=score_component,
        card_component=card_component,
        strength_component=strength_component,
        home_advantage_component=home_advantage_component,
    )


# ============================================================================
# Score-Aware Attacking Intent Functions
# ============================================================================

def _calculate_score_protection_factor(
    current_home_score: int,
    current_away_score: int,
    weights: MatchStateWeights
) -> tuple[float, float]:
    """
    Calculate how much the current score protects xG from time-based decay.
    
    Teams with large leads have less incentive to attack aggressively,
    so their xG should decay more slowly. Teams trailing have more incentive
    to attack, so their xG should decay more slowly (or even increase).
    
    Mathematical Model:
    - Score margin = abs(home_score - away_score)
    - Normalized margin = min(score_margin / 3.0, 1.0)  # Cap at 3 goals
    - Protection factor = normalized_margin * score_leading_protection
    
    For the trailing team:
    - Trailing boost = normalized_margin * score_trailing_boost
    
    Args:
        current_home_score: Current home team score
        current_away_score: Current away team score
        weights: Configurable weights
    
    Returns:
        Tuple of (home_protection, away_protection) where:
        - home_protection: How much home xG is protected (0.0-1.0)
        - away_protection: How much away xG is protected (0.0-1.0)
    """
    score_diff = current_home_score - current_away_score
    abs_score_diff = abs(score_diff)
    
    # Normalize score margin (capped at 3 goals for realism)
    normalized_margin = min(abs_score_diff / 3.0, 1.0)
    
    # Apply sensitivity parameter
    sensitive_margin = normalized_margin * weights.score_margin_sensitivity
    
    if score_diff > 0:
        # Home is leading
        home_protection = sensitive_margin * weights.score_leading_protection
        away_protection = sensitive_margin * weights.score_trailing_boost
    elif score_diff < 0:
        # Away is leading
        home_protection = sensitive_margin * weights.score_trailing_boost
        away_protection = sensitive_margin * weights.score_leading_protection
    else:
        # Draw - no protection or boost
        home_protection = 0.0
        away_protection = 0.0
    
    return home_protection, away_protection


def _calculate_strength_comeback_bonus(
    strength_diff: float,
    current_home_score: int,
    current_away_score: int,
    weights: MatchStateWeights
) -> tuple[float, float]:
    """
    Calculate how much team strength helps comeback attempts.
    
    Stronger teams are more likely to successfully mount comebacks when trailing.
    This function returns a bonus factor that reduces xG decay for the trailing
    team based on their strength advantage.
    
    Mathematical Model:
    - If home is stronger (strength_diff > 0) and trailing:
      bonus = (strength_diff / 20.0) * strength_comeback_factor
    - If away is stronger (strength_diff < 0) and trailing:
      bonus = (abs(strength_diff) / 20.0) * strength_comeback_factor
    - Otherwise: bonus = 0.0
    
    Args:
        strength_diff: Team strength difference (home - away)
        current_home_score: Current home team score
        current_away_score: Current away team score
        weights: Configurable weights
    
    Returns:
        Tuple of (home_bonus, away_bonus) where:
        - home_bonus: Bonus for home team comeback attempt (0.0-1.0)
        - away_bonus: Bonus for away team comeback attempt (0.0-1.0)
    """
    score_diff = current_home_score - current_away_score
    normalized_strength = min(abs(strength_diff) / 20.0, 1.0)
    
    home_bonus = 0.0
    away_bonus = 0.0
    
    if score_diff < 0 and strength_diff > 0:
        # Home is trailing but stronger
        home_bonus = normalized_strength * weights.strength_comeback_factor
    elif score_diff > 0 and strength_diff < 0:
        # Away is trailing but stronger
        away_bonus = normalized_strength * weights.strength_comeback_factor
    
    return home_bonus, away_bonus


def _calculate_red_card_attacking_penalty(
    home_red_cards: int,
    away_red_cards: int,
    weights: MatchStateWeights
) -> tuple[float, float]:
    """
    Calculate how red cards reduce attacking intent.
    
    Teams with red cards have reduced attacking capability, so their xG
    should decay more aggressively.
    
    Mathematical Model:
    - home_penalty = home_red_cards * red_card_attacking_reduction
    - away_penalty = away_red_cards * red_card_attacking_reduction
    
    Args:
        home_red_cards: Number of home team red cards
        away_red_cards: Number of away team red cards
        weights: Configurable weights
    
    Returns:
        Tuple of (home_penalty, away_penalty) where:
        - home_penalty: Penalty for home team (0.0-1.0)
        - away_penalty: Penalty for away team (0.0-1.0)
    """
    home_penalty = min(home_red_cards * weights.red_card_attacking_reduction, 1.0)
    away_penalty = min(away_red_cards * weights.red_card_attacking_reduction, 1.0)
    
    return home_penalty, away_penalty


def _calculate_team_specific_time_factor(
    base_time_factor: float,
    protection: tuple[float, float],
    bonus: tuple[float, float],
    penalty: tuple[float, float]
) -> tuple[float, float]:
    """
    Calculate team-specific time factors based on score, strength, and cards.
    
    This combines the base time decay with score-aware adjustments to produce
    individual time factors for each team.
    
    Mathematical Model:
    - protected_time_factor = base_time_factor * (1.0 - protection) + protection
    - boosted_time_factor = protected_time_factor * (1.0 + bonus)
    - final_time_factor = boosted_time_factor * (1.0 - penalty)
    
    The protection factor ensures that teams with leads don't lose all their xG.
    The bonus factor helps trailing teams maintain attacking intent.
    The penalty factor reduces xG for teams with red cards.
    
    Args:
        base_time_factor: Base time decay factor (0.0-1.0)
        protection: Tuple of (home_protection, away_protection)
        bonus: Tuple of (home_bonus, away_bonus)
        penalty: Tuple of (home_penalty, away_penalty)
    
    Returns:
        Tuple of (home_time_factor, away_time_factor)
    """
    home_protection, away_protection = protection
    home_bonus, away_bonus = bonus
    home_penalty, away_penalty = penalty
    
    # Apply protection (teams with leads retain more xG)
    home_protected = base_time_factor * (1.0 - home_protection) + home_protection
    away_protected = base_time_factor * (1.0 - away_protection) + away_protection
    
    # Apply bonus (trailing teams maintain attacking intent)
    home_boosted = home_protected * (1.0 + home_bonus)
    away_boosted = away_protected * (1.0 + away_bonus)
    
    # Apply penalty (red cards reduce attacking intent)
    home_final = max(home_boosted * (1.0 - home_penalty), 0.01)  # Minimum 1%
    away_final = max(away_boosted * (1.0 - away_penalty), 0.01)  # Minimum 1%
    
    return home_final, away_final


# ============================================================================
# xG Adjustment
# ============================================================================

def adjust_xg_from_match_state(
    original_home_xg: float,
    original_away_xg: float,
    match_state: MatchStateScore,
    weights: MatchStateWeights,
    elapsed_minutes: int,
    current_home_score: int,
    current_away_score: int,
    home_red_cards: int,
    away_red_cards: int,
    strength_diff: float,
) -> tuple[float, float]:
    """
    Adjust expected goals based on match state score and remaining time.
    
    This function applies three adjustments:
    1. Score-aware time-based xG reduction: As remaining time decreases, expected goals decrease
       - Teams with leads have protected xG (less decay)
       - Teams trailing have boosted xG (more attacking intent)
       - Red cards reduce attacking intent (more decay)
    2. Strength-based comeback bonus: Stronger teams get bonus when trailing
    3. Match state adjustment: Goals, cards, strength affect xG
    
    The match state score determines the magnitude and direction of xG adjustment.
    Positive score favors home, negative favors away.
    
    Args:
        original_home_xg: Original pre-match home xG
        original_away_xg: Original pre-match away xG
        match_state: Calculated match state score
        weights: Configurable weights
        elapsed_minutes: Current match minute
        current_home_score: Current home team score
        current_away_score: Current away team score
        home_red_cards: Home team red cards
        away_red_cards: Away team red cards
        strength_diff: Team strength difference (home - away)
    
    Returns:
        Tuple of (adjusted_home_xg, adjusted_away_xg)
    """
    # Step 1: Calculate base time factor
    remaining_minutes = max(90 - elapsed_minutes, 1)
    base_time_factor = (remaining_minutes / 90) ** weights.time_decay_power
    
    # Step 2: Calculate score-aware adjustments
    # Score protection: Teams with leads retain more xG
    protection = _calculate_score_protection_factor(
        current_home_score=current_home_score,
        current_away_score=current_away_score,
        weights=weights
    )
    
    # Strength bonus: Stronger teams get comeback bonus when trailing
    bonus = _calculate_strength_comeback_bonus(
        strength_diff=strength_diff,
        current_home_score=current_home_score,
        current_away_score=current_away_score,
        weights=weights
    )
    
    # Red card penalty: Teams with red cards have reduced attacking intent
    penalty = _calculate_red_card_attacking_penalty(
        home_red_cards=home_red_cards,
        away_red_cards=away_red_cards,
        weights=weights
    )
    
    # Step 3: Calculate team-specific time factors
    home_time_factor, away_time_factor = _calculate_team_specific_time_factor(
        base_time_factor=base_time_factor,
        protection=protection,
        bonus=bonus,
        penalty=penalty
    )
    
    # Step 4: Apply team-specific time factors to original xG
    time_adjusted_home_xg = original_home_xg * home_time_factor
    time_adjusted_away_xg = original_away_xg * away_time_factor
    
    logger.debug(
        f"[LIVE_PREDICTION] Score-aware xG reduction: "
        f"elapsed={elapsed_minutes}, remaining={remaining_minutes}, "
        f"base_time_factor={base_time_factor:.4f}, "
        f"home_time_factor={home_time_factor:.4f}, "
        f"away_time_factor={away_time_factor:.4f}, "
        f"home {original_home_xg:.4f} → {time_adjusted_home_xg:.4f}, "
        f"away {original_away_xg:.4f} → {time_adjusted_away_xg:.4f}, "
        f"protection={protection}, bonus={bonus}, penalty={penalty}"
    )
    
    # Step 5: Apply match state adjustments (goals, cards, strength)
    # Match state score determines adjustment magnitude
    adjustment = match_state.total_score * weights.xg_adjustment_factor
    
    # Apply adjustment to time-adjusted xG
    # Positive adjustment increases home xG, decreases away xG
    # Negative adjustment decreases home xG, increases away xG
    adjusted_home_xg = time_adjusted_home_xg * (1.0 + adjustment)
    adjusted_away_xg = time_adjusted_away_xg * (1.0 - adjustment)
    
    # Ensure minimum values to prevent zero probabilities
    adjusted_home_xg = max(weights.min_xg, adjusted_home_xg)
    adjusted_away_xg = max(weights.min_xg, adjusted_away_xg)
    
    logger.debug(
        f"[LIVE_PREDICTION] Final xG adjustment: "
        f"home {time_adjusted_home_xg:.4f} → {adjusted_home_xg:.4f}, "
        f"away {time_adjusted_away_xg:.4f} → {adjusted_away_xg:.4f}, "
        f"match_state={match_state.total_score:.4f}"
    )
    
    return adjusted_home_xg, adjusted_away_xg


# ============================================================================
# Live Prediction Service
# ============================================================================

class LivePredictionService:
    """
    Service for generating live match predictions.
    
    This service:
    1. Reads live match state from database
    2. Reads pre-match prediction from database
    3. Calculates match state score
    4. Adjusts xG based on match state
    5. Calls existing Poisson Engine with adjusted xG
    6. Returns live prediction with metadata
    """
    
    def __init__(self, weights: Optional[MatchStateWeights] = None):
        """
        Initialize the service with optional custom weights.
        
        Args:
            weights: Custom weights, or use default if not provided
        """
        self.weights = weights or MatchStateWeights.default()
        logger.info(f"[LIVE_PREDICTION] Initialized with weights: {self.weights}")
    
    def get_live_prediction(
        self,
        current_minute: int,
        current_home_score: int,
        current_away_score: int,
        home_red_cards: int,
        away_red_cards: int,
        original_home_xg: float,
        original_away_xg: float,
        strength_diff: float,
    ) -> dict:
        """
        Generate a live prediction for a match.
        
        Args:
            current_minute: Current match minute
            current_home_score: Current home score
            current_away_score: Current away score
            home_red_cards: Home red cards
            away_red_cards: Away red cards
            original_home_xg: Original pre-match home xG
            original_away_xg: Original pre-match away xG
            strength_diff: Team strength difference (home - away)
        
        Returns:
            Dictionary containing:
            - Probabilities (home_win, draw, away_win)
            - Expected goals (home, away, total)
            - All betting markets from Poisson Engine
            - Metadata (is_live_prediction, prediction_version, last_prediction_update)
        """
        # Build live state
        live_state = LiveMatchState(
            current_minute=current_minute,
            current_home_score=current_home_score,
            current_away_score=current_away_score,
            home_red_cards=home_red_cards,
            away_red_cards=away_red_cards,
        )
        
        # Build pre-match context
        pre_match_context = PreMatchContext(
            original_home_xg=original_home_xg,
            original_away_xg=original_away_xg,
            strength_diff=strength_diff,
            is_home_match=True,
        )
        
        # Calculate match state score
        match_state = calculate_match_state(
            live_state=live_state,
            pre_match_context=pre_match_context,
            weights=self.weights
        )
        
        logger.info(
            f"[LIVE_PREDICTION] Match state calculated: "
            f"total={match_state.total_score:.4f}, "
            f"time={match_state.time_component:.4f}, "
            f"score={match_state.score_component:.4f}, "
            f"card={match_state.card_component:.4f}, "
            f"strength={match_state.strength_component:.4f}"
        )
        
        # Adjust xG based on match state
        adjusted_home_xg, adjusted_away_xg = adjust_xg_from_match_state(
            original_home_xg=original_home_xg,
            original_away_xg=original_away_xg,
            match_state=match_state,
            weights=self.weights,
            elapsed_minutes=live_state.current_minute,
            current_home_score=live_state.current_home_score,
            current_away_score=live_state.current_away_score,
            home_red_cards=live_state.home_red_cards,
            away_red_cards=live_state.away_red_cards,
            strength_diff=pre_match_context.strength_diff,
        )
        
        # Call existing Poisson Engine with adjusted xG and current score
        poisson_results = evaluate_poisson_engine(
            expected_home_goals=adjusted_home_xg,
            expected_away_goals=adjusted_away_xg,
            current_home_score=live_state.current_home_score,
            current_away_score=live_state.current_away_score
        )
        
        # Build response
        response = {
            "probabilities": {
                "home_win": poisson_results["outcome_probabilities"]["home_win_probability"],
                "draw": poisson_results["outcome_probabilities"]["draw_probability"],
                "away_win": poisson_results["outcome_probabilities"]["away_win_probability"],
            },
            "expected_goals": {
                "home": adjusted_home_xg,
                "away": adjusted_away_xg,
                "total": adjusted_home_xg + adjusted_away_xg,
            },
            "markets": {
                "btts": poisson_results["btts"],
                "over_under": poisson_results["over_under"],
                "correct_score": {
                    "most_likely": poisson_results["most_likely_score"],
                    "top_5": poisson_results["top_5_scorelines"],
                },
                "asian_handicap": poisson_results["asian_handicap"],
                "team_goals": poisson_results["team_goals"],
                "clean_sheet": poisson_results["clean_sheet"],
            },
            "metadata": {
                "is_live_prediction": True,
                "prediction_version": "v1.0-live",
                "last_prediction_update": datetime.utcnow().isoformat(),
                "match_state_score": match_state.total_score,
                "original_home_xg": original_home_xg,
                "original_away_xg": original_away_xg,
            }
        }
        
        logger.info(
            f"[LIVE_PREDICTION] Live prediction generated: "
            f"home_win={response['probabilities']['home_win']:.4f}, "
            f"draw={response['probabilities']['draw']:.4f}, "
            f"away_win={response['probabilities']['away_win']:.4f}"
        )
        
        return response


# ============================================================================
# Convenience Function
# ============================================================================

def get_live_prediction(
    current_minute: int,
    current_home_score: int,
    current_away_score: int,
    home_red_cards: int,
    away_red_cards: int,
    original_home_xg: float,
    original_away_xg: float,
    strength_diff: float,
    weights: Optional[MatchStateWeights] = None,
) -> dict:
    """
    Convenience function to get a live prediction.
    
    This is the main entry point for the live prediction service.
    
    Args:
        current_minute: Current match minute
        current_home_score: Current home score
        current_away_score: Current away score
        home_red_cards: Home red cards
        away_red_cards: Away red cards
        original_home_xg: Original pre-match home xG
        original_away_xg: Original pre-match away xG
        strength_diff: Team strength difference (home - away)
        weights: Optional custom weights
    
    Returns:
        Live prediction dictionary
    """
    service = LivePredictionService(weights=weights)
    return service.get_live_prediction(
        current_minute=current_minute,
        current_home_score=current_home_score,
        current_away_score=current_away_score,
        home_red_cards=home_red_cards,
        away_red_cards=away_red_cards,
        original_home_xg=original_home_xg,
        original_away_xg=original_away_xg,
        strength_diff=strength_diff,
    )
