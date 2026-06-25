# API-Football Integration Full Audit

Date: 2026-06-25

---

## 1. Verification of Audit Points

### 1.1 Is `collectors/api_football.py` actually called anywhere in the application?

**Answer:** ❌ No

**Explanation:**
- The `APIFootballCollector` is only present in the `collectors/api_football.py` file
- It is NOT imported or used anywhere in the application:
  - `services/collection_service.py` only imports `FootballDataCollector`
  - No other files reference `api_football` or `APIFootballCollector` (except the summary we created)

---

### 1.2 Is live data being fetched from API-Football?

**Answer:** ❌ No

**Explanation:**
- All current live data fetching is from football-data.org, via `services/collection_service.py`'s `ingest_matches` method
- There are no calls to APIFootballCollector.fetch_live_matches or fetch_fixture_events

---

### 1.3 Are `current_minute`, `home_red_cards`, `away_red_cards`, and `api_football_id` being populated in the database?

**Answer:** ❌ No

**Explanation:**
- The fields exist in the database schema (migration applied successfully)
- BUT, no code actually updates/populates them! Current values are:
  - `api_football_id`: None
  - `current_minute`: None
  - `home_red_cards`: 0 (default, not updated)
  - `away_red_cards`: 0 (default, not updated)

---

### 1.4 Is any scheduler, cron job, startup task, or collection service invoking the collector?

**Answer:** ❌ No

**Explanation:**
- There are two background tasks:
  1. `run_live_match_sync()` (every 30s): calls `CollectionService.ingest_matches` (football-data.org)
  2. `run_daily_scheduler()`: calls full `ingest_football_data` (includes football-data, Transfermarkt, FIFA, Elo, Odds API)
- Neither task uses `APIFootballCollector`

---

### 1.5 Are the new features actually included in `extract_ml_features()` at runtime?

**Answer:** ✅ Yes, BUT with caveats!

**Explanation:**
- The new features ARE present and returned by `extract_ml_features()`!
  - Standings features: `home_group_position`, `away_group_position`, etc.
  - Odds features: `home_implied_probability`, etc.
  - Live match features: `current_minute`, `home_red_cards`, etc.
- However:
  - These features have default values (0 or 0.333) when data is missing
  - The models weren't retrained with these features, so even if present, they aren't used!

---

### 1.6 Were `world_cup_predictor.pkl` and `goal_predictor.pkl` retrained after adding these new features?

**Answer:** ❌ No!

**Explanation:**
- **Goal Predictor (`models/goal_predictor.pkl`)**:
  - Has only 27 features! The new features (standings, odds, live) are NOT in the model's feature list!
  - Old features: `['elo_diff', 'fifa_diff', 'form_diff', 'gs_diff', 'gc_diff', 'inj_diff', 'susp_diff', 'available_squad_diff', 'starting_xi_value_diff', 'missing_star_players_diff', 'elo_momentum_diff', 'strength_of_schedule_diff', 'home_adv', 'h2h_factor', 'match_stage_weight', 'home_attack_rating', 'away_attack_rating', 'attack_rating_diff', 'home_defence_rating', 'away_defence_rating', 'defence_rating_diff', 'home_clean_sheet_rate', 'away_clean_sheet_rate', 'clean_sheet_rate_diff', 'home_btts_rate', 'away_btts_rate', 'btts_rate_diff']`

- **World Cup Predictor (`models/world_cup_predictor.pkl`)**:
  - Has only 28 features! The new features (standings, odds, live) are NOT in the model's feature list!
  - Old features: `['elo_diff', 'fifa_diff', 'form_diff', 'gs_diff', 'gc_diff', 'inj_diff', 'susp_diff', 'home_adv', 'h2h_factor', 'available_squad_diff', 'starting_xi_value_diff', 'missing_star_players_diff', 'match_stage_weight', 'elo_momentum_diff', 'home_elo_momentum', 'away_elo_momentum', 'strength_of_schedule_diff', 'home_strength_of_schedule', 'away_strength_of_schedule', 'world_cup_matches_played_diff', 'major_tournament_matches_diff', 'knockout_matches_diff', 'home_injury_count', 'away_injury_count', 'home_suspension_count', 'away_suspension_count', 'home_injury_market_value_loss', 'away_injury_market_value_loss']`

---

## 2. Report: Working, Partially Implemented, Non-Functional

### ✅ Working Features:
- **Database Schema Changes**: The new fields in the `matches` table were added successfully!
- **New Features in extract_ml_features**: All new features are being calculated and returned!
- **Standings Table Exists**: The standings table was already present!
- **Bookmaker Odds Table Exists**: The bookmaker odds table was already present and populated!

---

### ⚠️ Partially Implemented Features:
1. **API-Football Collector**:
   - The collector code exists in `collectors/api_football.py`, but it's not integrated anywhere!
   - It's not imported, initialized, or called!

2. **New Features in ML Datasets**:
   - We added new features to `ml/train_goal_model.py`, but we didn't update:
     - `ml/build_goal_dataset.py`
     - `ml/build_dataset_world_cup.py`
   - These files are needed to rebuild datasets with the new features!

---

### ❌ Completely Non-Functional:
1. **Populating API-Football fields in DB**: No code uses APIFootballCollector to update `api_football_id`, `current_minute`, `home_red_cards`, etc.
2. **ML Models using new features**: Even though extract_ml_features returns them, the models were never retrained!

---

## 3. Exact Files that Need Modification/Work Before Deployment

### 3.1 Modify Existing Files:
1. **`services/collection_service.py`**:
   - Import `APIFootballCollector`
   - Initialize it with `settings.API_FOOTBALL_KEY`
   - Add methods to ingest live data and update matches with red cards, current score, etc.

2. **`ml/build_goal_dataset.py`**:
   - Update to include ALL new features (standings, odds, live) when building the goal dataset!
   - Currently it only includes the old features!

3. **`ml/build_dataset_world_cup.py`**:
   - Update to include ALL new features when building the world cup outcome dataset!

4. **`api/main.py`**:
   - If you want to use APIFootball collector, either:
     - Update `run_live_match_sync()` to use APIFootballCollector in addition to FootballDataCollector
     - Or, create a separate background task for APIFootball data ingestion

5. **`collectors/api_football.py`**:
   - Needs enhancement: currently `parse_live_fixture` expects data from both fetch_live_matches and fetch_fixture_events, but the code is incomplete!

---

### 3.2 Run These Commands:
1. **Update Training Datasets**:
   ```bash
   python3 -m ml.build_goal_dataset
   python3 -m ml.build_dataset_world_cup
   ```

2. **Retrain Both Models**:
   ```bash
   python3 -m ml.train_goal_model
   python3 -m ml.train_world_cup_model
   ```

---

## 4. Summary

We started the live prediction upgrade, but we haven't finished:
- ✅ Created `collectors/api_football.py`
- ✅ Updated Match model
- ✅ Added Alembic migration and applied it
- ✅ Updated extract_ml_features with new features
- ✅ Updated train_goal_model.py's feature list
- ❌ NOT integrated collector into CollectionService
- ❌ NOT updated build_goal_dataset.py or build_dataset_world_cup.py
- ❌ NOT retrained the models
- ❌ NOT modified the live sync background task to use APIFootball

To fully implement this upgrade, we still need to do the above steps!
