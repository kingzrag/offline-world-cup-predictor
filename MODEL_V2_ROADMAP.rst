MODEL V2 ROADMAP
==================

This report provides a comprehensive audit of the current football prediction model (Version 1.0) and outlines a strategic roadmap for its evolution to Version 2.0. The analysis covers feature utilization, model performance insights, and identifies key areas for improvement.

1. Every feature currently used by the model
------------------------------------------

The `ml/features.py` module is responsible for generating a wide array of features. These features can be broadly categorized as follows:

**Phase 1 Core Features:**
*   ``elo_diff``: Difference in ELO ratings between home and away teams.
*   ``fifa_diff``: Difference in FIFA rankings between home and away teams (lower ranking is better, so ``away_rank - home_rank``).
*   ``form_diff``: Difference in recent form (average points per game) between home and away teams.
*   ``gs_diff``: Difference in average goals scored (GS) in recent matches.
*   ``gc_diff``: Difference in average goals conceded (GC) in recent matches.
*   ``mv_diff``: Difference in total squad market value between home and away teams.
*   ``inj_diff``: Difference in total market value of injured players (``away_inj_mv - home_inj_mv``).
*   ``susp_diff``: Difference in total market value of suspended players (``away_susp_mv - home_susp_mv``).
*   ``home_adv``: Home advantage flag (1 for home team, 0 for neutral or non-host World Cup matches).
*   ``h2h_factor``: Head-to-head performance factor (home team points ratio in recent H2H matches).

**Phase 2 Player Intelligence Features:**
*   ``available_squad_diff``: Difference in market value of available (not injured/suspended) squad players.
*   ``availability_pct_diff``: Difference in percentage of available squad market value.
*   ``starting_xi_value_diff``: Difference in market value of the top 11 available players.
*   ``missing_star_players_diff``: Difference in count of missing star players (injured/suspended with market value > €50M).
*   ``match_stage_weight``: Weight assigned to the match stage (e.g., group stage, knockout rounds).

**Phase 3 Structural Features:**
*   ``home_elo_momentum``: Home team's ELO momentum (simulated ELO delta over last 10 matches).
*   ``away_elo_momentum``: Away team's ELO momentum.
*   ``elo_momentum_diff``: Difference in ELO momentum.
*   ``home_strength_of_schedule``: Home team's strength of schedule (average opponent ELO over last 5 matches).
*   ``away_strength_of_schedule``: Away team's strength of schedule.
*   ``strength_of_schedule_diff``: Difference in strength of schedule.
*   ``world_cup_matches_played_diff``: Difference in World Cup matches played.
*   ``major_tournament_matches_diff``: Difference in major tournament matches played.
*   ``knockout_matches_diff``: Difference in knockout matches played.

**Phase 4.5 Advanced Goal Intelligence Features:**
*   ``home_attack_rating``: Home team's weighted average goals scored in last 20 matches.
*   ``away_attack_rating``: Away team's weighted average goals scored in last 20 matches.
*   ``attack_rating_diff``: Difference in attack ratings.
*   ``home_defence_rating``: Home team's weighted average goals conceded in last 20 matches.
*   ``away_defence_rating``: Away team's weighted average goals conceded in last 20 matches.
*   ``defence_rating_diff``: Difference in defence ratings.
*   ``home_clean_sheet_rate``: Home team's clean sheet rate in last 20 matches.
*   ``away_clean_sheet_rate``: Away team's clean sheet rate in last 20 matches.
*   ``clean_sheet_rate_diff``: Difference in clean sheet rates.
*   ``home_btts_rate``: Home team's Both Teams To Score (BTTS) rate in last 20 matches.
*   ``away_btts_rate``: Away team's BTTS rate in last 20 matches.
*   ``btts_rate_diff``: Difference in BTTS rates.

**Injury & Suspension Counts & Absolute Market-Value Loss Features:**
*   ``home_injury_count``: Number of injured players for the home team.
*   ``away_injury_count``: Number of injured players for the away team.
*   ``home_suspension_count``: Number of suspended players for the home team.
*   ``away_suspension_count``: Number of suspended players for the away team.
*   ``home_injury_market_value_loss``: Total market value of injured players for the home team.
*   ``away_injury_market_value_loss``: Total market value of injured players for the away team.

**Standings Features (Live Features):**
*   ``home_group_position``: Home team's current group position.
*   ``away_group_position``: Away team's current group position.
*   ``group_position_diff``: Difference in group position (``away_group_position - home_group_position``).
*   ``home_points``: Home team's points in the current competition.
*   ``away_points``: Away team's points in the current competition.
*   ``points_diff``: Difference in points.
*   ``home_goals_difference``: Home team's goal difference.
*   ``away_goals_difference``: Away team's goal difference.
*   ``goal_difference_diff``: Difference in goal difference.

**Betting Odds Features (Live Features):**
*   ``home_implied_probability``: Implied probability of home win from latest bookmaker odds.
*   ``draw_implied_probability``: Implied probability of draw from latest bookmaker odds.
*   ``away_implied_probability``: Implied probability of away win from latest bookmaker odds.

**Live Match Event Features (Live Features):**
*   ``current_minute``: Current minute of the match.
*   ``time_remaining``: Time remaining in the match.
*   ``current_home_score``: Current home score.
*   ``current_away_score``: Current away score.
*   ``current_score_diff``: Current score difference.
*   ``home_red_cards``: Number of red cards for the home team.
*   ``away_red_cards``: Number of red cards for the away team.
*   ``red_card_diff``: Difference in red cards.

**SofaScore Intelligence Features (Live Features):**
*   ``home_avg_rating``: Home team's average SofaScore rating of starting XI.
*   ``away_avg_rating``: Away team's average SofaScore rating of starting XI.
*   ``home_possession``: Home team's possession percentage.
*   ``away_possession``: Away team's possession percentage.
*   ``home_xg``: Home team's expected goals (xG) from SofaScore.
*   ``away_xg``: Away team's expected goals (xG) from SofaScore.
*   ``possession_diff``: Difference in possession.
*   ``xg_diff``: Difference in xG.

**Match Intelligence Features (Phase 4 Expansion - Live Features):**
*   ``home_attacking_strength``, ``away_attacking_strength``
*   ``home_defensive_strength``, ``away_defensive_strength``
*   ``home_midfield_control``, ``away_midfield_control``
*   ``home_goalkeeper_performance``, ``away_goalkeeper_performance``
*   ``home_passing_dominance``, ``away_passing_dominance``
*   ``home_pressing_intensity``, ``away_pressing_intensity``
*   ``home_set_piece_threat``, ``away_set_piece_threat``
*   ``home_discipline_score``, ``away_discipline_score``
*   ``home_fatigue_score``, ``away_fatigue_score``
*   ``home_substitution_impact``, ``away_substitution_impact``
*   ``home_player_availability_score``, ``away_player_availability_score``
*   ``home_injury_impact``, ``away_injury_impact``
*   ``home_suspension_impact``, ``away_suspension_impact``
*   ``home_formation_stability``, ``away_formation_stability``
*   ``home_momentum_score``, ``away_momentum_score``
*   ``confidence_score``
*   ``home_goalkeeper_strength``, ``away_goalkeeper_strength``
*   ``home_passing_strength``, ``away_passing_strength``
*   ``home_recent_form``, ``away_recent_form``
*   ``home_aerial_dominance``, ``away_aerial_dominance``
*   ``home_pressing_strength``, ``away_pressing_strength``
*   ``home_defensive_stability``, ``away_defensive_stability``
*   ``home_attacking_efficiency``, ``away_attacking_efficiency``
*   ``home_finishing_quality``, ``away_finishing_quality``
*   ``home_set_piece_strength``, ``away_set_piece_strength``
*   ``home_squad_availability``, ``away_squad_availability``
*   ``home_tactical_stability``, ``away_tactical_stability``

**Kaggle Features:**
*   Dynamically loaded if ``KAGGLE_FEATURES_AVAILABLE`` is True. These are typically raw statistics from the Kaggle dataset.

2. Every engineered feature
---------------------------

Almost all features are engineered to some extent, as they are not raw data points but rather calculations or aggregations. Here are some key examples of engineered features and their derivations:

*   **``elo_diff``**: Derived from ``get_team_elo`` function, which itself involves a lookup and a fallback to a default value.
*   **``fifa_diff``**: Derived from ``fifa_ranking`` attributes of ``Team`` objects, with a fallback to 150.
*   **``form_diff``, ``gs_diff``, ``gc_diff``**: Derived from ``get_team_recent_stats``, which calculates average points, goals scored, and goals conceded over the last N matches.
*   **``mv_diff``**: Derived from ``squad_market_value`` attributes of ``Team`` objects.
*   **``inj_diff``, ``susp_diff``**: Derived from summing ``player_market_value`` of ``Injury`` and ``Suspension`` objects.
*   **``home_injury_count``, ``away_injury_count``, ``home_suspension_count``, ``away_suspension_count``**: Simple counts of ``Injury`` and ``Suspension`` objects.
*   **``home_injury_market_value_loss``, ``away_injury_market_value_loss``**: Sum of ``player_market_value`` for injuries.
*   **``available_squad_diff``**: Calculated as ``(home_mv - home_inj_mv - home_susp_mv) - (away_mv - away_inj_mv - away_susp_mv)``.
*   **``availability_pct_diff``**: Calculated as ``(home_available / home_mv) - (away_available / away_mv)``.
*   **``starting_xi_value_diff``**: Calculated by summing the market values of the top 11 available players.
*   **``missing_star_players_diff``**: Count of players with market value > €50M who are injured or suspended.
*   **``match_stage_weight``**: A categorical feature mapped to numerical weights based on ``STAGE_WEIGHTS``.
*   **``elo_momentum_diff``**: Derived from ``get_elo_momentum``, which simulates ELO deltas over recent matches.
*   **``strength_of_schedule_diff``**: Derived from ``get_strength_of_schedule``, which calculates the average opponent ELO.
*   **``world_cup_matches_played_diff``, ``major_tournament_matches_diff``, ``knockout_matches_diff``**: Derived from ``get_tournament_experience``, which counts historical match appearances.
*   **``h2h_factor``**: Calculated from head-to-head match results.
*   **``attack_rating_diff``, ``defence_rating_diff``**: Derived from ``get_attack_rating`` and ``get_defence_rating``, which are weighted averages of goals scored/conceded.
*   **``clean_sheet_rate_diff``, ``btts_rate_diff``**: Derived from ``get_clean_sheet_rate`` and ``get_btts_rate``, which are rates over recent matches.
*   **``group_position_diff``, ``points_diff``, ``goal_difference_diff``**: Derived from ``Standing`` objects.
*   **``home_implied_probability``, ``draw_implied_probability``, ``away_implied_probability``**: Derived from ``BookmakerOdds``.
*   **``current_score_diff``, ``red_card_diff``**: Derived from ``Match`` object attributes.
*   **``home_avg_rating``, ``away_avg_rating``**: Derived from ``PlayerMatchPerformance`` objects.
*   **``possession_diff``, ``xg_diff``**: Derived from ``MatchStatistic`` objects.
*   **All ``intelligence_service`` features**: These are all highly engineered, calculated by the ``IntelligenceService`` based on various match and team statistics.

3. Every feature that is never used
-----------------------------------

By comparing the features generated in ``ml/features.py`` with the feature lists used by ``world_cup_predictor.pkl`` and ``goal_predictor.pkl``, we can identify unused features.

**Features generated in `ml/features.py` but NOT used by `world_cup_predictor.pkl`:**
*   ``availability_pct_diff`` (This feature is calculated but not present in the World Cup model's feature list)
*   All SofaScore Intelligence features (``home_avg_rating``, ``away_avg_rating``, ``home_possession``, ``away_possession``, ``home_xg``, ``away_xg``, ``possession_diff``, ``xg_diff``) are calculated but not used by the World Cup model.
*   All Match Intelligence features (e.g., ``home_attacking_strength``, ``away_attacking_strength``, etc.) are calculated but not used by the World Cup model.

**Features generated in `ml/features.py` but NOT used by `goal_predictor.pkl`:**
*   ``match_stage_weight`` (This feature is calculated but not present in the Goal model's feature list)
*   All SofaScore Intelligence features (``home_avg_rating``, ``away_avg_rating``, ``home_possession``, ``away_possession``, ``home_xg``, ``away_xg``, ``possession_diff``, ``xg_diff``) are calculated but not used by the Goal model.
*   All Match Intelligence features (e.g., ``home_attacking_strength``, ``away_attacking_strength``, etc.) are calculated but not used by the Goal model.

**Summary of Never Used Features:**
*   ``availability_pct_diff`` (unused by World Cup model)
*   All SofaScore Intelligence features (unused by both models)
*   All Match Intelligence features (unused by both models)
*   ``match_stage_weight`` (unused by Goal model)

4. Every duplicated feature
---------------------------

While not strictly "duplicated" in terms of identical calculation, several features capture similar information or are highly correlated. This can lead to redundancy and potentially mask the true importance of individual features.

*   **ELO-related features**: ``elo_diff``, ``home_elo_momentum``, ``away_elo_momentum``, ``elo_momentum_diff``. These all relate to team strength and recent performance based on ELO.
*   **Squad Value features**: ``mv_diff``, ``available_squad_diff``, ``starting_xi_value_diff``. These represent different granularities of squad value.
*   **Injury/Suspension features**: ``inj_diff``, ``susp_diff``, ``home_injury_count``, ``away_injury_count``, ``home_suspension_count``, ``away_suspension_count``, ``home_injury_market_value_loss``, ``away_injury_market_value_loss``, ``missing_star_players_diff``. These are all different ways of quantifying player unavailability.
*   **Recent Form/Goals features**: ``form_diff``, ``gs_diff``, ``gc_diff``, ``home_attack_rating``, ``away_attack_rating``, ``attack_rating_diff``, ``home_defence_rating``, ``away_defence_rating``, ``defence_rating_diff``. These all describe recent offensive and defensive performance.
*   **Standings features**: ``home_group_position``, ``away_group_position``, ``group_position_diff``, ``home_points``, ``away_points``, ``points_diff``, ``home_goals_difference``, ``away_goals_difference``, ``goal_difference_diff``. These are all derived from competition standings.

The presence of these highly correlated features might indicate an opportunity for feature selection or dimensionality reduction to simplify the model and potentially improve generalization.

5. Which features have the highest importance
---------------------------------------------

Based on the `examine_models.py` output (top 20 feature importances for each model):

**World Cup Predictor (Outcome Model):**
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

**Goal Predictor (Home Goal Model):**
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
11. ``attack_rating_diff`` (0.021857)
12. ``away_attack_rating`` (0.021746)
13. ``missing_star_players_diff`` (0.021574)
14. ``starting_xi_value_diff`` (0.021477)
15. ``points_diff`` (0.021442)
16. ``away_strength_of_schedule`` (0.021361)
17. ``away_injury_market_value_loss`` (0.021332)
18. ``defence_rating_diff`` (0.021197)
19. ``strength_of_schedule_diff`` (0.020972)
20. ``away_clean_sheet_rate`` (0.020944)

**Goal Predictor (Away Goal Model):**
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
11. ``away_injury_market_value_loss`` (0.023632)
12. ``home_injury_count`` (0.022911)
13. ``major_tournament_matches_diff`` (0.022497)
14. ``world_cup_matches_played_diff`` (0.022301)
15. ``away_points`` (0.021767)
16. ``home_strength_of_schedule`` (0.021069)
17. ``away_attack_rating`` (0.020909)
18. ``home_attack_rating`` (0.020836)
19. ``away_elo_momentum`` (0.020753)
20. ``attack_rating_diff`` (0.020665)

**Key Observations:**
*   **ELO and FIFA rankings** are consistently among the most important features for all models, highlighting their fundamental predictive power for team strength.
*   **Goal difference, group position, and points** from standings are also highly influential, especially for the outcome model.
*   **Injury/Suspension related features** like ``missing_star_players_diff``, ``starting_xi_value_diff``, and ``away_injury_market_value_loss`` show up in the top features, indicating that the recent retraining with simulated injury data has made these features impactful. This is a positive sign.
*   **Attack and Defence ratings/diffs** are important for goal prediction, as expected.

6. Which features should be removed
-----------------------------------

Based on the analysis, the following features should be considered for removal or re-evaluation:

*   **All SofaScore Intelligence features**: These are currently calculated in ``ml/features.py`` but are not used by either the World Cup or Goal prediction models. Removing their calculation would reduce computational overhead without impacting current predictions.
*   **All Match Intelligence features**: Similar to SofaScore features, these are calculated but unused by both models. Their removal would also streamline feature engineering.
*   **``availability_pct_diff``**: This feature is calculated but not used by the World Cup model. It's also highly correlated with ``available_squad_diff`` and ``mv_diff``.
*   **Redundant Injury/Suspension features**: While some injury/suspension features are important, there might be redundancy. For example, if ``missing_star_players_diff`` and ``starting_xi_value_diff`` capture most of the signal, some of the raw counts or market value losses might be less impactful. This would require further analysis (e.g., using permutation importance or more advanced feature selection techniques) to confirm.
*   **``match_stage_weight``**: This feature is calculated but not used by the Goal model.

**Recommendation**: Start by removing the completely unused SofaScore and Match Intelligence features. For the other potentially redundant features, a more rigorous feature selection process (e.g., recursive feature elimination, L1 regularization) should be applied during model retraining to identify and remove those that do not contribute significantly to predictive power.

7. Which important football features are still missing
------------------------------------------------------

Despite the extensive feature set, several important football features are still missing or could be enhanced:

*   **Player-level statistics (beyond market value)**:
    *   **Individual player form**: Recent goals, assists, key passes, defensive actions for key players.
    *   **Player roles/positions**: Impact of missing a key defender vs. a key striker.
    *   **Player quality metrics**: Beyond market value, consider ratings (e.g., SofaScore, WhoScored) for individual players.
*   **Tactical information**:
    *   **Formation**: How different formations match up.
    *   **Managerial style/tendencies**: Defensive vs. attacking, pressing intensity.
    *   **Home/Away specific tactics**: Some teams play differently at home vs. away.
*   **Match context**:
    *   **Importance of the match**: Derby, relegation battle, title decider (beyond just match stage).
    *   **Weather conditions**: Rain, wind, temperature can affect game flow.
    *   **Referee tendencies**: Some referees are stricter than others (more cards, penalties).
*   **Team chemistry/cohesion**:
    *   **Time under current manager**: How long the team has been playing together.
    *   **New signings integration**: Impact of recent transfers.
*   **Travel fatigue**: Especially for international matches or teams playing multiple competitions.
*   **Historical performance against specific opponents (beyond H2H factor)**: More granular analysis of past matchups, including scorelines, goal scorers, etc.
*   **Expected Assists (xA)**: A more advanced metric for chance creation.
*   **Goalkeeper specific metrics**: Save percentage, clean sheet probability.

8. Whether my Expected Goals (xG) calculation is mathematically correct
-----------------------------------------------------------------------

The `ml/features.py` file currently extracts `home_xg` and `away_xg` from `MatchStatistic` objects, which are presumably sourced from SofaScore. The `xg_diff` feature is then calculated as `home_xg - away_xg`.

**Conclusion**: The model *uses* xG data, but it does not *calculate* xG itself. It relies on an external source (SofaScore) for these values. Therefore, the mathematical correctness of the xG calculation depends entirely on the methodology used by SofaScore.

If the question implies whether the *integration* of xG into the features is correct, then yes, the difference (``xg_diff``) is a standard way to use this feature. However, the model itself is not performing the xG calculation.

9. Whether my Poisson engine is correctly using the predicted xG
----------------------------------------------------------------

**Analysis:**
The `predict_goals` function in `ModelService` is responsible for predicting expected goals.
1.  It first extracts ML features using `self._get_features`.
2.  It then uses `home_model` and `away_model` (XGBoost regressors) to predict `raw_home` and `raw_away` goals.
3.  These raw predictions are clipped to a minimum of 0.0 to become `expected_home` and `expected_away` goals.
4.  Crucially, these `expected_home` and `expected_away` goals are then passed directly to the `evaluate_poisson_engine` function: `poisson = evaluate_poisson_engine(expected_home, expected_away)`.

The `poisson_engine.py` module (imported at the top of `model_service.py`) is where the actual Poisson distribution calculations happen. The `evaluate_poisson_engine` function takes these two `expected_goals` values (lambdas for the Poisson distribution) and uses them to calculate probabilities for various scorelines and betting markets.

**Conclusion:**
Yes, the Poisson engine is correctly using the predicted xG. The `expected_home` and `expected_away` goals, which are the outputs of the XGBoost regressors, are directly fed as the lambda parameters into the `evaluate_poisson_engine` function. This is the standard and mathematically correct way to use predicted xG values in a Poisson model for football match outcomes.

10. Whether my betting markets are mathematically consistent
------------------------------------------------------------

**Analysis:**
The `predict_goals` function generates several betting markets based on the Poisson engine's output:
*   ``over_under`` markets (e.g., Over/Under 0.5, 1.5, ..., 4.5)
*   ``btts`` (Both Teams To Score)
*   ``most_likely_score`` and ``top_5_scorelines``
*   ``asian_handicap``
*   ``team_goals`` (e.g., Home Over 0.5, 1.5, 2.5)
*   ``clean_sheet`` probabilities
*   ``probability_matrix`` (full scoreline matrix)
*   ``outcome_probabilities`` (1X2 probabilities derived from the Poisson matrix)

The `_predict_betting_markets` function then attempts to use dedicated betting market models (if loaded) for ``asian_handicap``, ``asian_total``, ``btts``, ``clean_sheet``, and ``correct_score``. If these dedicated models are not available or fail, it falls back to the Poisson-based predictions from ``goal_result``.

**Mathematical Consistency Check:**

1.  **Probabilities Sum to 1.0**: The `ModelService.normalize_1x2_probs` function is explicitly used to ensure that the final home, draw, and away probabilities sum exactly to 1.0. This is crucial for consistency.
2.  **Poisson Distribution**: The core of the betting market generation relies on the Poisson distribution. Assuming the `poisson_engine.py` correctly implements the Poisson probability mass function, the probabilities for individual scorelines will be mathematically consistent with the input xG values.
3.  **Derived Markets**: Markets like Over/Under, BTTS, and 1X2 outcomes are derived from the full scoreline probability matrix. If the matrix is consistent, these derived markets should also be consistent. For example, P(Over 2.5) is the sum of probabilities of all scorelines where total goals > 2.5.
4.  **Asian Handicap**: The `predict_goals` function calculates a simple ``asian_handicap_label`` based on the xG difference. The `_predict_betting_markets` function then either uses a dedicated ML model for Asian Handicap or falls back to the Poisson engine's ``suggested_lines``. The consistency here depends on the `poisson_engine`'s implementation of Asian Handicaps.
5.  **Bookmaker Odds vs. Model Odds**: The ``home_implied_probability``, ``draw_implied_probability``, ``away_implied_probability`` features are extracted from actual bookmaker odds. These are used as *features* for the 1X2 model, but the model's *own* predicted probabilities are generated independently. The system does not attempt to reconcile or arbitrage directly against these implied probabilities within the `model_service.py`.

**Potential Areas for Further Scrutiny (beyond the scope of this audit without `poisson_engine.py` content):**
*   **`poisson_engine.py` implementation**: The mathematical correctness of the Poisson engine itself (e.g., how it handles scoreline probabilities, how it derives Over/Under, BTTS, and Asian Handicap lines from the score matrix) is critical. Without reviewing `poisson_engine.py`, I can only assume it's correctly implemented.
*   **Dedicated Betting Market Models**: If dedicated ML models are used for betting markets, their consistency with the Poisson-derived probabilities would need to be evaluated. The current code simply uses their output if available.
*   **Arbitrage Detection**: The current system doesn't explicitly check for arbitrage opportunities between its own predicted probabilities and external bookmaker odds.

**Conclusion:**
Based on the `model_service.py` code, the betting markets generated from the Poisson engine are *internally consistent* with the predicted xG, assuming the `poisson_engine.py` module is mathematically sound. The 1X2 probabilities are explicitly normalized. The use of external bookmaker implied probabilities as features is separate from the model's own probability generation.


11. Which parts of the prediction engine are strongest
------------------------------------------------------

Based on the feature importances and the overall design:

*   **ELO and FIFA Ranking Integration**: These are consistently the strongest predictors, indicating that the model effectively leverages fundamental team strength metrics.
*   **Injury/Suspension Impact**: The recent updates to incorporate real and simulated injury data, along with features like ``missing_star_players_diff`` and ``starting_xi_value_diff``, have made player availability a significant factor. This is a strong point, as it addresses a crucial real-world influence on match outcomes.
*   **Recent Form and Goal Statistics**: Features like ``form_diff``, ``attack_rating_diff``, and ``defence_rating_diff`` are well-engineered and contribute significantly to predictions, especially for the goal model.
*   **Live Data Integration (Standings, Betting Odds, Red Cards)**: The ability to incorporate real-time data like group standings, implied probabilities from bookmakers, and live match events (red cards, current score) is a major strength, allowing for dynamic predictions.

12. Which parts are weakest
----------------------------

*   **Reliance on External xG**: The model currently consumes xG from SofaScore. While convenient, this creates a dependency and limits control over the xG methodology. If SofaScore's xG model changes or is inaccurate, it directly impacts the prediction engine.
*   **Lack of Granular Player-Level Data**: Beyond market value and injury status, the model lacks detailed player-level performance metrics (e.g., individual player form, specific skill ratings). This limits its ability to fully understand the impact of individual players on a match.
*   **Limited Tactical Understanding**: The model does not explicitly incorporate tactical information (formations, managerial styles), which are crucial in football.
*   **Unused Features**: The presence of calculated but unused SofaScore and Match Intelligence features indicates inefficiency and potential for improvement by either integrating them or removing them.
*   **Potential for Feature Redundancy**: As noted in point 4, some features might be highly correlated, potentially leading to less interpretable models or minor performance degradation.
*   **Historical Data Limitations for Injuries**: While simulated injuries are used for training, the lack of extensive historical real injury data from Transfermarkt might limit the model's ability to learn nuanced injury impacts.

13. How much improvement each missing feature could realistically provide
------------------------------------------------------------------------

*   **Granular Player-Level Statistics (e.g., individual form, skill ratings)**:
    *   **Realistic Improvement**: 5-10% increase in predictive accuracy (e.g., AUC, log loss) for match outcomes and 10-15% for goal prediction.
    *   **Reasoning**: Football is a player-driven game. Understanding individual player contributions and their current form can significantly refine predictions, especially when star players are involved or in matches between evenly matched teams.
*   **Tactical Information (e.g., formations, managerial styles)**:
    *   **Realistic Improvement**: 3-7% increase in predictive accuracy.
    *   **Reasoning**: Tactics dictate how a team plays and how they might counter an opponent. Incorporating this can help predict game flow and potential upsets.
*   **Advanced xG Model (internal calculation)**:
    *   **Realistic Improvement**: 2-5% increase in predictive accuracy.
    *   **Reasoning**: Having an in-house xG model provides full control and allows for customization and continuous improvement, potentially leading to more accurate xG values than a generic external source.
*   **Travel Fatigue/Fixture Congestion**:
    *   **Realistic Improvement**: 1-3% increase in predictive accuracy.
    *   **Reasoning**: Physical condition significantly impacts performance, especially in demanding tournaments or leagues with tight schedules.
*   **Referee Bias/Tendencies**:
    *   **Realistic Improvement**: 0.5-2% increase in predictive accuracy.
    *   **Reasoning**: While subtle, referee decisions can swing a game. Understanding their tendencies could provide a marginal edge.

14. A roadmap from Version 1.0 to Version 2.0 of my prediction engine
--------------------------------------------------------------------

**Vision for Version 2.0**: A more robust, interpretable, and highly accurate prediction engine that leverages deeper player and tactical insights, with reduced reliance on external black-box components.

**Phase 1: Optimization & Refinement (Immediate - 1-2 months)**

*   **Action**: Remove unused features from ``ml/features.py``.
    *   **Details**: Eliminate calculation of SofaScore Intelligence and Match Intelligence features if they are not used by any model. Remove ``availability_pct_diff`` from World Cup model features and ``match_stage_weight`` from Goal model features.
    *   **Benefit**: Reduce computational overhead, simplify feature engineering, improve code clarity.
*   **Action**: Rigorous Feature Selection.
    *   **Details**: Implement advanced feature selection techniques (e.g., permutation importance, L1 regularization, recursive feature elimination) to identify and remove truly redundant or low-impact features from both models.
    *   **Benefit**: Improve model interpretability, potentially reduce overfitting, and slightly boost performance.
*   **Action**: Enhance Injury/Suspension Feature Engineering.
    *   **Details**: Explore more nuanced ways to incorporate injury/suspension data, such as categorizing injuries by severity, position of the player, or expected return date.
    *   **Benefit**: Capture more granular impact of player unavailability.
*   **Action**: Review and Refine Existing Feature Calculations.
    *   **Details**: Audit the logic for ``get_elo_momentum``, ``get_strength_of_schedule``, ``get_team_recent_stats``, ``get_attack_rating``, ``get_defence_rating``, etc., to ensure they are robust and capture the intended footballing concepts.
    *   **Benefit**: Ensure the foundational features are as accurate and representative as possible.

**Phase 2: Deeper Player & Tactical Insights (Short-term - 3-6 months)**

*   **Action**: Integrate Granular Player-Level Statistics.
    *   **Details**: Explore external data sources (e.g., Opta, StatsBomb, or more detailed SofaScore APIs) for individual player performance metrics (e.g., goals, assists, passes, tackles, dribbles, ratings). Engineer features like "average player rating of starting XI," "key player form," "impact of missing top scorer/defender."
    *   **Benefit**: Significant boost in predictive power by understanding individual player contributions.
*   **Action**: Incorporate Basic Tactical Information.
    *   **Details**: Develop features to represent common formations (e.g., 4-3-3, 4-4-2) and basic managerial tendencies (e.g., "possession-based," "counter-attacking"). This might involve parsing match reports or using external data.
    *   **Benefit**: Capture a crucial aspect of match dynamics that is currently missing.
*   **Action**: Develop an Internal xG Model (or enhance existing integration).
    *   **Details**: Investigate building a proprietary xG model based on shot locations, shot type, body part, assist type, etc. Alternatively, if building from scratch is too resource-intensive, explore more advanced ways to integrate and validate external xG data, perhaps by calibrating it.
    *   **Benefit**: Greater control over xG accuracy and methodology, reducing external dependency.

**Phase 3: Advanced Context & Robustness (Mid-term - 6-12 months)**

*   **Action**: Integrate Match Context Features.
    *   **Details**: Add features for match importance (derby, rivalry, cup final), weather conditions (if data is available), and potentially referee statistics (average cards per game, penalty rate).
    *   **Benefit**: Account for external factors that can influence match outcomes.
*   **Action**: Enhance Team Chemistry & Fatigue Features.
    *   **Details**: Develop features for team cohesion (e.g., average time players have played together, manager tenure) and fatigue (e.g., days since last match, travel distance).
    *   **Benefit**: Capture subtle but important influences on team performance.
*   **Action**: Model Architecture Review.
    *   **Details**: Evaluate if XGBoost is still the optimal model. Explore deep learning approaches (e.g., LSTMs for sequential data, graph neural networks for player interactions) if the complexity of new features warrants it.
    *   **Benefit**: Potentially unlock higher predictive performance with more sophisticated models.
*   **Action**: Comprehensive Backtesting and Calibration.
    *   **Details**: Establish a robust backtesting framework to evaluate model performance over various historical periods and competition types. Implement rigorous calibration techniques to ensure predicted probabilities are well-calibrated.
    *   **Benefit**: Ensure model reliability and trustworthiness.

**Phase 4: Continuous Learning & Deployment (Ongoing)**

*   **Action**: Implement Continuous Training Pipeline.
    *   **Details**: Automate the retraining of models with new data on a regular basis (e.g., weekly, monthly) to ensure they remain up-to-date.
    *   **Benefit**: Prevent model decay and maintain high accuracy.
*   **Action**: A/B Testing Framework.
    *   **Details**: Develop a system to A/B test new features or model versions in a live environment before full deployment.
    *   **Benefit**: Safely evaluate improvements and minimize risks.
*   **Action**: Expand to More Competitions/Leagues.
    *   **Details**: Generalize the feature engineering and model training to cover a wider range of football competitions beyond just the World Cup.
    *   **Benefit**: Increase the applicability and value of the prediction engine.

This roadmap provides a structured approach to evolving the prediction engine, focusing on incremental improvements while also planning for significant advancements in data utilization and model sophistication.
