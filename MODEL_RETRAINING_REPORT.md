# Model Retraining Report

Generated: 2026-06-26T15:04:05.370655Z

## Dataset Summary

- Matches used: **20,493**
- Features used: **146**
- Dataset path: `/Users/anuragsaikia/prediction/ml/dataset_international_retrain.csv`
- Date range: **1958-06-24T00:00:00** → **2026-06-25T01:00:00**
- International competition codes: `AFCON, AFCONQ, ASIAN, ASIANQ, CA, CNL, EC, EU, EUQ, FRI, OLY, UNL, WC, WCQ, WCQA, WCQC, WCQE, WWC`
- Train / Validation / Test rows: **14,345 / 3,074 / 3,074**

## World Cup Predictor (1X2)

- Selected candidate: `wc_all_features_146__xgb_classifier_balanced_b`
- Selected feature subset: `wc_all_features_146`
- Current deployed feature count: **57**
- Selected new feature count: **146**
- Saved versioned model: **No**
- Output path: `/Users/anuragsaikia/prediction/models/world_cup_predictor_v2.pkl`

### New model metrics

| Split | Accuracy | Log Loss | F1 Macro | F1 Weighted |
|---|---:|---:|---:|---:|
| Validation | 0.5719 | 0.9011 | 0.5216 | 0.5715 |
| Test | 0.5729 | 0.8772 | 0.5115 | 0.5634 |

### Current deployed model metrics

| Split | Accuracy | Log Loss | F1 Macro | F1 Weighted |
|---|---:|---:|---:|---:|
| Validation | 0.6418 | 0.8793 | 0.5656 | 0.6182 |
| Test | 0.6474 | 0.8491 | 0.5646 | 0.6162 |

#### Top Feature Importance

| Rank | Feature | Importance |
|---|---|---:|
| 1 | `elo_diff` | 0.056964 |
| 2 | `fifa_diff` | 0.023457 |
| 3 | `defence_rating_diff` | 0.015241 |
| 4 | `away_midfield_control` | 0.013286 |
| 5 | `starting_xi_value_diff` | 0.013026 |
| 6 | `away_passing_strength` | 0.012416 |
| 7 | `home_points` | 0.012402 |
| 8 | `away_formation_stability` | 0.012259 |
| 9 | `home_adv` | 0.011686 |
| 10 | `major_tournament_matches_diff` | 0.011552 |
| 11 | `home_defence_rating` | 0.011507 |
| 12 | `elo_momentum_diff` | 0.011156 |
| 13 | `world_cup_matches_played_diff` | 0.010786 |
| 14 | `tactical_stability_diff` | 0.010720 |
| 15 | `away_pressing_intensity` | 0.010552 |
| 16 | `away_injury_count` | 0.010356 |
| 17 | `away_finishing_quality` | 0.010112 |
| 18 | `strength_of_schedule_diff` | 0.009970 |
| 19 | `attack_rating_diff` | 0.009918 |
| 20 | `away_points` | 0.009914 |
| 21 | `home_elo_momentum` | 0.009905 |
| 22 | `away_defence_rating` | 0.009892 |
| 23 | `away_attack_rating` | 0.009867 |
| 24 | `formation_stability_diff` | 0.009817 |
| 25 | `home_injury_market_value_loss` | 0.009643 |

## Goal Predictor

- Selected candidate: `goal_all_features_146__xgb_goal_poisson_a`
- Selected feature subset: `goal_all_features_146`
- Current deployed feature count: **58**
- Selected new feature count: **146**
- Saved versioned model: **No**
- Output path: `/Users/anuragsaikia/prediction/models/goal_predictor_v2.pkl`

### New goal model metrics

| Split | Home MAE | Home RMSE | Away MAE | Away RMSE | Avg MAE | Avg RMSE |
|---|---:|---:|---:|---:|---:|---:|
| Validation | 1.0019 | 1.3570 | 0.8131 | 1.0886 | 0.9075 | 1.2228 |
| Test | 1.0202 | 1.3528 | 0.8291 | 1.1010 | 0.9246 | 1.2269 |

### Current deployed goal model metrics

| Split | Home MAE | Home RMSE | Away MAE | Away RMSE | Avg MAE | Avg RMSE |
|---|---:|---:|---:|---:|---:|---:|
| Validation | 1.0060 | 1.3769 | 0.8133 | 1.1020 | 0.9096 | 1.2394 |
| Test | 0.9726 | 1.3147 | 0.8126 | 1.0820 | 0.8926 | 1.1984 |

#### Home Goal Model Feature Importance

| Rank | Feature | Importance |
|---|---|---:|
| 1 | `elo_diff` | 0.067691 |
| 2 | `fifa_diff` | 0.056832 |
| 3 | `defence_rating_diff` | 0.049204 |
| 4 | `away_defence_rating` | 0.035356 |
| 5 | `starting_xi_value_diff` | 0.024892 |
| 6 | `away_goalkeeper_strength` | 0.021355 |
| 7 | `gc_diff` | 0.017570 |
| 8 | `away_strength_of_schedule` | 0.013962 |
| 9 | `major_tournament_matches_diff` | 0.013925 |
| 10 | `attack_rating_diff` | 0.013701 |
| 11 | `away_clean_sheet_rate` | 0.012781 |
| 12 | `elo_momentum_diff` | 0.012487 |
| 13 | `away_btts_rate` | 0.012248 |
| 14 | `strength_of_schedule_diff` | 0.012146 |
| 15 | `home_attack_rating` | 0.010880 |
| 16 | `world_cup_matches_played_diff` | 0.010026 |
| 17 | `home_formation_stability` | 0.009891 |
| 18 | `confidence_score` | 0.009798 |
| 19 | `away_defensive_stability` | 0.009573 |
| 20 | `defensive_strength_diff` | 0.009461 |
| 21 | `away_points` | 0.009386 |
| 22 | `pressing_strength_diff` | 0.009384 |
| 23 | `home_defence_rating` | 0.009355 |
| 24 | `away_attack_rating` | 0.009229 |
| 25 | `fatigue_score_diff` | 0.009205 |

#### Away Goal Model Feature Importance

| Rank | Feature | Importance |
|---|---|---:|
| 1 | `elo_diff` | 0.053696 |
| 2 | `fifa_diff` | 0.044921 |
| 3 | `home_defence_rating` | 0.037273 |
| 4 | `defence_rating_diff` | 0.033965 |
| 5 | `availability_pct_diff` | 0.022068 |
| 6 | `starting_xi_value_diff` | 0.018102 |
| 7 | `away_attack_rating` | 0.014913 |
| 8 | `attack_rating_diff` | 0.013531 |
| 9 | `goal_difference_diff` | 0.012970 |
| 10 | `major_tournament_matches_diff` | 0.012722 |
| 11 | `world_cup_matches_played_diff` | 0.012654 |
| 12 | `elo_momentum_diff` | 0.011868 |
| 13 | `away_aerial_dominance` | 0.011625 |
| 14 | `home_defensive_strength` | 0.011585 |
| 15 | `inj_diff` | 0.011208 |
| 16 | `away_squad_availability` | 0.011200 |
| 17 | `away_attacking_strength` | 0.011155 |
| 18 | `away_passing_strength` | 0.010810 |
| 19 | `availability_score_diff` | 0.010769 |
| 20 | `away_player_availability_score` | 0.010393 |
| 21 | `away_btts_rate` | 0.010320 |
| 22 | `mv_diff` | 0.010138 |
| 23 | `away_suspension_count` | 0.010054 |
| 24 | `home_group_position` | 0.009950 |
| 25 | `home_injury_market_value_loss` | 0.009903 |

## Comparison Summary

- 1X2 deployed test accuracy/log loss/f1_macro: **0.6474 / 0.8491 / 0.5646**
- 1X2 new test accuracy/log loss/f1_macro: **0.5729 / 0.8772 / 0.5115**
- Goal deployed avg test MAE/RMSE: **0.8926 / 1.1984**
- Goal new avg test MAE/RMSE: **0.9246 / 1.2269**

## Reproducibility

- Dataset is rebuilt from PostgreSQL using `extract_ml_features()` and historical FINISHED international matches only.
- Splits are deterministic chronological splits (70/15/15).
- XGBoost random state is fixed at `42`.
- Retrain command: `python3 ml/retrain_international_models.py --force-rebuild`
