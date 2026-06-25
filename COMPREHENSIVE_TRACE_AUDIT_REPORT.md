
# GERMANY vs ECUADOR - END-TO-END PREDICTION TRACE AUDIT REPORT
## Date: 2026-06-25

---

## 1. FEATURE GENERATION
Features are extracted from `ml/features.py` → `extract_ml_features()`.
Data sources:
- **Matches table:** for results, goals, dates
- **Team Elo table:** for Elo ratings and momentum
- **Team table:** FIFA rankings, squad market values
- **Injuries/Suspensions tables:** for player availability (via market value impact)

### All Extracted Features (Germany vs Ecuador):
| Feature | Value |
|---------|-------|
| attack_rating_diff | 2.2285714285714286 |
| availability_pct_diff | 0.0 |
| available_squad_diff | 211.44999999999982 |
| away_attack_rating | 0.8571428571428571 |
| away_btts_rate | 0.3 |
| away_clean_sheet_rate | 0.65 |
| away_defence_rating | 0.4857142857142857 |
| away_elo_momentum | 18.372516412375667 |
| away_injury_count | 0 |
| away_injury_market_value_loss | 0 |
| away_strength_of_schedule | 1826.4 |
| away_suspension_count | 0 |
| btts_rate_diff | 0.25000000000000006 |
| clean_sheet_rate_diff | -0.30000000000000004 |
| defence_rating_diff | 0.4857142857142857 |
| elo_diff | 123 |
| elo_momentum_diff | 6.8733841806115095 |
| fifa_diff | 9 |
| form_diff | 1.8 |
| gc_diff | 0.3999999999999999 |
| gs_diff | 3.0 |
| h2h_factor | 1.0 |
| home_adv | 0 |
| home_attack_rating | 3.085714285714286 |
| home_btts_rate | 0.55 |
| home_clean_sheet_rate | 0.35 |
| home_defence_rating | 0.9714285714285714 |
| home_elo_momentum | 25.245900592987176 |
| home_injury_count | 0 |
| home_injury_market_value_loss | 0 |
| home_strength_of_schedule | 1691.4 |
| home_suspension_count | 0 |
| inj_diff | 0 |
| knockout_matches_diff | 0 |
| major_tournament_matches_diff | 59 |
| match_stage_weight | 0 |
| missing_star_players_diff | 0 |
| mv_diff | 211.44999999999982 |
| starting_xi_value_diff | 55.24000000000001 |
| strength_of_schedule_diff | -135.0 |
| susp_diff | 0 |
| world_cup_matches_played_diff | -47 |

---

## 2. WORLD CUP MODEL INPUT VECTOR
Features in order as used by the model:
1. elo_diff: 123
2. fifa_diff: 9
3. form_diff: 1.8
4. gs_diff: 3.0
5. gc_diff: 0.3999999999999999
6. inj_diff: 0
7. susp_diff: 0
8. home_adv: 0
9. h2h_factor: 1.0
10. available_squad_diff: 211.44999999999982
11. starting_xi_value_diff: 55.24000000000001
12. missing_star_players_diff: 0
13. match_stage_weight: 0
14. elo_momentum_diff: 6.8733841806115095
15. home_elo_momentum: 25.245900592987176
16. away_elo_momentum: 18.372516412375667
17. strength_of_schedule_diff: -135.0
18. home_strength_of_schedule: 1691.4
19. away_strength_of_schedule: 1826.4
20. world_cup_matches_played_diff: -47
21. major_tournament_matches_diff: 59
22. knockout_matches_diff: 0
23. home_injury_count: 0
24. away_injury_count: 0
25. home_suspension_count: 0
26. away_suspension_count: 0
27. home_injury_market_value_loss: 0
28. away_injury_market_value_loss: 0

---

## 3. RAW MODEL PREDICTIONS
No calibration applied yet!
| Outcome | Raw Probability | Raw % |
|---------|-----------------|-------|
| Home Win | 0.79669833 | 79.6698% |
| Draw | 0.17802897 | 17.8029% |
| Away Win | 0.02527265 | 2.5273% |

---

## 4. API RESPONSE PROBABILITIES
Transformation: Raw probs rounded to 4 decimal places (code: `services/model_service.py` lines 137‑139)
| Outcome | Rounded Probability | Rounded % |
|---------|---------------------|-----------|
| Home Win | 0.7967 | 79.67% |
| Draw | 0.1780 | 17.80% |
| Away Win | 0.0253 | 2.53% |

---

## 5. FRONTEND MAPPING & DISPLAY
Transformation: Multiply by 100 to convert 0‑1 → %
| Outcome | Displayed % |
|---------|-------------|
| Home Win | 79.67% |
| Draw | 17.80% |
| Away Win | 2.53% |

---

## 6. SUMMARY OF PROBABILITY CHANGES
| Step | Change | Location |
|------|--------|----------|
| 1 | Raw model probs → Rounded to 4 decimals | `services/model_service.py` lines 137‑139 |
| 2 | 0‑1 decimal → 0‑100% | Frontend multiplication by 100 |
| NO OTHER CALIBRATION/NORMALIZATION APPLIED! |

---

## 7. LIVE TOURNAMENT DATA IMPACT
**YES!** 2026 World Cup matches that are marked `FINISHED` are included in all recent‑match features!
- Features that change during tournament:
  - form_diff, gs_diff, gc_diff
  - elo_momentum_diff, strength_of_schedule_diff
  - attack_rating_diff, defence_rating_diff
  - clean_sheet_rate_diff, btts_rate_diff
- Data source: `matches` table (status = 'FINISHED')
- No live standings or betting odds used!
- No cached features — recalculated on every prediction!

---

## 8. GOAL MODEL PREDICTIONS (Germany vs Ecuador)
- Raw xG Home: 1.93974495
- Raw xG Away: 0.70547318
- Rounded xG Home: 1.9397
- Rounded xG Away: 0.7055

---

## 9. BONUS: OTHER MATCH AUDITS
### Bosnia and Herzegovina vs Qatar
- Raw: Home 0.3005, Draw 0.2129, Away 0.4867 → Display: 30.05%, 21.29%, 48.67%
### Scotland vs Brazil
- Raw: Home 0.1703, Draw 0.2543, Away 0.5754 → Display: 17.03%, 25.43%, 57.54%
