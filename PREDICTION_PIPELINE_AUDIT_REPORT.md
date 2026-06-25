# Prediction Pipeline Audit Report

**Date Generated:** 2026-06-25  
**Audit Scope:** Full prediction pipeline - FOOTBALL_DATA_API_KEY & ODDS_API_KEY usage

---

## 1. Executive Summary

This audit examines the entire prediction pipeline to determine if data from:
- **Football-Data.org** (via `FOOTBALL_DATA_API_KEY`)
- **The Odds API** (via `ODDS_API_KEY`)

is being properly collected, stored, and used in feature extraction and model predictions.

---

## 2. Data Collection & Storage Overview

### 2.1 API Keys Configuration
- `FOOTBALL_DATA_API_KEY`: Stored in `utils/config.py` and used in `collectors/football_data.py`
- `ODDS_API_KEY`: Stored in `utils/config.py` and used in `services/odds_service.py`

### 2.2 Data Flow
```
External APIs → Database Tables → Feature Extraction → Model Prediction
```

---

## 3. Detailed Audit: Football-Data.org (FOOTBALL_DATA_API_KEY)

### 3.1 Live Score
| Question | Answer | Details |
|------------|--------|---------|
| API Endpoint Used | `/competitions/{code}/matches` | `FootballDataCollector.fetch_matches()` |
| Database Table Used | `matches` | Stored in `home_score`, `away_score`, `status` columns |
| Stored in Database | ✅ YES | `Match.home_score, Match.away_score, Match.status |
| Used in Feature Generation | ✅ YES | `extract_ml_features() uses historical match scores for: form, goals scored/conceded, head-to-head, etc. |
| Used by Prediction Model | ✅ YES | Used as target variables for training (home_score, away_score) |

### 3.2 Match Minute
| Question | Answer | Details |
|------------|--------|---------|
| API Endpoint Used | `/competitions/{code}/matches` | `FootballDataCollector.fetch_matches()` |
| Database Table Used | `matches` | Stored in `live_minute` column |
| Stored in Database | ✅ YES | `Match.live_minute` |
| Used in Feature Generation | ❌ NO | `extract_ml_features()` does NOT reference `live_minute` |
| Used by Prediction Model | ❌ NO | Not included in any model features |

### 3.3 Red Cards
| Question | Answer | Details |
|------------|--------|---------|
| API Endpoint Used | ❌ NO | Football-Data.org API does NOT collect red cards (no endpoint in `matches` |
| Database Table Used | ❌ NO | No table for red cards in models |
| Stored in Database | ❌ NO | Not collected/stored |
| Used in Feature Generation | ❌ NO | Not available |
| Used by Prediction Model | ❌ NO | Not available |

### 3.4 Group Standings
| Question | Answer | Details |
|------------|--------|---------|
| API Endpoint Used | `/competitions/{code}/standings` | `FootballDataCollector.fetch_standings()` |
| Database Table Used | `standings` | `Standing` model with all standings data |
| Stored in Database | ✅ YES | `Standing` table: position, played_games, won, draw, lost, points, goals_for, goals_against, goals_difference |
| Used in Feature Generation | ❌ NO | `extract_ml_features()` does NOT reference `Standing` |
| Used by Prediction Model | ❌ NO | Not included in any model features |

---

## 4. Detailed Audit: The Odds API (ODDS_API_KEY)

### 4.1 Betting Odds
| Question | Answer | Details |
|------------|--------|---------|
| API Endpoint Used | `/sports/{sport_key}/odds` | `OddsService.fetch_upcoming_odds()` |
| Database Table Used | `bookmaker_odds` | `BookmakerOdds` model |
| Stored in Database | ✅ YES | `bookmaker_odds` table: home_odds, draw_odds, away_odds |
| Used in Feature Generation | ❌ NO | `extract_ml_features()` does NOT reference `BookmakerOdds` |
| Used by Prediction Model | ❌ NO | Not included in any model features |

---

## 5. Feature Extraction Analysis (`extract_ml_features`)

### 5.1 Features Currently Used
The `extract_ml_features()` function in `ml/features.py` generates **only uses these sources:

| Source | Data |
|--------|------|
| **Football-Data.org** | Historical match results (home_score, away_score) |
| **Elo Ratings** | Precomputed team Elo scores |
| **FIFA Rankings** | Team FIFA rankings |
| **Injuries** | Injury data from Transfermarkt |
| **Suspensions** | Suspension data from Transfermarkt |
| **Squad Values** | Team market value data |

### 5.2 NOT used by Models
**Goal Prediction Model (`train_goal_model.py`) uses these features:
```python
GOAL_FEATURES = [
    "elo_diff", "fifa_diff", "form_diff", "gs_diff", "gc_diff", "inj_diff", "susp_diff",
    "available_squad_diff", "starting_xi_value_diff", "missing_star_players_diff",
    "elo_momentum_diff", "strength_of_schedule_diff", "home_adv", "h2h_factor",
    "match_stage_weight", "home_attack_rating", "away_attack_rating", "attack_rating_diff",
    "home_defence_rating", "away_defence_rating", "defence_rating_diff",
    "home_clean_sheet_rate", "away_clean_sheet_rate", "clean_sheet_rate_diff",
    "home_btts_rate", "away_btts_rate", "btts_rate_diff"
]
```
**NOT included: live_minute, red cards, group standings, betting odds!

---

## 6. Categorized Summary

### ✅ **USED** (Used in both feature generation and models)
- **Live Scores** (historical) → historical match scores are used extensively for:
  - form_diff
  - gs_diff (goals scored diff)
  - gc_diff (goals conceded diff)
  - home_attack_rating
  - home_defence_rating
  - clean_sheet_rate
  - btts_rate
  - h2h_factor

### 📥 **COLLECTED BUT NOT USED** (Collected and stored, NOT used in features/models)
1. **Match Minute** (`Match.live_minute`)
   - Collected from Football-Data.org API
   - Stored in database
   - NOT used by features/model
2. **Group Standings** (`Standing` table)
   - Collected from Football-Data.org API
   - Stored in database
   - NOT used by features/model
3. **Betting Odds** (`BookmakerOdds` table)
   - Collected from The Odds API
   - Stored in database
   - NOT used by features/model

### ❌ **NOT COLLECTED**
1. **Red Cards**
   - NOT collected from any API
   - NOT stored in database
   - NOT used by features/model

---

## 7. Recommendation

1. **Consider using collected data** for better predictions:
   - **Betting odds (great feature for model calibration
   - Group standings (especially for tournament context
   - Live minute (for in-play predictions)

2. **Red cards would be nice to have but requires different API integration

---

## 8. Files Examined
- `utils/config.py`
- `collectors/football_data.py`
- `services/odds_service.py`
- `services/collection_service.py`
- `ml/features.py`
- `ml/train_goal_model.py`
- `ml/build_goal_dataset.py`
- `models/match.py`
- `models/standing.py`
- `models/bookmaker_odds.py`

