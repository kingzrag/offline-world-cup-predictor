MODEL OPTIMIZATION REPORT
=========================

This report details a comprehensive ML optimization study for the football prediction engine, focusing on feature analysis and potential improvements. The goal is to identify and recommend features for removal, and to estimate the impact of various feature categories on model performance.

1. Feature Importance
---------------------

Feature importance (gain) was measured for both the World Cup Predictor (outcome model) and the Goal Predictor (home and away goal models) using the `examine_models.py` script.

**World Cup Predictor (Outcome Model) - Top 20 Features:**
1.  ``elo_diff`` (0.056259)
2.  ``fifa_diff`` (0.051890)
3.  ``goal_difference_diff`` (0.028345)
4.  ``home_group_position`` (0.025265)
5.  ``missing_star_players_diff`` (0.024974)
6.  ``home_points`` (0.024937)
7.  ``points_diff`` (0.023971)
8.  ``away_defence_rating`` (0.023086)
9.  ``group_position_diff`` (0.022919)
10. ``starting_xi_value_diff`` (0.022901)
11. ``mv_diff`` (0.022861)
12. ``form_diff`` (0.022377)
13. ``away_clean_sheet_rate`` (0.022127)
14. ``attack_rating_diff`` (0.022003)
15. ``gs_diff`` (0.021850)
16. ``major_tournament_matches_diff`` (0.021630)
17. ``away_elo_momentum`` (0.021533)
18. ``defence_rating_diff`` (0.021432)
19. ``home_defence_rating`` (0.021284)
20. ``world_cup_matches_played_diff`` (0.021112)

**Goal Predictor (Home Goal Model) - Top 10 Features:**
1.  ``elo_diff`` (0.084515)
2.  ``fifa_diff`` (0.059781)
3.  ``goal_difference_diff`` (0.044585)
4.  ``away_points`` (0.037161)
5.  ``clean_sheet_rate_diff`` (0.028416)
6.  ``available_squad_diff`` (0.026839)
7.  ``group_position_diff`` (0.026400)
8.  ``away_defence_rating`` (0.024203)
9.  ``home_btts_rate`` (0.023552)
10. ``gc_diff`` (0.022668)

**Goal Predictor (Away Goal Model) - Top 10 Features:**
1.  ``fifa_diff`` (0.072746)
2.  ``elo_diff`` (0.056089)
3.  ``goal_difference_diff`` (0.045216)
4.  ``missing_star_players_diff`` (0.036635)
5.  ``mv_diff`` (0.032160)
6.  ``defence_rating_diff`` (0.031635)
7.  ``home_defence_rating`` (0.026675)
8.  ``strength_of_schedule_diff`` (0.026655)
9.  ``elo_momentum_diff`` (0.025913)
10. ``clean_sheet_rate_diff`` (0.024766)

2. Correlation with the Target
------------------------------

Correlation analysis was performed using `ml_optimization_study.py` on `dataset_world_cup.csv` and `dataset_goals.csv`.

**World Cup Dataset (Target: `target` - Outcome 0, 1, 2):**
*   **Top Correlated Features:**
    *   ``elo_diff`` (0.397825)
    *   ``fifa_diff`` (0.368890)
    *   ``goal_difference_diff`` (0.323282)
    *   ``group_position_diff`` (0.320728)
    *   ``points_diff`` (0.316994)
    *   ``mv_diff`` (0.309760)
    *   ``starting_xi_value_diff`` (0.309604)
    *   ``available_squad_diff`` (0.307640)
    *   ``attack_rating_diff`` (0.302453)
*   **Features with NaN Correlation (due to constant values in dataset):**
    *   ``red_card_diff``, ``referee_strictness``, ``set_piece_strength_diff``, ``set_piece_threat_diff``, ``squad_availability_diff``, ``substitution_impact_diff``, ``susp_diff``, ``suspension_impact_diff``, ``tactical_stability_diff``, ``time_remaining``

**Goal Dataset (Target: `home_score`):**
*   **Top Correlated Features:**
    *   ``elo_diff`` (0.424889)
    *   ``fifa_diff`` (0.395530)
    *   ``attack_rating_diff`` (0.248315)
    *   ``starting_xi_value_diff`` (0.244661)
    *   ``mv_diff`` (0.240881)
    *   ``available_squad_diff`` (0.238234)
    *   ``h2h_factor`` (0.223962)
    *   ``form_diff`` (0.221485)
    *   ``gs_diff`` (0.201498)
*   **Features with NaN Correlation (due to constant values in dataset):**
    *   ``away_suspension_count``, ``home_implied_probability``, ``draw_implied_probability``, ``away_implied_probability``, ``current_minute``, ``time_remaining``, ``current_score_diff``, ``home_red_cards``, ``away_red_cards``, ``red_card_diff``

**Goal Dataset (Target: `away_score`):**
*   **Top Correlated Features:**
    *   ``away_score`` (1.000000)
    *   ``defence_rating_diff`` (0.273503)
    *   ``gc_diff`` (0.237303)
    *   ``home_defence_rating`` (0.211541)
    *   ``away_attack_rating`` (0.172666)
    *   ``inj_diff`` (0.114667)
    *   ``away_clean_sheet_rate`` (0.065820)
    *   ``away_injury_market_value_loss`` (0.055951)
    *   ``elo_momentum_diff`` (0.043469)
    *   ``away_points`` (0.042811)
*   **Features with NaN Correlation (due to constant values in dataset):**
    *   Same as `home_score` target.

**Key Observations:**
*   ``elo_diff`` and ``fifa_diff`` are consistently the most correlated features with both outcome and goal targets, reinforcing their importance.
*   Features related to goal difference, group position, and points also show strong correlations.
*   Many "live" features (e.g., implied probabilities, current minute, red cards) and "Match Intelligence" features show NaN correlation, indicating they are constant in the current training datasets. This is a critical finding.

3. Detect Noisy Features
------------------------

The `ml_optimization_study.py` script identified numerous constant features in both datasets. These features have zero variance and provide no information to the model, effectively acting as noise or dead weight.

**Constant Features in World Cup Dataset (value shown in parentheses):**
*   ``aerial_dominance_diff`` (0.0)
*   ``attacking_efficiency_diff`` (0.0)
*   ``attacking_strength_diff`` (0.0)
*   ``availability_score_diff`` (0.0)
*   ``avg_rating_diff`` (0.0)
*   ``away_aerial_dominance`` (0.0)
*   ``away_attacking_efficiency`` (0.0)
*   ``away_attacking_strength`` (0.0)
*   ``away_avg_rating`` (0.0)
*   ``away_defensive_stability`` (0.5)
*   ``away_defensive_strength`` (0.0)
*   ``away_discipline_score`` (1.0)
*   ``away_expected_goals`` (0.0)
*   ``away_fatigue_score`` (1.0)
*   ``away_finishing_quality`` (0.5)
*   ``away_formation_stability`` (0.5)
*   ``away_goalkeeper_performance`` (0.0)
*   ``away_goalkeeper_strength`` (0.0)
*   ``away_implied_probability`` (0.333)
*   ``away_injury_impact`` (0.0)
*   ``away_kaggle_attack_rating`` (0.0)
*   ``away_kaggle_bench_strength`` (0.0)
*   ``away_kaggle_defense_rating`` (0.0)
*   ``away_kaggle_discipline_score`` (0.0)
*   ``away_kaggle_starting_xi_strength`` (0.0)
*   ``away_kaggle_suspension_risk`` (0.0)
*   ``away_midfield_control`` (0.0)
*   ``away_momentum_score`` (0.5)
*   ``away_passing_dominance`` (0.0)
*   ``away_passing_strength`` (0.0)
*   ``away_player_availability_score`` (1.0)
*   ``away_possession`` (0.0)
*   ``away_pressing_intensity`` (0.0)
*   ``away_pressing_strength`` (0.0)
*   ``away_recent_form`` (0.5)
*   ``away_red_cards`` (0)
*   ``away_set_piece_strength`` (0.0)
*   ``away_set_piece_threat`` (0.0)
*   ``away_squad_availability`` (1.0)
*   ``away_substitution_impact`` (0.0)
*   ``away_suspension_count`` (0)
*   ``away_suspension_impact`` (0.0)
*   ``away_tactical_stability`` (0.5)
*   ``confidence_score`` (0.5)
*   ``current_minute`` (0)
*   ``current_score_diff`` (0)
*   ``defensive_stability_diff`` (0.0)
*   ``defensive_strength_diff`` (0.0)
*   ``discipline_score_diff`` (0.0)
*   ``draw_implied_probability`` (0.333)
*   ``expected_goals_diff`` (0.0)
*   ``fatigue_score_diff`` (0.0)
*   ``finishing_quality_diff`` (0.0)
*   ``formation_stability_diff`` (0.0)
*   ``goalkeeper_performance_diff`` (0.0)
*   ``goalkeeper_strength_diff`` (0.0)
*   ``home_aerial_dominance`` (0.0)
*   ``home_attacking_efficiency`` (0.0)
*   ``home_attacking_strength`` (0.0)
*   ``home_avg_rating`` (0.0)
*   ``home_defensive_stability`` (0.5)
*   ``home_defensive_strength`` (0.0)
*   ``home_discipline_score`` (1.0)
*   ``home_expected_goals`` (0.0)
*   ``home_fatigue_score`` (1.0)
*   ``home_finishing_quality`` (0.5)
*   ``home_formation_stability`` (0.5)
*   ``home_goalkeeper_performance`` (0.0)
*   ``home_goalkeeper_strength`` (0.0)
*   ``home_implied_probability`` (0.333)
*   ``home_injury_impact`` (0.0)
*   ``home_kaggle_attack_rating`` (0.0)
*   ``home_kaggle_bench_strength`` (0.0)
*   ``home_kaggle_defense_rating`` (0.0)
*   ``home_kaggle_discipline_score`` (0.0)
*   ``home_kaggle_starting_xi_strength`` (0.0)
*   ``home_kaggle_suspension_risk`` (0.0)
*   ``home_midfield_control`` (0.0)
*   ``home_momentum_score`` (0.5)
*   ``home_passing_dominance`` (0.0)
*   ``home_passing_strength`` (0.0)
*   ``home_player_availability_score`` (1.0)
*   ``home_possession`` (0.0)
*   ``home_pressing_intensity`` (0.0)
*   ``home_pressing_strength`` (0.0)
*   ``home_recent_form`` (0.5)
*   ``home_red_cards`` (0)
*   ``home_set_piece_strength`` (0.0)
*   ``home_set_piece_threat`` (0.0)
*   ``home_squad_availability`` (1.0)
*   ``home_substitution_impact`` (0.0)
*   ``home_suspension_count`` (0)
*   ``home_suspension_impact`` (0.0)
*   ``home_tactical_stability`` (0.5)
*   ``injury_impact_diff`` (0.0)
*   ``kaggle_attack_rating_diff`` (0.0)
*   ``kaggle_bench_strength_diff`` (0.0)
*   ``kaggle_defense_rating_diff`` (0.0)
*   ``kaggle_discipline_score_diff`` (0.0)
*   ``kaggle_starting_xi_strength_diff`` (0.0)
*   ``kaggle_suspension_risk_diff`` (0.0)
*   ``midfield_control_diff`` (0.0)
*   ``momentum_score_diff`` (0.0)
*   ``passing_dominance_diff`` (0.0)
*   ``passing_strength_diff`` (0.0)
*   ``possession_diff`` (0.0)
*   ``pressing_intensity_diff`` (0.0)
*   ``pressing_strength_diff`` (0.0)
*   ``recent_form_diff`` (0.0)
*   ``red_card_diff`` (0)
*   ``referee_strictness`` (0.0)
*   ``set_piece_strength_diff`` (0.0)
*   ``set_piece_threat_diff`` (0.0)
*   ``squad_availability_diff`` (0.0)
*   ``substitution_impact_diff`` (0.0)
*   ``susp_diff`` (0)
*   ``suspension_impact_diff`` (0.0)
*   ``tactical_stability_diff`` (0.0)
*   ``time_remaining`` (90)

**Constant Features in Goal Dataset (value shown in parentheses):**
*   ``susp_diff`` (0)
*   ``match_stage_weight`` (0)
*   ``knockout_matches_diff`` (0)
*   ``home_suspension_count`` (0)
*   ``away_suspension_count`` (0)
*   ``home_implied_probability`` (0.333)
*   ``draw_implied_probability`` (0.333)
*   ``away_implied_probability`` (0.333)
*   ``current_minute`` (0)
*   ``time_remaining`` (90)
*   ``current_score_diff`` (0)
*   ``home_red_cards`` (0)
*   ``away_red_cards`` (0)
*   ``red_card_diff`` (0)

**Key Observation:**
A large number of features, particularly those related to "Match Intelligence" (Phase 4 Expansion), "SofaScore Intelligence", "Betting Odds", and "Live Match Events", are constant in the current datasets. This means they are not providing any predictive signal and are effectively noise. This is likely due to the historical nature of the training data not containing these live/dynamic features.

4. Detect Duplicated Features
-----------------------------

The correlation analysis identified features with absolute correlation greater than 0.95, indicating high redundancy.

**Highly Correlated Features (World Cup Dataset):**
*   ``mv_diff`` is highly correlated with ``available_squad_diff``.
*   ``starting_xi_value_diff`` is highly correlated with ``available_squad_diff`` and ``mv_diff``.

**Highly Correlated Features (Goal Dataset):**
*   ``available_squad_diff`` is highly correlated with ``mv_diff``.
*   ``starting_xi_value_diff`` is highly correlated with ``mv_diff`` and ``available_squad_diff``.

**Key Observation:**
The squad market value features (``mv_diff``, ``available_squad_diff``, ``starting_xi_value_diff``) are highly inter-correlated. While they represent different aspects of squad value, their high correlation suggests that some of them might be redundant.

5. Detect Features Causing Overfitting
--------------------------------------

Features that are noisy (constant or very low variance) or highly duplicated can contribute to overfitting, especially in tree-based models like XGBoost, by allowing the model to learn spurious correlations or by adding unnecessary complexity.

*   **Constant Features**: All constant features identified in point 3 are prime candidates for removal as they add no information but increase model complexity.
*   **Highly Correlated Features**: The highly correlated squad value features (``mv_diff``, ``available_squad_diff``, ``starting_xi_value_diff``) could lead to overfitting if the model assigns importance to multiple highly similar features, making it less generalizable.
*   **Low Importance Features**: Features with very low importance (not appearing in the top 20 for any model) and low correlation with the target are also candidates for removal, as they might be capturing noise rather than signal.

6. Rank every feature from most useful to least useful
------------------------------------------------------

Combining feature importance (from `examine_models.py`) and correlation with target (from `ml_optimization_study.py`), here's a qualitative ranking. Features with high importance and high correlation are most useful. Features that are constant or highly redundant are least useful.

**Most Useful (High Importance & High Correlation):**
*   ``elo_diff``
*   ``fifa_diff``
*   ``goal_difference_diff``
*   ``group_position_diff``
*   ``points_diff``
*   ``mv_diff`` (though with redundancy concerns)
*   ``starting_xi_value_diff`` (though with redundancy concerns)
*   ``available_squad_diff`` (though with redundancy concerns)
*   ``attack_rating_diff``
*   ``defence_rating_diff``
*   ``missing_star_players_diff``
*   ``form_diff``
*   ``gs_diff``
*   ``gc_diff``

**Moderately Useful (Moderate Importance & Correlation):**
*   ``home_adv``
*   ``h2h_factor``
*   ``elo_momentum_diff``, ``home_elo_momentum``, ``away_elo_momentum``
*   ``strength_of_schedule_diff``, ``home_strength_of_schedule``, ``away_strength_of_schedule``
*   ``world_cup_matches_played_diff``, ``major_tournament_matches_diff``, ``knockout_matches_diff``
*   ``home_injury_count``, ``away_injury_count``, ``home_injury_market_value_loss``, ``away_injury_market_value_loss``
*   ``home_clean_sheet_rate``, ``away_clean_sheet_rate``, ``clean_sheet_rate_diff``
*   ``home_btts_rate``, ``away_btts_rate``, ``btts_rate_diff``

**Least Useful / Noisy (Low/Zero Importance & Correlation, or Constant):**
*   All constant features identified in point 3 (e.g., ``red_card_diff``, ``current_minute``, all "Match Intelligence" and "SofaScore Intelligence" features, ``home_implied_probability``, etc.). These are effectively useless in the current training setup.
*   Features with very low importance that are not highly correlated with the target.

7. Recommend which features should be removed
---------------------------------------------

Based on the analysis, the following features are recommended for removal:

*   **All Constant Features**: Any feature identified as "Constant feature" in point 3 should be removed from the feature set. These features provide no information and only add computational overhead and potential for confusion. This includes:
    *   All "Match Intelligence" features (e.g., ``home_attacking_strength``, ``away_attacking_strength``, etc.)
    *   All "SofaScore Intelligence" features (e.g., ``home_avg_rating``, ``away_avg_rating``, ``home_possession``, ``away_possession``, ``home_xg``, ``away_xg``, ``possession_diff``, ``xg_diff``)
    *   "Live Match Event" features (``current_minute``, ``time_remaining``, ``current_score_diff``, ``home_red_cards``, ``away_red_cards``, ``red_card_diff``)
    *   "Betting Odds" features (``home_implied_probability``, ``draw_implied_probability``, ``away_implied_probability``)
    *   Other constant features like ``susp_diff``, ``match_stage_weight``, ``knockout_matches_diff``, ``home_suspension_count``, ``away_suspension_count``, ``referee_strictness``, and all Kaggle-derived features (as they are currently constant).
*   **Redundant Squad Value Features**: Given the high correlation between ``mv_diff``, ``available_squad_diff``, and ``starting_xi_value_diff``, consider keeping only the most informative one (e.g., ``starting_xi_value_diff`` as it's more granular) and removing the others. This would require further experimentation to confirm the optimal choice.
*   **Low Importance Features**: After removing constant and highly redundant features, re-evaluate the importance of the remaining features. Any features with consistently very low importance across models and targets could be considered for removal to simplify the model.

**Rationale for Removal**: Removing these features will:
*   Reduce model complexity.
*   Improve model interpretability.
*   Decrease training and inference time.
*   Potentially improve generalization by reducing noise and overfitting.

8. Evaluation of Improvements Separately
----------------------------------------

This section estimates the expected improvements in accuracy, Log Loss, and Brier Score for various feature categories. These are qualitative estimates based on feature importance, correlation, and domain knowledge, as direct retraining is not performed.

*   **Kaggle Engineered Features**:
    *   **Expected Accuracy Improvement**: 0-1%
    *   **Expected Log Loss Improvement**: 0.00-0.01
    *   **Expected Brier Score Improvement**: 0.00-0.01
    *   **Reasoning**: Currently, all Kaggle-derived features are constant in the training datasets, meaning they provide no signal. If these features were properly populated with meaningful data, they could offer a marginal improvement, but their current state makes them useless.
*   **Injury Features (e.g., `inj_diff`, `home_injury_count`, `home_injury_market_value_loss`, `missing_star_players_diff`)**:
    *   **Expected Accuracy Improvement**: 1-3%
    *   **Expected Log Loss Improvement**: 0.01-0.03
    *   **Expected Brier Score Improvement**: 0.01-0.03
    *   **Reasoning**: Injury features, especially ``missing_star_players_diff`` and ``starting_xi_value_diff``, show up in the top features for both models. This indicates they are already providing a good signal. Further refinement (e.g., more granular injury types, player positions) could yield additional gains.
*   **Suspension Features (e.g., `susp_diff`, `home_suspension_count`)**:
    *   **Expected Accuracy Improvement**: 0-1%
    *   **Expected Log Loss Improvement**: 0.00-0.01
    *   **Expected Brier Score Improvement**: 0.00-0.01
    *   **Reasoning**: Currently, suspension-related features (e.g., ``susp_diff``, ``home_suspension_count``) are constant (zero) in the training datasets, making them ineffective. If real suspension data were available and integrated, they would likely have a similar impact to injury features, but perhaps slightly less given that suspensions are often for single matches.
*   **Elo Features (e.g., `elo_diff`, `elo_momentum_diff`)**:
    *   **Expected Accuracy Improvement**: 0-1% (already very strong)
    *   **Expected Log Loss Improvement**: 0.00-0.01
    *   **Expected Brier Score Improvement**: 0.00-0.01
    *   **Reasoning**: ELO features are consistently among the most important and highly correlated. They form a strong baseline. Minor improvements might come from more sophisticated ELO models (e.g., incorporating goal difference, home advantage adjustments).
*   **FIFA Ranking (e.g., `fifa_diff`)**:
    *   **Expected Accuracy Improvement**: 0-1% (already very strong)
    *   **Expected Log Loss Improvement**: 0.00-0.01
    *   **Expected Brier Score Improvement**: 0.00-0.01
    *   **Reasoning**: Similar to ELO, FIFA ranking is a very strong predictor. Further improvements are likely marginal unless the ranking system itself is refined or combined with other features in a more complex way.
*   **Market Value (e.g., `mv_diff`, `available_squad_diff`, `starting_xi_value_diff`)**:
    *   **Expected Accuracy Improvement**: 1-2%
    *   **Expected Log Loss Improvement**: 0.01-0.02
    *   **Expected Brier Score Improvement**: 0.01-0.02
    *   **Reasoning**: These features are highly important and correlated. Removing redundancy (as discussed in point 7) and potentially enriching with more granular player market values (e.g., average XI market value) could lead to slight gains.
*   **Recent Form (e.g., `form_diff`, `gs_diff`, `gc_diff`, `attack_rating_diff`, `defence_rating_diff`)**:
    *   **Expected Accuracy Improvement**: 1-3%
    *   **Expected Log Loss Improvement**: 0.01-0.03
    *   **Expected Brier Score Improvement**: 0.01-0.03
    *   **Reasoning**: These features are already strong predictors. Improvements could come from optimizing the look-back window (e.g., weighted average over different periods), incorporating opponent strength into form calculations, or using more advanced form metrics.
*   **xG (e.g., `home_xg`, `away_xg`, `xg_diff`)**:
    *   **Expected Accuracy Improvement**: 2-5%
    *   **Expected Log Loss Improvement**: 0.02-0.05
    *   **Expected Brier Score Improvement**: 0.02-0.05
    *   **Reasoning**: Currently, the xG features from SofaScore are constant in the training data, making them useless. If real xG data were integrated and the model trained on it, this would be a *significant* improvement. Developing an in-house xG model (as suggested in the V2 roadmap) would provide even greater control and potential for accuracy gains.
*   **BTTS History (e.g., `home_btts_rate`, `away_btts_rate`, `btts_rate_diff`)**:
    *   **Expected Accuracy Improvement**: 0-1%
    *   **Expected Log Loss Improvement**: 0.00-0.01
    *   **Expected Brier Score Improvement**: 0.00-0.01
    *   **Reasoning**: These features have moderate importance. Improvements could come from optimizing the look-back window or incorporating opponent BTTS rates.
*   **Clean Sheet History (e.g., `home_clean_sheet_rate`, `away_clean_sheet_rate`, `clean_sheet_rate_diff`)**:
    *   **Expected Accuracy Improvement**: 0-1%
    *   **Expected Log Loss Improvement**: 0.00-0.01
    *   **Expected Brier Score Improvement**: 0.00-0.01
    *   **Reasoning**: Similar to BTTS history, these features have moderate importance. Optimizing the look-back window or considering opponent clean sheet rates could yield minor gains.
*   **Tournament Experience (e.g., `world_cup_matches_played_diff`, `major_tournament_matches_diff`, `knockout_matches_diff`)**:
    *   **Expected Accuracy Improvement**: 0-1%
    *   **Expected Log Loss Improvement**: 0.00-0.01
    *   **Expected Brier Score Improvement**: 0.00-0.01
    *   **Reasoning**: These features have moderate importance. Their impact is likely limited to specific tournament contexts.
*   **Head-to-head (e.g., `h2h_factor`)**:
    *   **Expected Accuracy Improvement**: 0-1%
    *   **Expected Log Loss Improvement**: 0.00-0.01
    *   **Expected Brier Score Improvement**: 0.00-0.01
    *   **Reasoning**: The `h2h_factor` has moderate importance. Improvements could come from more sophisticated H2H metrics (e.g., recent H2H form, H2H goal differences).

9. Comparison: Current Model vs. Optimized Feature Set
------------------------------------------------------

**Current Model (Version 1.0):**
*   **Strengths**: Strong baseline performance driven by ELO, FIFA rankings, and recent form. Injury features are now contributing positively due to recent retraining.
*   **Weaknesses**: Significant amount of noisy/constant features (especially "live" and "intelligence" features) that add no value and potentially hinder performance. Redundancy among squad value features. Limited granularity in player and tactical data.
*   **Performance**: Achieves reasonable accuracy, Log Loss, and F1 scores (as per `train_world_cup_model.py` and `train_goal_model.py` outputs).

**Optimized Feature Set (Hypothetical Version 1.1):**
*   **Expected Strengths**: Leaner, more interpretable models. Faster training and inference. Reduced risk of overfitting from noisy/redundant features. Improved focus on truly predictive signals.
*   **Expected Performance Improvement**:
    *   **Accuracy**: Expected to see a modest improvement of **2-5%** for the outcome model and **3-7%** for the goal models, primarily from removing noise and refining existing features.
    *   **Log Loss**: Expected to decrease by **0.02-0.05**, indicating better calibrated probabilities.
    *   **Brier Score**: Expected to decrease by **0.02-0.05**, also reflecting better calibrated probabilities and overall accuracy.
*   **Reasoning**: The removal of numerous constant and highly correlated features will simplify the model's learning task. While the direct impact of removing constant features on metrics might be minimal (as they contribute no signal), it cleans up the feature space. The more significant gains will come from addressing redundancy and ensuring that all *intended* features (like xG, suspensions, and live data) are actually populated with real, varying data during training.

**Overall**: Optimizing the feature set is a crucial first step towards Version 2.0. It will create a more efficient and robust foundation upon which to build more advanced features and models. The most significant immediate gains are expected from properly populating and utilizing features that are currently constant in the training data (e.g., xG, live match events, betting odds, Kaggle features).
