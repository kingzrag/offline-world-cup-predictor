# Betting Market Models Report

Generated: 2026-06-26T20:04:48.796480Z

## Dataset Summary

- Total matches: **20,493**
- Train/Val/Test split: **14,345 / 3,074 / 3,074**
- Features used: **146**
- Date range: **1958-06-24T00:00:00** → **2026-06-25T01:00:00**

## Asian Handicap

- **Outperforms baseline:** ✅ Yes
- **Baseline accuracy:** 0.5286
- **Baseline log loss:** 0.6931
- **Test accuracy:** 0.7251
- **Test log loss:** 0.5477
- **Test F1 (weighted):** 0.7253
- **Test Brier score:** 0.1838

### Performance Comparison

| Metric | Baseline | Model | Improvement |
|---|---:|---:|---:|
| Accuracy | 0.5286 | 0.7251 | +0.1965 |
| Log Loss | 0.6931 | 0.5477 | +0.1455 |

### Top Feature Importance

| Rank | Feature | Importance |
|---|---|---:|
| 1 | `elo_diff` | 0.066639 |
| 2 | `fifa_diff` | 0.035911 |
| 3 | `starting_xi_value_diff` | 0.015858 |
| 4 | `away_points` | 0.014950 |
| 5 | `defence_rating_diff` | 0.014712 |
| 6 | `away_suspension_count` | 0.012501 |
| 7 | `major_tournament_matches_diff` | 0.012415 |
| 8 | `elo_momentum_diff` | 0.012160 |
| 9 | `availability_pct_diff` | 0.012021 |
| 10 | `attack_rating_diff` | 0.011649 |
| 11 | `home_finishing_quality` | 0.011539 |
| 12 | `home_attacking_strength` | 0.011444 |
| 13 | `world_cup_matches_played_diff` | 0.011217 |
| 14 | `fatigue_score_diff` | 0.011055 |
| 15 | `away_player_availability_score` | 0.010593 |
| 16 | `away_midfield_control` | 0.010586 |
| 17 | `away_squad_availability` | 0.010534 |
| 18 | `away_attack_rating` | 0.010472 |
| 19 | `h2h_factor` | 0.010379 |
| 20 | `away_defence_rating` | 0.010303 |

### Calibration

- **Brier score (test):** 0.1838

## Asian Total

- **Outperforms baseline:** ❌ No
- **Baseline accuracy:** 0.5016
- **Baseline log loss:** 0.6931
- **Test accuracy:** 0.5452
- **Test log loss:** 0.6949
- **Test F1 (weighted):** 0.5450
- **Test Brier score:** 0.2496

### Performance Comparison

| Metric | Baseline | Model | Improvement |
|---|---:|---:|---:|
| Accuracy | 0.5016 | 0.5452 | +0.0436 |
| Log Loss | 0.6931 | 0.6949 | -0.0017 |

### Top Feature Importance

| Rank | Feature | Importance |
|---|---|---:|
| 1 | `home_suspension_count` | 0.027975 |
| 2 | `away_attacking_strength` | 0.016637 |
| 3 | `home_injury_count` | 0.015395 |
| 4 | `elo_diff` | 0.014887 |
| 5 | `away_possession` | 0.013565 |
| 6 | `home_attacking_strength` | 0.013335 |
| 7 | `away_defence_rating` | 0.013112 |
| 8 | `availability_pct_diff` | 0.012861 |
| 9 | `passing_dominance_diff` | 0.012683 |
| 10 | `home_adv` | 0.012617 |
| 11 | `home_squad_availability` | 0.012445 |
| 12 | `fifa_diff` | 0.012390 |
| 13 | `home_possession` | 0.011993 |
| 14 | `away_group_position` | 0.011493 |
| 15 | `away_defensive_stability` | 0.011487 |
| 16 | `away_pressing_intensity` | 0.011250 |
| 17 | `fatigue_score_diff` | 0.010871 |
| 18 | `defence_rating_diff` | 0.010764 |
| 19 | `home_defence_rating` | 0.010687 |
| 20 | `available_squad_diff` | 0.010670 |

### Calibration

- **Brier score (test):** 0.2496

## Btts

- **Outperforms baseline:** ❌ No
- **Baseline accuracy:** 0.5716
- **Baseline log loss:** 0.6931
- **Test accuracy:** 0.5355
- **Test log loss:** 0.7145
- **Test F1 (weighted):** 0.5345
- **Test Brier score:** 0.2583

### Performance Comparison

| Metric | Baseline | Model | Improvement |
|---|---:|---:|---:|
| Accuracy | 0.5716 | 0.5355 | -0.0361 |
| Log Loss | 0.6931 | 0.7145 | -0.0213 |

### Top Feature Importance

| Rank | Feature | Importance |
|---|---|---:|
| 1 | `away_injury_market_value_loss` | 0.030773 |
| 2 | `away_pressing_strength` | 0.017909 |
| 3 | `home_adv` | 0.015516 |
| 4 | `home_suspension_impact` | 0.015460 |
| 5 | `elo_diff` | 0.014877 |
| 6 | `away_pressing_intensity` | 0.013667 |
| 7 | `fifa_diff` | 0.013360 |
| 8 | `home_squad_availability` | 0.013035 |
| 9 | `away_squad_availability` | 0.012980 |
| 10 | `away_possession` | 0.012974 |
| 11 | `away_expected_goals` | 0.012696 |
| 12 | `home_player_availability_score` | 0.011373 |
| 13 | `away_passing_strength` | 0.011310 |
| 14 | `availability_score_diff` | 0.011149 |
| 15 | `away_btts_rate` | 0.010998 |
| 16 | `fatigue_score_diff` | 0.010883 |
| 17 | `defence_rating_diff` | 0.010663 |
| 18 | `world_cup_matches_played_diff` | 0.010594 |
| 19 | `squad_availability_diff` | 0.010519 |
| 20 | `mv_diff` | 0.010449 |

### Calibration

- **Brier score (test):** 0.2583

## Clean Sheet

- **Outperforms baseline:** ✅ Yes
- **Baseline accuracy:** 0.6113
- **Baseline log loss:** 0.6931
- **Test accuracy:** 0.6259
- **Test log loss:** 0.6448
- **Test F1 (weighted):** 0.6295
- **Test Brier score:** 0.2259

### Performance Comparison

| Metric | Baseline | Model | Improvement |
|---|---:|---:|---:|
| Accuracy | 0.6113 | 0.6259 | +0.0146 |
| Log Loss | 0.6931 | 0.6448 | +0.0483 |

### Top Feature Importance

| Rank | Feature | Importance |
|---|---|---:|
| 1 | `elo_diff` | 0.037127 |
| 2 | `fifa_diff` | 0.024581 |
| 3 | `away_passing_strength` | 0.017819 |
| 4 | `home_formation_stability` | 0.017115 |
| 5 | `away_midfield_control` | 0.016898 |
| 6 | `home_midfield_control` | 0.013738 |
| 7 | `defence_rating_diff` | 0.013258 |
| 8 | `home_passing_strength` | 0.013053 |
| 9 | `away_pressing_intensity` | 0.012863 |
| 10 | `starting_xi_value_diff` | 0.012551 |
| 11 | `away_squad_availability` | 0.012185 |
| 12 | `away_attack_rating` | 0.011983 |
| 13 | `availability_score_diff` | 0.011737 |
| 14 | `away_expected_goals` | 0.011723 |
| 15 | `away_injury_count` | 0.011479 |
| 16 | `home_group_position` | 0.011322 |
| 17 | `world_cup_matches_played_diff` | 0.011177 |
| 18 | `away_injury_market_value_loss` | 0.011089 |
| 19 | `home_defence_rating` | 0.011063 |
| 20 | `major_tournament_matches_diff` | 0.010871 |

### Calibration

- **Brier score (test):** 0.2259

## Correct Score

- **Outperforms baseline:** ❌ No
- **Baseline accuracy:** 0.2658
- **Baseline log loss:** 2.4849
- **Test accuracy:** 0.1779
- **Test log loss:** 2.2891
- **Test F1 (weighted):** 0.1784
- **Test Brier score:** N/A (multiclass)

### Performance Comparison

| Metric | Baseline | Model | Improvement |
|---|---:|---:|---:|
| Accuracy | 0.2658 | 0.1779 | -0.0878 |
| Log Loss | 2.4849 | 2.2891 | +0.1958 |

### Top Feature Importance

| Rank | Feature | Importance |
|---|---|---:|
| 1 | `home_expected_goals` | 0.021203 |
| 2 | `elo_diff` | 0.020242 |
| 3 | `home_passing_strength` | 0.018678 |
| 4 | `home_possession` | 0.015724 |
| 5 | `home_passing_dominance` | 0.015668 |
| 6 | `fifa_diff` | 0.013609 |
| 7 | `home_group_position` | 0.012627 |
| 8 | `away_passing_dominance` | 0.012623 |
| 9 | `expected_goals_diff` | 0.012508 |
| 10 | `away_expected_goals` | 0.012346 |
| 11 | `tactical_stability_diff` | 0.011858 |
| 12 | `away_midfield_control` | 0.011582 |
| 13 | `away_possession` | 0.011007 |
| 14 | `defence_rating_diff` | 0.010833 |
| 15 | `away_group_position` | 0.010697 |
| 16 | `away_player_availability_score` | 0.010486 |
| 17 | `group_position_diff` | 0.010302 |
| 18 | `midfield_control_diff` | 0.010225 |
| 19 | `available_squad_diff` | 0.009884 |
| 20 | `availability_pct_diff` | 0.009851 |

### Calibration

- **Brier score (test):** N/A (multiclass)

## Summary

| Market | Outperforms Baseline | Test Accuracy | Test Log Loss |
|---|---|---:|---:|
| asian_handicap | ✅ | 0.7251 | 0.5477 |
| asian_total | ❌ | 0.5452 | 0.6949 |
| btts | ❌ | 0.5355 | 0.7145 |
| clean_sheet | ✅ | 0.6259 | 0.6448 |
| correct_score | ❌ | 0.1779 | 2.2891 |
