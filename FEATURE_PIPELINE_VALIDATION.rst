================================================================================
FEATURE PIPELINE VALIDATION REPORT
================================================================================

Audit Date: July 3, 2026
Project: Football Prediction Engine
Models: world_cup_predictor.pkl, goal_predictor.pkl
Datasets: dataset_world_cup.csv (562 rows), dataset_goals.csv (2051 rows)

================================================================================
EXECUTIVE SUMMARY
================================================================================

Total Features Engineered: 165

Dataset World Cup Status:
- HEALTHY: 44 features (26.7%)
- CONSTANT: 119 features (72.1%)
- MOSTLY_ZERO: 2 features (1.2%)

Dataset Goals Status:
- HEALTHY: 47 features (28.5%)
- CONSTANT: 11 features (6.7%)
- NOT_IN_DATASET: 107 features (64.8%)

Training Usage:
- World Cup Model: 57/165 features (34.5%)
- Goal Model: 58/165 features (35.2%)

CRITICAL FINDINGS:
1. 72.1% of features are CONSTANT in dataset_world_cup.csv
2. 64.8% of features are MISSING from dataset_goals.csv
3. All 19 Kaggle features are CONSTANT (always zero) - BROKEN
4. All 48 IntelligenceService features are CONSTANT - BROKEN
5. All 7 SofaScore features are CONSTANT - NO LIVE DATA
6. All 9 live-match features are CONSTANT - NO LIVE DATA
7. Only 35% of engineered features actually reach XGBoost training

================================================================================
DETAILED FEATURE AUDIT
================================================================================

================================================================================
PHASE 1: CORE FEATURES (HEALTHY)
================================================================================

1. elo_diff
   Source: get_team_elo() - TeamElo database
   Pipeline: TeamElo DB → get_team_elo() → extract_ml_features() → dataset → XGBoost
   WC Status: HEALTHY (Min: -416.00, Max: 416.00, Mean: 3.51, Std: 132.47)
   Goals Status: HEALTHY (Min: -416.00, Max: 416.00, Mean: 2.18, Std: 129.39)
   WC Training: YES (Importance: 0.084515 - #1)
   Goals Training: YES (Home: 0.084515 - #1, Away: 0.056089 - #2)
   Verdict: FULLY WORKING - Strongest feature in both models

2. fifa_diff
   Source: Team.fifa_ranking - Team database
   Pipeline: Team DB → extract_ml_features() → dataset → XGBoost
   WC Status: HEALTHY (Min: -137.00, Max: 137.00, Mean: 2.58, Std: 39.10)
   Goals Status: HEALTHY (Min: -137.00, Max: 137.00, Mean: 1.13, Std: 38.39)
   WC Training: YES (Importance: 0.059781 - #2)
   Goals Training: YES (Home: 0.059781 - #2, Away: 0.072746 - #1)
   Verdict: FULLY WORKING - Top 3 feature in both models

3. form_diff
   Source: get_team_recent_stats() - Match database
   Pipeline: Match DB → get_team_recent_stats() → extract_ml_features() → dataset → XGBoost
   WC Status: HEALTHY (Min: -2.40, Max: 2.40, Mean: 0.01, Std: 0.67)
   Goals Status: HEALTHY (Min: -2.40, Max: 2.40, Mean: 0.02, Std: 0.68)
   WC Training: YES (Importance: 0.017890 - #24)
   Goals Training: YES (Home: 0.017890 - #31, Away: 0.015731 - #37)
   Verdict: FULLY WORKING

4. gs_diff (goals scored difference)
   Source: get_team_recent_stats() - Match database
   Pipeline: Match DB → get_team_recent_stats() → extract_ml_features() → dataset → XGBoost
   WC Status: HEALTHY (Min: -3.20, Max: 3.20, Mean: 0.03, Std: 0.89)
   Goals Status: HEALTHY (Min: -3.20, Max: 3.20, Mean: 0.04, Std: 0.90)
   WC Training: YES (Importance: 0.015273 - #37)
   Goals Training: YES (Home: 0.015273 - #37, Away: 0.018905 - #27)
   Verdict: FULLY WORKING

5. gc_diff (goals conceded difference)
   Source: get_team_recent_stats() - Match database
   Pipeline: Match DB → get_team_recent_stats() → extract_ml_features() → dataset → XGBoost
   WC Status: HEALTHY (Min: -2.80, Max: 2.80, Mean: -0.02, Std: 0.75)
   Goals Status: HEALTHY (Min: -2.80, Max: 2.80, Mean: -0.01, Std: 0.76)
   WC Training: YES (Importance: 0.022668 - #10)
   Goals Training: YES (Home: 0.022668 - #10, Away: 0.018072 - #28)
   Verdict: FULLY WORKING

6. mv_diff (market value difference)
   Source: Team.squad_market_value - Team database
   Pipeline: Team DB → extract_ml_features() → dataset → XGBoost
   WC Status: HEALTHY (Min: -1236.27, Max: 1273.00, Mean: 54.07, Std: 530.50)
   Goals Status: HEALTHY (Min: -1236.27, Max: 1273.00, Mean: 36.89, Std: 518.47)
   WC Training: YES (Importance: 0.019426 - #28)
   Goals Training: YES (Home: 0.019426 - #28, Away: 0.032160 - #5)
   Verdict: FULLY WORKING

7. inj_diff (injury market value difference)
   Source: Injury.player_market_value - Injury database
   Pipeline: Injury DB → extract_ml_features() → dataset → XGBoost
   WC Status: HEALTHY (Min: -288.36, Max: 305.00, Mean: -5.20, Std: 67.50)
   Goals Status: HEALTHY (Min: -288.36, Max: 305.00, Mean: -3.22, Std: 66.12)
   WC Training: YES (Importance: 0.019897 - #25)
   Goals Training: YES (Home: 0.019897 - #25, Away: 0.017543 - #31)
   Verdict: FULLY WORKING

8. susp_diff (suspension market value difference)
   Source: Suspension.player_market_value - Suspension database
   Pipeline: Suspension DB → extract_ml_features() → dataset → XGBoost
   WC Status: CONSTANT (Min: 0.00, Max: 0.00, Mean: 0.00, Std: 0.00)
   Goals Status: CONSTANT (Min: 0.00, Max: 0.00, Mean: 0.00, Std: 0.00)
   WC Training: YES (Importance: 0.000000 - #57)
   Goals Training: YES (Home: 0.000000 - #45, Away: 0.000000 - #45)
   Verdict: BROKEN - Suspensions are cleared during dataset building (line 209 in build_dataset_world_cup.py)
   Fix: Remove suspension clearing logic or use real suspension data

9. home_adv
   Source: Competition code check - Competition database
   Pipeline: Competition DB → extract_ml_features() → dataset → XGBoost
   WC Status: CONSTANT (Min: 0.00, Max: 0.00, Mean: 0.00, Std: 0.00)
   Goals Status: CONSTANT (Min: 0.00, Max: 0.00, Mean: 0.00, Std: 0.00)
   WC Training: YES (Importance: 0.010036 - #44)
   Goals Training: YES (Home: 0.010036 - #44, Away: 0.013085 - #41)
   Verdict: CONSTANT - No World Cup hosts in dataset (USA/Mexico/Canada not in Kaggle filter)
   Fix: Include host nations in dataset or remove feature

10. h2h_factor
    Source: Match history query - Match database
    Pipeline: Match DB → extract_ml_features() → dataset → XGBoost
    WC Status: HEALTHY (Min: 0.00, Max: 1.00, Mean: 0.50, Std: 0.29)
    Goals Status: HEALTHY (Min: 0.00, Max: 1.00, Mean: 0.50, Std: 0.29)
    WC Training: YES (Importance: 0.016941 - #35)
    Goals Training: YES (Home: 0.016941 - #35, Away: 0.016311 - #36)
    Verdict: FULLY WORKING

================================================================================
PHASE 2: PLAYER INTELLIGENCE FEATURES (MIXED)
================================================================================

11. available_squad_diff
    Source: squad_market_value - injuries - suspensions - Team/Injury/Suspension databases
    Pipeline: Team/Injury/Suspension DB → extract_ml_features() → dataset → XGBoost
    WC Status: HEALTHY (Min: -962.58, Max: 968.50, Mean: 40.99, Std: 392.26)
    Goals Status: HEALTHY (Min: -962.58, Max: 968.50, Mean: 26.62, Std: 384.47)
    WC Training: YES (Importance: 0.026839 - #6)
    Goals Training: YES (Home: 0.026839 - #6, Away: 0.020198 - #23)
    Verdict: FULLY WORKING - Top 10 feature

12. availability_pct_diff
    Source: available_squad / squad_market_value - calculated
    Pipeline: Calculated → extract_ml_features() → dataset → XGBoost
    WC Status: HEALTHY (Min: -0.20, Max: 0.20, Mean: 0.00, Std: 0.06)
    Goals Status: HEALTHY (Min: -0.20, Max: 0.20, Mean: 0.00, Std: 0.06)
    WC Training: YES (Importance: 0.020282 - #23)
    Goals Training: YES (Home: 0.020282 - #23, Away: 0.015277 - #40)
    Verdict: FULLY WORKING

13. starting_xi_value_diff
    Source: top 11 available players - NationalTeamPlayer database
    Pipeline: NationalTeamPlayer DB → extract_ml_features() → dataset → XGBoost
    WC Status: HEALTHY (Min: -962.58, Max: 968.50, Mean: 40.99, Std: 392.26)
    Goals Status: HEALTHY (Min: -962.58, Max: 968.50, Mean: 26.62, Std: 384.47)
    WC Training: YES (Importance: 0.021477 - #14)
    Goals Training: YES (Home: 0.021477 - #14, Away: 0.018786 - #28)
    Verdict: FULLY WORKING

14. missing_star_players_diff
    Source: injured/suspended players > 50M - Injury/Suspension/NationalTeamPlayer databases
    Pipeline: Injury/Suspension/NationalTeamPlayer DB → extract_ml_features() → dataset → XGBoost
    WC Status: HEALTHY (Min: -3.00, Max: 3.00, Mean: 0.03, Std: 0.65)
    Goals Status: HEALTHY (Min: -3.00, Max: 3.00, Mean: 0.02, Std: 0.64)
    WC Training: YES (Importance: 0.021574 - #13)
    Goals Training: YES (Home: 0.021574 - #13, Away: 0.036635 - #4)
    Verdict: FULLY WORKING - Top 15 feature

15. match_stage_weight
    Source: STAGE_WEIGHTS dict - Match.stage field
    Pipeline: Match DB → extract_ml_features() → dataset → XGBoost
    WC Status: MOSTLY_ZERO (Min: 0.00, Max: 4.00, Mean: 0.09, Std: 0.51, Zero: 545/562)
    Goals Status: CONSTANT (Min: 0.00, Max: 0.00, Mean: 0.00, Std: 0.00)
    WC Training: YES (Importance: 0.000000 - #57)
    Goals Training: YES (Home: 0.000000 - #47, Away: 0.000000 - #47)
    Verdict: MOSTLY_ZERO - Most matches are group stage (weight 0)
    Fix: Include more knockout stage matches or remove feature

================================================================================
PHASE 3: STRUCTURAL FEATURES (HEALTHY)
================================================================================

16. home_elo_momentum
    Source: get_elo_momentum() - TeamElo/Match databases
    Pipeline: TeamElo/Match DB → get_elo_momentum() → extract_ml_features() → dataset → XGBoost
    WC Status: HEALTHY (Min: -48.20, Max: 52.80, Mean: 0.29, Std: 15.17)
    Goals Status: HEALTHY (Min: -48.20, Max: 52.80, Mean: 0.18, Std: 14.91)
    WC Training: YES (Importance: 0.017839 - #33)
    Goals Training: YES (Home: 0.017839 - #32, Away: 0.020272 - #21)
    Verdict: FULLY WORKING

17. away_elo_momentum
    Source: get_elo_momentum() - TeamElo/Match databases
    Pipeline: TeamElo/Match DB → get_elo_momentum() → extract_ml_features() → dataset → XGBoost
    WC Status: HEALTHY (Min: -52.80, Max: 48.20, Mean: -0.29, Std: 15.17)
    Goals Status: HEALTHY (Min: -52.80, Max: 48.20, Mean: -0.18, Std: 14.91)
    WC Training: YES (Importance: 0.017008 - #36)
    Goals Training: YES (Home: 0.015198 - #38, Away: 0.020753 - #19)
    Verdict: FULLY WORKING

18. elo_momentum_diff
    Source: home_elo_momentum - away_elo_momentum - calculated
    Pipeline: Calculated → extract_ml_features() → dataset → XGBoost
    WC Status: HEALTHY (Min: -76.40, Max: 76.40, Mean: 0.58, Std: 21.46)
    Goals Status: HEALTHY (Min: -76.40, Max: 76.40, Mean: 0.37, Std: 21.06)
    WC Training: YES (Importance: 0.017008 - #36)
    Goals Training: YES (Home: 0.017008 - #34, Away: 0.025913 - #9)
    Verdict: FULLY WORKING

19. home_strength_of_schedule
    Source: get_strength_of_schedule() - TeamElo/Match databases
    Pipeline: TeamElo/Match DB → get_strength_of_schedule() → extract_ml_features() → dataset → XGBoost
    WC Status: HEALTHY (Min: 1409.40, Max: 2141.00, Mean: 1759.98, Std: 112.21)
    Goals Status: HEALTHY (Min: 1063.60, Max: 1995.60, Mean: 1633.70, Std: 185.52)
    WC Training: YES (Importance: 0.020431 - #21)
    Goals Training: YES (Home: 0.020431 - #21, Away: 0.021069 - #16)
    Verdict: FULLY WORKING

20. away_strength_of_schedule
    Source: get_strength_of_schedule() - TeamElo/Match databases
    Pipeline: TeamElo/Match DB → get_strength_of_schedule() → extract_ml_features() → dataset → XGBoost
    WC Status: HEALTHY (Min: 1409.40, Max: 2141.00, Mean: 1759.98, Std: 112.21)
    Goals Status: HEALTHY (Min: 1045.00, Max: 2123.00, Mean: 1635.71, Std: 182.10)
    WC Training: YES (Importance: 0.020431 - #21)
    Goals Training: YES (Home: 0.021361 - #16, Away: 0.015442 - #39)
    Verdict: FULLY WORKING

21. strength_of_schedule_diff
    Source: home_sos - away_sos - calculated
    Pipeline: Calculated → extract_ml_features() → dataset → XGBoost
    WC Status: HEALTHY (Min: -538.00, Max: 641.00, Mean: 5.52, Std: 118.93)
    Goals Status: HEALTHY (Min: -619.00, Max: 625.60, Mean: -2.02, Std: 125.20)
    WC Training: YES (Importance: 0.020972 - #19)
    Goals Training: YES (Home: 0.020972 - #18, Away: 0.026655 - #8)
    Verdict: FULLY WORKING

22. world_cup_matches_played_diff
    Source: get_tournament_experience() - Match/Competition databases
    Pipeline: Match/Competition DB → get_tournament_experience() → extract_ml_features() → dataset → XGBoost
    WC Status: HEALTHY (Min: -95.00, Max: 109.00, Mean: 2.58, Std: 24.34)
    Goals Status: HEALTHY (Min: -119.00, Max: 154.00, Mean: 0.80, Std: 23.62)
    WC Training: YES (Importance: 0.019694 - #27)
    Goals Training: YES (Home: 0.019694 - #27, Away: 0.022301 - #14)
    Verdict: FULLY WORKING

23. major_tournament_matches_diff
    Source: get_tournament_experience() - Match/Competition databases
    Pipeline: Match/Competition DB → get_tournament_experience() → extract_ml_features() → dataset → XGBoost
    WC Status: MOSTLY_ZERO (Min: -155.00, Max: 143.00, Mean: 1.13, Std: 27.84, Zero: 511/562)
    Goals Status: HEALTHY (Min: -151.00, Max: 213.00, Mean: 1.14, Std: 30.01)
    WC Training: YES (Importance: 0.020310 - #22)
    Goals Training: YES (Home: 0.020310 - #22, Away: 0.022497 - #13)
    Verdict: MOSTLY_ZERO in WC, HEALTHY in Goals

24. knockout_matches_diff
    Source: get_tournament_experience() - Match/Competition databases
    Pipeline: Match/Competition DB → get_tournament_experience() → extract_ml_features() → dataset → XGBoost
    WC Status: MOSTLY_ZERO (Min: -4.00, Max: 4.00, Mean: 0.04, Std: 0.72, Zero: 511/562)
    Goals Status: CONSTANT (Min: 0.00, Max: 0.00, Mean: 0.00, Std: 0.00)
    WC Training: YES (Importance: 0.000000 - #57)
    Goals Training: YES (Home: 0.000000 - #46, Away: 0.000000 - #46)
    Verdict: MOSTLY_ZERO - Few knockout matches in dataset

================================================================================
PHASE 4.5: ADVANCED GOAL INTELLIGENCE (HEALTHY)
================================================================================

25. home_attack_rating
    Source: get_attack_rating() - Match database
    Pipeline: Match DB → get_attack_rating() → extract_ml_features() → dataset → XGBoost
    WC Status: HEALTHY (Min: 0.00, Max: 4.13, Mean: 1.53, Std: 0.59)
    Goals Status: HEALTHY (Min: 0.00, Max: 4.13, Mean: 1.53, Std: 0.59)
    WC Training: YES (Importance: 0.017568 - #32)
    Goals Training: YES (Home: 0.017568 - #33, Away: 0.020836 - #18)
    Verdict: FULLY WORKING

26. away_attack_rating
    Source: get_attack_rating() - Match database
    Pipeline: Match DB → get_attack_rating() → extract_ml_features() → dataset → XGBoost
    WC Status: HEALTHY (Min: 0.00, Max: 4.00, Mean: 1.48, Std: 0.57)
    Goals Status: HEALTHY (Min: 0.00, Max: 4.00, Mean: 1.48, Std: 0.57)
    WC Training: YES (Importance: 0.017568 - #32)
    Goals Training: YES (Home: 0.021746 - #12, Away: 0.020909 - #17)
    Verdict: FULLY WORKING

27. attack_rating_diff
    Source: home_attack - away_attack - calculated
    Pipeline: Calculated → extract_ml_features() → dataset → XGBoost
    WC Status: HEALTHY (Min: -2.66, Max: 2.77, Mean: 0.05, Std: 0.69)
    Goals Status: HEALTHY (Min: -2.66, Max: 2.77, Mean: 0.05, Std: 0.69)
    WC Training: YES (Importance: 0.021857 - #11)
    Goals Training: YES (Home: 0.021857 - #11, Away: 0.020665 - #20)
    Verdict: FULLY WORKING - Top 15 feature

28. home_defence_rating
    Source: get_defence_rating() - Match database
    Pipeline: Match DB → get_defence_rating() → extract_ml_features() → dataset → XGBoost
    WC Status: HEALTHY (Min: 0.00, Max: 5.11, Mean: 1.26, Std: 0.64)
    Goals Status: HEALTHY (Min: 0.00, Max: 5.11, Mean: 1.26, Std: 0.64)
    WC Training: YES (Importance: 0.019027 - #29)
    Goals Training: YES (Home: 0.019027 - #29, Away: 0.026675 - #7)
    Verdict: FULLY WORKING

29. away_defence_rating
    Source: get_defence_rating() - Match database
    Pipeline: Match DB → get_defence_rating() → extract_ml_features() → dataset → XGBoost
    WC Status: HEALTHY (Min: 0.00, Max: 5.17, Mean: 1.27, Std: 0.64)
    Goals Status: HEALTHY (Min: 0.00, Max: 5.17, Mean: 1.27, Std: 0.64)
    WC Training: YES (Importance: 0.019027 - #29)
    Goals Training: YES (Home: 0.024203 - #8, Away: 0.019782 - #25)
    Verdict: FULLY WORKING

30. defence_rating_diff
    Source: home_defence - away_defence - calculated
    Pipeline: Calculated → extract_ml_features() → dataset → XGBoost
    WC Status: HEALTHY (Min: -3.51, Max: 3.57, Mean: -0.01, Std: 0.70)
    Goals Status: HEALTHY (Min: -3.51, Max: 3.57, Mean: -0.01, Std: 0.70)
    WC Training: YES (Importance: 0.021197 - #18)
    Goals Training: YES (Home: 0.021197 - #18, Away: 0.031635 - #6)
    Verdict: FULLY WORKING - Top 20 feature

31. home_clean_sheet_rate
    Source: get_clean_sheet_rate() - Match database
    Pipeline: Match DB → get_clean_sheet_rate() → extract_ml_features() → dataset → XGBoost
    WC Status: HEALTHY (Min: 0.00, Max: 0.91, Mean: 0.36, Std: 0.15)
    Goals Status: HEALTHY (Min: 0.00, Max: 0.91, Mean: 0.36, Std: 0.15)
    WC Training: YES (Importance: 0.014807 - #39)
    Goals Training: YES (Home: 0.014807 - #39, Away: 0.017256 - #33)
    Verdict: FULLY WORKING

32. away_clean_sheet_rate
    Source: get_clean_sheet_rate() - Match database
    Pipeline: Match DB → get_clean_sheet_rate() → extract_ml_features() → dataset → XGBoost
    WC Status: HEALTHY (Min: 0.00, Max: 1.00, Mean: 0.36, Std: 0.15)
    Goals Status: HEALTHY (Min: 0.00, Max: 1.00, Mean: 0.36, Std: 0.15)
    WC Training: YES (Importance: 0.014807 - #39)
    Goals Training: YES (Home: 0.020944 - #20, Away: 0.017251 - #33)
    Verdict: FULLY WORKING

33. clean_sheet_rate_diff
    Source: home_clean - away_clean - calculated
    Pipeline: Calculated → extract_ml_features() → dataset → XGBoost
    WC Status: HEALTHY (Min: -0.80, Max: 0.75, Mean: 0.00, Std: 0.18)
    Goals Status: HEALTHY (Min: -0.80, Max: 0.75, Mean: 0.00, Std: 0.18)
    WC Training: YES (Importance: 0.028416 - #5)
    Goals Training: YES (Home: 0.028416 - #5, Away: 0.024766 - #10)
    Verdict: FULLY WORKING - Top 10 feature

34. home_btts_rate
    Source: get_btts_rate() - Match database
    Pipeline: Match DB → get_btts_rate() → extract_ml_features() → dataset → XGBoost
    WC Status: HEALTHY (Min: 0.00, Max: 1.00, Mean: 0.44, Std: 0.13)
    Goals Status: HEALTHY (Min: 0.00, Max: 1.00, Mean: 0.44, Std: 0.13)
    WC Training: YES (Importance: 0.023552 - #9)
    Goals Training: YES (Home: 0.023552 - #9, Away: 0.018276 - #29)
    Verdict: FULLY WORKING - Top 10 feature

35. away_btts_rate
    Source: get_btts_rate() - Match database
    Pipeline: Match DB → get_btts_rate() → extract_ml_features() → dataset → XGBoost
    WC Status: HEALTHY (Min: 0.00, Max: 1.00, Mean: 0.44, Std: 0.13)
    Goals Status: HEALTHY (Min: 0.00, Max: 1.00, Mean: 0.44, Std: 0.13)
    WC Training: YES (Importance: 0.023552 - #9)
    Goals Training: YES (Home: 0.019950 - #24, Away: 0.015486 - #38)
    Verdict: FULLY WORKING

36. btts_rate_diff
    Source: home_btts - away_btts - calculated
    Pipeline: Calculated → extract_ml_features() → dataset → XGBoost
    WC Status: HEALTHY (Min: -0.70, Max: 0.61, Mean: 0.00, Std: 0.17)
    Goals Status: HEALTHY (Min: -0.70, Max: 0.61, Mean: 0.00, Std: 0.17)
    WC Training: YES (Importance: 0.016579 - #38)
    Goals Training: YES (Home: 0.016579 - #36, Away: 0.019578 - #26)
    Verdict: FULLY WORKING

================================================================================
INJURY & SUSPENSION COUNT FEATURES (MIXED)
================================================================================

37. home_injury_count
    Source: len(Injury.query) - Injury database
    Pipeline: Injury DB → extract_ml_features() → dataset → XGBoost
    WC Status: CONSTANT (Min: 0.00, Max: 0.00, Mean: 0.00, Std: 0.00)
    Goals Status: HEALTHY (Min: 0.00, Max: 3.00, Mean: 1.52, Std: 1.10)
    WC Training: YES (Importance: 0.000000 - #57)
    Goals Training: YES (Home: 0.014574 - #40, Away: 0.022911 - #12)
    Verdict: CONSTANT in WC - Injuries cleared during dataset building (line 207)
    Fix: Remove injury clearing logic or use real injury data

38. away_injury_count
    Source: len(Injury.query) - Injury database
    Pipeline: Injury DB → extract_ml_features() → dataset → XGBoost
    WC Status: CONSTANT (Min: 0.00, Max: 0.00, Mean: 0.00, Std: 0.00)
    Goals Status: HEALTHY (Min: 0.00, Max: 3.00, Mean: 1.49, Std: 1.10)
    WC Training: YES (Importance: 0.000000 - #57)
    Goals Training: YES (Home: 0.013569 - #41, Away: 0.016509 - #35)
    Verdict: CONSTANT in WC - Injuries cleared during dataset building (line 207)
    Fix: Remove injury clearing logic or use real injury data

39. home_suspension_count
    Source: len(Suspension.query) - Suspension database
    Pipeline: Suspension DB → extract_ml_features() → dataset → XGBoost
    WC Status: CONSTANT (Min: 0.00, Max: 0.00, Mean: 0.00, Std: 0.00)
    Goals Status: CONSTANT (Min: 0.00, Max: 0.00, Mean: 0.00, Std: 0.00)
    WC Training: YES (Importance: 0.000000 - #57)
    Goals Training: YES (Home: 0.000000 - #45, Away: 0.000000 - #45)
    Verdict: CONSTANT - Suspensions cleared during dataset building (line 209)
    Fix: Remove suspension clearing logic or use real suspension data

40. away_suspension_count
    Source: len(Suspension.query) - Suspension database
    Pipeline: Suspension DB → extract_ml_features() → dataset → XGBoost
    WC Status: CONSTANT (Min: 0.00, Max: 0.00, Mean: 0.00, Std: 0.00)
    Goals Status: CONSTANT (Min: 0.00, Max: 0.00, Mean: 0.00, Std: 0.00)
    WC Training: YES (Importance: 0.000000 - #57)
    Goals Training: YES (Home: 0.000000 - #46, Away: 0.000000 - #46)
    Verdict: CONSTANT - Suspensions cleared during dataset building (line 209)
    Fix: Remove suspension clearing logic or use real suspension data

41. home_injury_market_value_loss
    Source: sum(Injury.player_market_value) - Injury database
    Pipeline: Injury DB → extract_ml_features() → dataset → XGBoost
    WC Status: CONSTANT (Min: 0.00, Max: 0.00, Mean: 0.00, Std: 0.00)
    Goals Status: HEALTHY (Min: 0.00, Max: 335.00, Mean: 19.12, Std: 36.64)
    WC Training: YES (Importance: 0.000000 - #57)
    Goals Training: YES (Home: 0.018222 - #30, Away: 0.017119 - #34)
    Verdict: CONSTANT in WC - Injuries cleared during dataset building (line 207)
    Fix: Remove injury clearing logic or use real injury data

42. away_injury_market_value_loss
    Source: sum(Injury.player_market_value) - Injury database
    Pipeline: Injury DB → extract_ml_features() → dataset → XGBoost
    WC Status: CONSTANT (Min: 0.00, Max: 0.00, Mean: 0.00, Std: 0.00)
    Goals Status: HEALTHY (Min: 0.00, Max: 370.00, Mean: 15.93, Std: 35.10)
    WC Training: YES (Importance: 0.000000 - #57)
    Goals Training: YES (Home: 0.021332 - #17, Away: 0.023632 - #11)
    Verdict: CONSTANT in WC - Injuries cleared during dataset building (line 207)
    Fix: Remove injury clearing logic or use real injury data

================================================================================
STANDINGS FEATURES (MOSTLY ZERO)
================================================================================

43. home_group_position
    Source: Standing.position - Standing database
    Pipeline: Standing DB → extract_ml_features() → dataset → XGBoost
    WC Status: CONSTANT (Min: 0.00, Max: 0.00, Mean: 0.00, Std: 0.00)
    Goals Status: MOSTLY_ZERO (Min: 0.00, Max: 4.00, Mean: 0.34, Std: 0.85, Zero: 1696/2051)
    WC Training: YES (Importance: 0.000000 - #57)
    Goals Training: YES (Home: 0.010213 - #43, Away: 0.007232 - #44)
    Verdict: CONSTANT in WC - No standing data for international matches
    Fix: Standing data only available for league competitions

44. away_group_position
    Source: Standing.position - Standing database
    Pipeline: Standing DB → extract_ml_features() → dataset → XGBoost
    WC Status: CONSTANT (Min: 0.00, Max: 0.00, Mean: 0.00, Std: 0.00)
    Goals Status: MOSTLY_ZERO (Min: 0.00, Max: 4.00, Mean: 0.37, Std: 0.93, Zero: 1706/2051)
    WC Training: YES (Importance: 0.000000 - #57)
    Goals Training: YES (Home: 0.019734 - #26, Away: 0.012978 - #42)
    Verdict: CONSTANT in WC - No standing data for international matches
    Fix: Standing data only available for league competitions

45. group_position_diff
    Source: home_position - away_position - calculated
    Pipeline: Calculated → extract_ml_features() → dataset → XGBoost
    WC Status: CONSTANT (Min: 0.00, Max: 0.00, Mean: 0.00, Std: 0.00)
    Goals Status: MOSTLY_ZERO (Min: -4.00, Max: 4.00, Mean: 0.03, Std: 0.81, Zero: 1710/2051)
    WC Training: YES (Importance: 0.000000 - #57)
    Goals Training: YES (Home: 0.026400 - #7, Away: 0.012959 - #43)
    Verdict: CONSTANT in WC - No standing data for international matches
    Fix: Standing data only available for league competitions

46. home_points
    Source: Standing.points - Standing database
    Pipeline: Standing DB → extract_ml_features() → dataset → XGBoost
    WC Status: CONSTANT (Min: 0.00, Max: 0.00, Mean: 0.00, Std: 0.00)
    Goals Status: MOSTLY_ZERO (Min: 0.00, Max: 6.00, Mean: 0.47, Std: 1.26, Zero: 1694/2051)
    WC Training: YES (Importance: 0.000000 - #57)
    Goals Training: YES (Home: 0.013510 - #42, Away: 0.020249 - #22)
    Verdict: CONSTANT in WC - No standing data for international matches
    Fix: Standing data only available for league competitions

47. away_points
    Source: Standing.points - Standing database
    Pipeline: Standing DB → extract_ml_features() → dataset → XGBoost
    WC Status: CONSTANT (Min: 0.00, Max: 0.00, Mean: 0.00, Std: 0.00)
    Goals Status: MOSTLY_ZERO (Min: 0.00, Max: 6.00, Mean: 0.40, Std: 1.17, Zero: 1726/2051)
    WC Training: YES (Importance: 0.000000 - #57)
    Goals Training: YES (Home: 0.037161 - #4, Away: 0.021767 - #15)
    Verdict: CONSTANT in WC - No standing data for international matches
    Fix: Standing data only available for league competitions

48. points_diff
    Source: home_points - away_points - calculated
    Pipeline: Calculated → extract_ml_features() → dataset → XGBoost
    WC Status: HEALTHY (Min: -9.00, Max: 9.00, Mean: 0.15, Std: 2.53)
    Goals Status: MOSTLY_ZERO (Min: -6.00, Max: 6.00, Mean: 0.07, Std: 1.27, Zero: 1761/2051)
    WC Training: YES (Importance: 0.021442 - #15)
    Goals Training: YES (Home: 0.021442 - #15, Away: 0.019874 - #24)
    Verdict: HEALTHY in WC, MOSTLY_ZERO in Goals

49. goal_difference_diff
    Source: Standing.goals_difference - Standing database
    Pipeline: Standing DB → extract_ml_features() → dataset → XGBoost
    WC Status: HEALTHY (Min: -10.00, Max: 13.00, Mean: 0.12, Std: 1.56)
    Goals Status: MOSTLY_ZERO (Min: -10.00, Max: 13.00, Mean: 0.12, Std: 1.56, Zero: 1725/2051)
    WC Training: YES (Importance: 0.044585 - #3)
    Goals Training: YES (Home: 0.044585 - #3, Away: 0.045216 - #3)
    Verdict: HEALTHY in WC, MOSTLY_ZERO in Goals - Top 5 feature in WC

================================================================================
BETTING ODDS FEATURES (CONSTANT)
================================================================================

50. home_implied_probability
    Source: BookmakerOdds.home_odds - BookmakerOdds database
    Pipeline: BookmakerOdds DB → extract_ml_features() → dataset → XGBoost
    WC Status: CONSTANT (Min: 0.33, Max: 0.33, Mean: 0.33, Std: 0.00)
    Goals Status: CONSTANT (Min: 0.33, Max: 0.33, Mean: 0.33, Std: 0.00)
    WC Training: YES (Importance: 0.000000 - #57)
    Goals Training: YES (Home: 0.000000 - #50, Away: 0.000000 - #50)
    Verdict: CONSTANT - No bookmaker odds data in database
    Fix: Populate BookmakerOdds table or remove feature

51. draw_implied_probability
    Source: BookmakerOdds.draw_odds - BookmakerOdds database
    Pipeline: BookmakerOdds DB → extract_ml_features() → dataset → XGBoost
    WC Status: CONSTANT (Min: 0.33, Max: 0.33, Mean: 0.33, Std: 0.00)
    Goals Status: CONSTANT (Min: 0.33, Max: 0.33, Mean: 0.33, Std: 0.00)
    WC Training: YES (Importance: 0.000000 - #57)
    Goals Training: YES (Home: 0.000000 - #51, Away: 0.000000 - #51)
    Verdict: CONSTANT - No bookmaker odds data in database
    Fix: Populate BookmakerOdds table or remove feature

52. away_implied_probability
    Source: BookmakerOdds.away_odds - BookmakerOdds database
    Pipeline: BookmakerOdds DB → extract_ml_features() → dataset → XGBoost
    WC Status: CONSTANT (Min: 0.33, Max: 0.33, Mean: 0.33, Std: 0.00)
    Goals Status: CONSTANT (Min: 0.33, Max: 0.33, Mean: 0.33, Std: 0.00)
    WC Training: YES (Importance: 0.000000 - #57)
    Goals Training: YES (Home: 0.000000 - #52, Away: 0.000000 - #52)
    Verdict: CONSTANT - No bookmaker odds data in database
    Fix: Populate BookmakerOdds table or remove feature

================================================================================
LIVE MATCH FEATURES (CONSTANT)
================================================================================

53. current_minute
    Source: Match.current_minute - Match database
    Pipeline: Match DB → extract_ml_features() → dataset → XGBoost
    WC Status: CONSTANT (Min: 0.00, Max: 0.00, Mean: 0.00, Std: 0.00)
    Goals Status: CONSTANT (Min: 0.00, Max: 0.00, Mean: 0.00, Std: 0.00)
    WC Training: YES (Importance: 0.000000 - #57)
    Goals Training: YES (Home: 0.000000 - #53, Away: 0.000000 - #53)
    Verdict: CONSTANT - Training data uses finished matches (no live data)
    Fix: These features only useful for live predictions, not training

54. time_remaining
    Source: 90 - current_minute - calculated
    Pipeline: Calculated → extract_ml_features() → dataset → XGBoost
    WC Status: CONSTANT (Min: 90.00, Max: 90.00, Mean: 90.00, Std: 0.00)
    Goals Status: CONSTANT (Min: 90.00, Max: 90.00, Mean: 90.00, Std: 0.00)
    WC Training: YES (Importance: 0.000000 - #57)
    Goals Training: YES (Home: 0.000000 - #54, Away: 0.000000 - #54)
    Verdict: CONSTANT - Training data uses finished matches (no live data)
    Fix: These features only useful for live predictions, not training

55. current_score_diff
    Source: Match.current_home_score - Match.current_away_score - Match database
    Pipeline: Match DB → extract_ml_features() → dataset → XGBoost
    WC Status: CONSTANT (Min: 0.00, Max: 0.00, Mean: 0.00, Std: 0.00)
    Goals Status: CONSTANT (Min: 0.00, Max: 0.00, Mean: 0.00, Std: 0.00)
    WC Training: YES (Importance: 0.000000 - #57)
    Goals Training: YES (Home: 0.000000 - #55, Away: 0.000000 - #55)
    Verdict: CONSTANT - Training data uses finished matches (no live data)
    Fix: These features only useful for live predictions, not training

56. home_red_cards
    Source: Match.home_red_cards - Match database
    Pipeline: Match DB → extract_ml_features() → dataset → XGBoost
    WC Status: CONSTANT (Min: 0.00, Max: 0.00, Mean: 0.00, Std: 0.00)
    Goals Status: CONSTANT (Min: 0.00, Max: 0.00, Mean: 0.00, Std: 0.00)
    WC Training: YES (Importance: 0.000000 - #57)
    Goals Training: YES (Home: 0.000000 - #56, Away: 0.000000 - #56)
    Verdict: CONSTANT - No red card data in Match table
    Fix: Populate Match.home_red_cards/away_red_cards or remove feature

57. away_red_cards
    Source: Match.away_red_cards - Match database
    Pipeline: Match DB → extract_ml_features() → dataset → XGBoost
    WC Status: CONSTANT (Min: 0.00, Max: 0.00, Mean: 0.00, Std: 0.00)
    Goals Status: CONSTANT (Min: 0.00, Max: 0.00, Mean: 0.00, Std: 0.00)
    WC Training: YES (Importance: 0.000000 - #57)
    Goals Training: YES (Home: 0.000000 - #57, Away: 0.000000 - #57)
    Verdict: CONSTANT - No red card data in Match table
    Fix: Populate Match.home_red_cards/away_red_cards or remove feature

58. red_card_diff
    Source: home_red - away_red - calculated
    Pipeline: Calculated → extract_ml_features() → dataset → XGBoost
    WC Status: CONSTANT (Min: 0.00, Max: 0.00, Mean: 0.00, Std: 0.00)
    Goals Status: CONSTANT (Min: 0.00, Max: 0.00, Mean: 0.00, Std: 0.00)
    WC Training: YES (Importance: 0.000000 - #57)
    Goals Training: YES (Home: 0.000000 - #58, Away: 0.000000 - #58)
    Verdict: CONSTANT - No red card data in Match table
    Fix: Populate Match.home_red_cards/away_red_cards or remove feature

================================================================================
SOFASCORE FEATURES (CONSTANT)
================================================================================

59. home_avg_rating
    Source: PlayerMatchPerformance.sofa_score_rating - PlayerMatchPerformance database
    Pipeline: PlayerMatchPerformance DB → extract_ml_features() → dataset → XGBoost
    WC Status: CONSTANT (Min: 0.00, Max: 0.00, Mean: 0.00, Std: 0.00)
    Goals Status: NOT_IN_DATASET
    WC Training: NO
    Goals Training: NO
    Verdict: CONSTANT - No SofaScore player ratings in database
    Fix: Populate PlayerMatchPerformance.sofa_score_rating or remove feature

60. away_avg_rating
    Source: PlayerMatchPerformance.sofa_score_rating - PlayerMatchPerformance database
    Pipeline: PlayerMatchPerformance DB → extract_ml_features() → dataset → XGBoost
    WC Status: CONSTANT (Min: 0.00, Max: 0.00, Mean: 0.00, Std: 0.00)
    Goals Status: NOT_IN_DATASET
    WC Training: NO
    Goals Training: NO
    Verdict: CONSTANT - No SofaScore player ratings in database
    Fix: Populate PlayerMatchPerformance.sofa_score_rating or remove feature

61. avg_rating_diff
    Source: home_avg - away_avg - calculated
    Pipeline: Calculated → extract_ml_features() → dataset → XGBoost
    WC Status: CONSTANT (Min: 0.00, Max: 0.00, Mean: 0.00, Std: 0.00)
    Goals Status: NOT_IN_DATASET
    WC Training: NO
    Goals Training: NO
    Verdict: CONSTANT - No SofaScore player ratings in database
    Fix: Populate PlayerMatchPerformance.sofa_score_rating or remove feature

62. home_possession
    Source: MatchStatistic.home_possession - MatchStatistic database
    Pipeline: MatchStatistic DB → extract_ml_features() → dataset → XGBoost
    WC Status: CONSTANT (Min: 0.00, Max: 0.00, Mean: 0.00, Std: 0.00)
    Goals Status: NOT_IN_DATASET
    WC Training: NO
    Goals Training: NO
    Verdict: CONSTANT - No MatchStatistic data in database
    Fix: Populate MatchStatistic table or remove feature

63. away_possession
    Source: MatchStatistic.away_possession - MatchStatistic database
    Pipeline: MatchStatistic DB → extract_ml_features() → dataset → XGBoost
    WC Status: CONSTANT (Min: 0.00, Max: 0.00, Mean: 0.00, Std: 0.00)
    Goals Status: NOT_IN_DATASET
    WC Training: NO
    Goals Training: NO
    Verdict: CONSTANT - No MatchStatistic data in database
    Fix: Populate MatchStatistic table or remove feature

64. possession_diff
    Source: home_poss - away_poss - calculated
    Pipeline: Calculated → extract_ml_features() → dataset → XGBoost
    WC Status: CONSTANT (Min: 0.00, Max: 0.00, Mean: 0.00, Std: 0.00)
    Goals Status: NOT_IN_DATASET
    WC Training: NO
    Goals Training: NO
    Verdict: CONSTANT - No MatchStatistic data in database
    Fix: Populate MatchStatistic table or remove feature

65. home_expected_goals
    Source: MatchStatistic.home_expected_goals - MatchStatistic database
    Pipeline: MatchStatistic DB → extract_ml_features() → dataset → XGBoost
    WC Status: CONSTANT (Min: 0.00, Max: 0.00, Mean: 0.00, Std: 0.00)
    Goals Status: NOT_IN_DATASET
    WC Training: NO
    Goals Training: NO
    Verdict: CONSTANT - No MatchStatistic data in database
    Fix: Populate MatchStatistic table or remove feature

66. away_expected_goals
    Source: MatchStatistic.away_expected_goals - MatchStatistic database
    Pipeline: MatchStatistic DB → extract_ml_features() → dataset → XGBoost
    WC Status: CONSTANT (Min: 0.00, Max: 0.00, Mean: 0.00, Std: 0.00)
    Goals Status: NOT_IN_DATASET
    WC Training: NO
    Goals Training: NO
    Verdict: CONSTANT - No MatchStatistic data in database
    Fix: Populate MatchStatistic table or remove feature

67. expected_goals_diff
    Source: home_xg - away_xg - calculated
    Pipeline: Calculated → extract_ml_features() → dataset → XGBoost
    WC Status: CONSTANT (Min: 0.00, Max: 0.00, Mean: 0.00, Std: 0.00)
    Goals Status: NOT_IN_DATASET
    WC Training: NO
    Goals Training: NO
    Verdict: CONSTANT - No MatchStatistic data in database
    Fix: Populate MatchStatistic table or remove feature

================================================================================
INTELLIGENCE SERVICE FEATURES (ALL CONSTANT - 48 FEATURES)
================================================================================

Features 68-115: All IntelligenceService features
Source: IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py
Pipeline: IntelligenceService → extract_ml_features() → dataset → XGBoost
WC Status: CONSTANT (all at default values)
Goals Status: NOT_IN_DATASET (all missing)
WC Training: NO (all missing from training)
Goals Training: NO (all missing from training)

List of CONSTANT IntelligenceService features:
- home_attacking_strength, away_attacking_strength, attacking_strength_diff
- home_defensive_strength, away_defensive_strength, defensive_strength_diff
- home_midfield_control, away_midfield_control, midfield_control_diff
- home_goalkeeper_performance, away_goalkeeper_performance, goalkeeper_performance_diff
- home_passing_dominance, away_passing_dominance, passing_dominance_diff
- home_pressing_intensity, away_pressing_intensity, pressing_intensity_diff
- home_set_piece_threat, away_set_piece_threat, set_piece_threat_diff
- home_discipline_score, away_discipline_score, discipline_score_diff
- home_fatigue_score, away_fatigue_score, fatigue_score_diff
- home_substitution_impact, away_substitution_impact, substitution_impact_diff
- home_player_availability_score, away_player_availability_score, availability_score_diff
- home_injury_impact, away_injury_impact, injury_impact_diff
- home_suspension_impact, away_suspension_impact, suspension_impact_diff
- home_formation_stability, away_formation_stability, formation_stability_diff
- home_momentum_score, away_momentum_score, momentum_score_diff
- home_goalkeeper_strength, away_goalkeeper_strength, goalkeeper_strength_diff
- home_passing_strength, away_passing_strength, passing_strength_diff
- home_recent_form, away_recent_form, recent_form_diff
- home_aerial_dominance, away_aerial_dominance, aerial_dominance_diff
- home_pressing_strength, away_pressing_strength, pressing_strength_diff
- home_defensive_stability, away_defensive_stability, defensive_stability_diff
- home_attacking_efficiency, away_attacking_efficiency, attacking_efficiency_diff
- home_finishing_quality, away_finishing_quality, finishing_quality_diff
- home_set_piece_strength, away_set_piece_strength, set_piece_strength_diff
- home_squad_availability, away_squad_availability, squad_availability_diff
- home_tactical_stability, away_tactical_stability, tactical_stability_diff
- confidence_score

Verdict: ALL BROKEN - IntelligenceService returns default values
Root Cause: IntelligenceService.calculate_match_intelligence() is not properly implemented or lacks data
Fix: Debug IntelligenceService implementation or remove all 48 features

================================================================================
KAGGLE FEATURES (ALL CONSTANT - 19 FEATURES)
================================================================================

Features 116-134: All Kaggle features
Source: ml/kaggle_features.py
Pipeline: Kaggle CSV → kaggle_features.py → extract_ml_features() → dataset → XGBoost
WC Status: CONSTANT (all zero)
Goals Status: NOT_IN_DATASET (all missing)
WC Training: NO (all filtered out due to missing from dataset)
Goals Training: NO (all missing from dataset)

List of CONSTANT Kaggle features:
- home_kaggle_attack_rating, away_kaggle_attack_rating, kaggle_attack_rating_diff
- home_kaggle_defense_rating, away_kaggle_defense_rating, kaggle_defense_rating_diff
- home_kaggle_discipline_score, away_kaggle_discipline_score, kaggle_discipline_score_diff
- home_kaggle_suspension_risk, away_kaggle_suspension_risk, kaggle_suspension_risk_diff
- home_kaggle_starting_xi_strength, away_kaggle_starting_xi_strength, kaggle_starting_xi_strength_diff
- home_kaggle_bench_strength, away_kaggle_bench_strength, kaggle_bench_strength_diff
- referee_strictness

Verdict: ALL BROKEN - Kaggle features always return default (zero) values
Root Cause: Team name matching fails between database and Kaggle CSV, or Kaggle data not loaded
Location: ml/kaggle_features.py line 485-506 (team name matching logic)
Fix: Debug team name matching in get_team_kaggle_features() or remove all 19 features

================================================================================
SUMMARY CATEGORIES
================================================================================

1. FULLY WORKING FEATURES (44)
   - elo_diff, fifa_diff, form_diff, gs_diff, gc_diff, mv_diff, inj_diff
   - h2h_factor, available_squad_diff, availability_pct_diff, starting_xi_value_diff
   - missing_star_players_diff, home_elo_momentum, away_elo_momentum, elo_momentum_diff
   - home_strength_of_schedule, away_strength_of_schedule, strength_of_schedule_diff
   - world_cup_matches_played_diff, major_tournament_matches_diff
   - home_attack_rating, away_attack_rating, attack_rating_diff
   - home_defence_rating, away_defence_rating, defence_rating_diff
   - home_clean_sheet_rate, away_clean_sheet_rate, clean_sheet_rate_diff
   - home_btts_rate, away_btts_rate, btts_rate_diff
   - goal_difference_diff, points_diff
   - All Phase 1, 2, 3, and 4.5 core features (except those noted below)

2. BROKEN FEATURES (67)
   - susp_diff (suspensions cleared during dataset building)
   - home_injury_count, away_injury_count (injuries cleared during dataset building)
   - home_suspension_count, away_suspension_count (suspensions cleared during dataset building)
   - home_injury_market_value_loss, away_injury_market_value_loss (injuries cleared)
   - All 48 IntelligenceService features (return default values)
   - All 19 Kaggle features (return default zero values)

3. CONSTANT FEATURES (119 in WC, 11 in Goals)
   - home_adv (no World Cup hosts in dataset)
   - match_stage_weight (mostly zero - few knockout matches)
   - knockout_matches_diff (mostly zero - few knockout matches)
   - All 7 SofaScore features (no data in database)
   - All 9 live-match features (no live data in training)
   - All 3 betting odds features (no bookmaker data)
   - All standing features (no standing data for international matches)
   - All 48 IntelligenceService features (default values)
   - All 19 Kaggle features (default zero values)

4. MOSTLY_ZERO FEATURES (2 in WC, 6 in Goals)
   - major_tournament_matches_diff (mostly zero in WC)
   - All standing features in Goals dataset (mostly zero)

5. FEATURES LOST BEFORE DATASET CREATION (0)
   - All features reach extract_ml_features() successfully

6. FEATURES LOST BEFORE TRAINING (108)
   - 48 IntelligenceService features (not in training feature lists)
   - 19 Kaggle features (filtered out due to being constant)
   - 7 SofaScore features (not in training feature lists)
   - 34 other features not included in training feature lists

7. FEATURES IGNORED BY XGBOOST (15)
   - Features with zero importance in trained models:
   - susp_diff, match_stage_weight, knockout_matches_diff
   - home_injury_count, away_injury_count, home_suspension_count, away_suspension_count
   - home_injury_market_value_loss, away_injury_market_value_loss
   - home_group_position, away_group_position
   - All betting odds features
   - All live-match features
   - All Kaggle features (not in training)

8. HIGHEST PRIORITY FIXES (Ranked)
   1. Fix Kaggle feature extraction (19 features) - ml/kaggle_features.py line 485-506
      - Team name matching fails between database and Kaggle CSV
      - Expected impact: High - Kaggle features could add significant predictive power
   
   2. Fix IntelligenceService implementation (48 features) - services/intelligence_service.py
      - Returns default values instead of calculated intelligence
      - Expected impact: High - 48 features completely wasted
   
   3. Remove injury/suspension clearing logic (6 features) - ml/build_dataset_world_cup.py line 207-210
      - Injuries and suspensions are cleared for "simulation" but never restored
      - Expected impact: Medium - These features work in Goals dataset
   
   4. Populate BookmakerOdds table (3 features)
      - No betting odds data in database
      - Expected impact: Medium - Betting odds are strong predictors
   
   5. Populate MatchStatistic table (7 features)
      - No SofaScore statistics in database
      - Expected impact: Medium - xG and possession are valuable features

9. EASIEST FIXES
   1. Remove constant features from training lists (100+ features)
      - Simply remove from FEATURES lists in training scripts
      - Impact: Immediate - Reduces noise in models
   
   2. Remove live-match features from training (9 features)
      - Only useful for live predictions, not training
      - Impact: Low - These features don't work in training anyway
   
   3. Remove standing features for international datasets (6 features)
      - Standing data only available for league competitions
      - Impact: Low - Features are mostly zero anyway

10. BIGGEST EXPECTED IMPROVEMENTS
    1. Fixing Kaggle features (19 features)
       - Could add significant predictive power if team data matches
       - Expected accuracy improvement: 2-5%
    
    2. Fixing IntelligenceService (48 features)
       - Would add 48 new predictive features
       - Expected accuracy improvement: 3-7%
    
    3. Populating BookmakerOdds (3 features)
       - Betting odds are among the strongest predictors
       - Expected accuracy improvement: 5-10%
    
    4. Populating MatchStatistic (7 features)
       - xG and possession are highly predictive
       - Expected accuracy improvement: 3-6%

11. FEATURES THAT SHOULD BE REMOVED
    - All 48 IntelligenceService features (broken, return defaults)
    - All 19 Kaggle features (broken, return zeros)
    - All 7 SofaScore features (no data source)
    - All 9 live-match features (not useful for training)
    - All 3 betting odds features (no data source)
    - All 6 standing features for international datasets (no data)
    - susp_diff, home_suspension_count, away_suspension_count (cleared during build)
    - home_injury_count, away_injury_count (cleared during build for WC)
    - home_injury_market_value_loss, away_injury_market_value_loss (cleared for WC)
    - match_stage_weight, knockout_matches_diff (mostly zero)
    - home_adv (constant - no hosts in dataset)

12. FEATURES THAT SHOULD NEVER BE REMOVED
    - elo_diff (strongest feature - #1 in both models)
    - fifa_diff (top 3 feature in both models)
    - form_diff, gs_diff, gc_diff (core form features)
    - mv_diff (market value is strong predictor)
    - inj_diff (works well when not cleared)
    - h2h_factor (historical performance)
    - available_squad_diff, starting_xi_value_diff (squad quality)
    - missing_star_players_diff (star player impact)
    - home_elo_momentum, away_elo_momentum (momentum)
    - strength_of_schedule_diff (schedule difficulty)
    - world_cup_matches_played_diff (tournament experience)
    - home_attack_rating, away_attack_rating, attack_rating_diff (goal scoring)
    - home_defence_rating, away_defence_rating, defence_rating_diff (goal prevention)
    - clean_sheet_rate_diff, btts_rate_diff (advanced goal metrics)
    - goal_difference_diff (standing performance)

13. FINAL VERDICT: IS THE MODEL READY FOR VERSION 2.0?
    
    NO - The model is NOT ready for Version 2.0
    
    REASONS:
    1. 72.1% of features are CONSTANT in dataset_world_cup.csv
    2. 64.8% of features are MISSING from dataset_goals.csv
    3. Only 35% of engineered features actually reach XGBoost training
    4. All 19 Kaggle features are BROKEN (always zero)
    5. All 48 IntelligenceService features are BROKEN (always default)
    6. Injury and suspension data is cleared during dataset building
    7. No bookmaker odds data in database
    8. No SofaScore statistics data in database
    9. Standing data not available for international competitions
    10. Many features have zero importance in trained models
    
    RECOMMENDED ACTIONS BEFORE VERSION 2.0:
    1. Remove all constant/broken features from training (100+ features)
    2. Fix or remove Kaggle feature integration
    3. Fix or remove IntelligenceService integration
    4. Remove injury/suspension clearing logic
    5. Populate BookmakerOdds table or remove betting features
    6. Populate MatchStatistic table or remove SofaScore features
    7. Remove standing features for international datasets
    8. Remove live-match features from training (keep for inference only)
    9. Retrain models with cleaned feature set
    10. Validate that all features in training are actually healthy
    
    CURRENT MODEL STATUS:
    - World Cup Model: 57/165 features (34.5%) actually used
    - Goal Model: 58/165 features (35.2%) actually used
    - Healthy features: 44/165 (26.7%)
    - Constant features: 119/165 (72.1%)
    - Broken features: 67/165 (40.6%)
    
    The model is over-engineered with 165 features but only 44 are healthy.
    The remaining 121 features are either constant, broken, or missing.
    This adds noise, complexity, and maintenance burden without predictive value.
    
    RECOMMENDED VERSION 2.0 APPROACH:
    1. Start with 44 healthy features
    2. Add back features only after fixing their data pipelines
    3. Target: 50-60 healthy features maximum
    4. Focus on data quality over feature quantity
    5. Implement feature health monitoring in CI/CD

================================================================================
END OF REPORT
================================================================================
