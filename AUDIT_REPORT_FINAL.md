
# WORLD CUP PREDICTION FEATURE AUDIT REPORT

---

## 1. API ENDPOINT & FEATURE FLOW
- Endpoints: `POST /api/predict` and `POST /api/predict-batch` in `api/routes/predict.py`
- Flow: `predict.py` → `services/model_service.py` → `ml/features.py` → extracts features → runs through trained models → returns predictions
- No cached feature values - features are calculated in real-time from the database

---

## 2. DATABASE TABLES USED
- **`Team`**: Stores team information, FIFA ranking, squad market value
- **`Match`**: Stores all matches (historical, friendly, WC, WCQ), including status, score, date, teams, competition
- **`Competition`**: Stores competition information
- **`TeamElo`**: Stores ELO ratings for teams
- **`Injury` / `Suspension`**: Stores player injuries and suspensions

---

## 3. FEATURE UPDATE FREQUENCY
All features are recalculated in real-time for every prediction request (no cached features):
- Features based on match results: Updated whenever new `FINISHED` matches are added to the database
- Features based on injuries/suspensions: Updated whenever `Injury`/`Suspension` records change
- FIFA rankings and squad market values: Updated whenever `Team` records are updated

---

## 4. 2026 WORLD CUP MATCHES: ARE THEY USED?
- **YES!** 2026 FIFA World Cup matches are stored in the database, and those marked `FINISHED` are included in feature calculations
- Database contains **48 FINISHED 2026 WC matches** as of 2026-06-24
- These matches are included in:
  - `form_diff`, `gs_diff`, `gc_diff` (last 5 matches)
  - `attack_rating`, `defence_rating`, `clean_sheet_rate`, `btts_rate` (last 20 matches)
  - `elo_momentum` (last 10 matches)
  - `strength_of_schedule` (last 5 matches)

---

## 5. TEAM-SPECIFIC MATCH AUDITS

### 🔹 GERMANY
- **FIFA Ranking**: 5
- **Squad Value**: €747.47M
- **Last 10 FINISHED Matches (for form/gs/gc)**:
  1. 2026-06-20: Germany 2-1 Ivory Coast (W) - FIFA World Cup
  2. 2026-06-14: Germany 7-1 Curaçao (W) - FIFA World Cup
  3. 2026-05-30: Germany 2-0 Greece (W) - Friendly
  4. 2026-03-26: Germany 2-1 Netherlands (W) - Friendly
  5. 2026-03-23: Germany 2-0 France (W) - Friendly
  6. 2025-11-16: Germany 4-0 Bosnia-Herzegovina (W) - Friendly
  7. 2025-11-14: Germany 2-1 Netherlands (W) - Friendly
  8. 2025-10-14: Germany 3-1 England (W) - UEFA Nations League
  9. 2025-10-11: Germany 1-0 France (W) - UEFA Nations League
  10. 2025-09-06: Germany 2-0 Netherlands (W) - Friendly

### 🔹 BRAZIL
- **FIFA Ranking**: 1
- **Squad Value**: €1551.35M
- **Last 10 FINISHED Matches (for form/gs/gc)**:
  1. 2026-06-20: Brazil 3-0 Haiti (W) - FIFA World Cup
  2. 2026-06-13: Brazil 1-1 Morocco (D) - FIFA World Cup
  3. 2026-06-04: Brazil 4-0 Ecuador (W) - Friendly
  4. 2026-05-30: Brazil 1-0 Uruguay (W) - Friendly
  5. 2026-03-27: Brazil 1-0 Spain (W) - Friendly
  6. 2026-03-23: Brazil 1-0 Portugal (W) - Friendly
  7. 2025-11-19: Brazil 3-0 Venezuela (W) - FIFA World Cup qualification
  8. 2025-11-14: Brazil 2-0 Chile (W) - FIFA World Cup qualification
  9. 2025-10-15: Brazil 1-0 Bolivia (W) - FIFA World Cup qualification
  10. 2025-10-10: Brazil 3-1 Peru (W) - FIFA World Cup qualification

### 🔹 QATAR
- **FIFA Ranking**: 64
- **Squad Value**: €77.93M
- **Last 10 FINISHED Matches (for form/gs/gc)**:
  1. 2026-06-18: Qatar 0-6 Canada (L) - FIFA World Cup
  2. 2026-06-13: Qatar 1-1 Switzerland (D) - FIFA World Cup
  3. 2026-05-29: Qatar 0-1 Iraq (L) - Friendly
  4. 2026-03-27: Qatar 0-1 Syria (L) - Friendly
  5. 2026-03-23: Qatar 0-1 Kuwait (L) - Friendly
  6. 2025-11-18: Qatar 0-0 Jordan (D) - FIFA World Cup qualification
  7. 2025-11-14: Qatar 0-0 Bahrain (D) - FIFA World Cup qualification
  8. 2025-10-15: Qatar 1-0 Yemen (W) - FIFA World Cup qualification
  9. 2025-10-11: Qatar 1-0 Palestine (W) - FIFA World Cup qualification
  10. 2025-09-09: Qatar 0-0 United Arab Emirates (D) - FIFA World Cup qualification

### 🔹 ECUADOR
- **FIFA Ranking**: 16
- **Squad Value**: €536.02M
- **Last 10 FINISHED Matches (for form/gs/gc)**:
  1. 2026-06-21: Ecuador 0-0 Curaçao (D) - FIFA World Cup
  2. 2026-06-14: Ecuador 0-1 Ivory Coast (L) - FIFA World Cup
  3. 2026-05-30: Ecuador 2-1 Saudi Arabia (W) - Friendly
  4. 2026-03-31: Ecuador 1-1 Netherlands (D) - Friendly
  5. 2026-03-27: Ecuador 1-1 Morocco (D) - Friendly
  6. 2025-11-18: Ecuador 2-0 New Zealand (W) - Friendly
  7. 2025-11-13: Ecuador 0-0 Canada (D) - Friendly
  8. 2025-10-14: Ecuador 1-1 Mexico (D) - Friendly
  9. 2025-10-10: Ecuador 1-1 United States (D) - Friendly
  10. 2025-09-09: Ecuador 1-0 Argentina (W) - FIFA World Cup qualification

---

## 6. FEATURE CLASSIFICATION

| Feature | Updates During Tournament? | Uses Recent WC Results? | Uses Live Standings? | Uses Injuries? | Uses Suspensions? | Uses Lineups? | Uses FIFA Rankings? | Uses ELO Ratings? | Uses Betting Odds? |
|---------|---------------------------|------------------------|---------------------|---------------|------------------|--------------|--------------------|------------------|-------------------|
| `elo_diff` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| `fifa_diff` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| `form_diff` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `gs_diff` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `gc_diff` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `mv_diff` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `inj_diff` | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `susp_diff` | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| `home_adv` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `h2h_factor` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `available_squad_diff` | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| `starting_xi_value_diff` | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| `missing_star_players_diff` | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| `match_stage_weight` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `home_elo_momentum` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| `away_elo_momentum` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| `elo_momentum_diff` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| `home_strength_of_schedule` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| `away_strength_of_schedule` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| `strength_of_schedule_diff` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| `world_cup_matches_played_diff` | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `major_tournament_matches_diff` | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `knockout_matches_diff` | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `home_attack_rating` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `away_attack_rating` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `attack_rating_diff` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `home_defence_rating` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `away_defence_rating` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `defence_rating_diff` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `home_clean_sheet_rate` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `away_clean_sheet_rate` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `clean_sheet_rate_diff` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `home_btts_rate` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `away_btts_rate` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `btts_rate_diff` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `home_injury_count` | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `away_injury_count` | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `home_suspension_count` | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| `away_suspension_count` | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| `home_injury_market_value_loss` | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `away_injury_market_value_loss` | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |

---

## 7. KEY FINDINGS

### ✅ LIVE TOURNAMENT MATCHES ARE USED!
- 2026 FIFA World Cup matches marked `FINISHED` are included in all recent match features (form, goals, attack/defence ratings, etc.)
- The feature calculation code in `ml/features.py` uses **all `FINISHED` matches with `utc_date < match_date`**, regardless of competition
- This means predictions update automatically as tournament matches conclude!

### ❌ NO LIVE STANDINGS, LINEUPS, OR BETTING ODDS
- The system does not use:
  - Live group standings or points accumulated
  - Starting lineups or player availability beyond injury/suspension status
  - Betting odds of any kind

---

## 8. EXPLANATION OF PREDICTIONS

### 🇩🇪 GERMANY vs ECUADOR 🇪🇨
- **Why Germany was strongly favored**:
  - `elo_diff`: +123 (Germany's Elo much higher)
  - `fifa_diff`: +9 (Germany's FIFA rank much better)
  - `form_diff`: +1.8 (Germany had won 10 straight before this match)
  - `gs_diff`: +3.0 (Germany scoring far more goals recently)
  - `h2h_factor`: 1.0 (Germany had won all recent head-to-head matches)
  - `available_squad_diff`: +211.45M€ (Germany's squad far more valuable)

### 🏴󠁧󠁢󠁳󠁣󠁴󠁿 SCOTLAND vs BRAZIL 🇧🇷
- **Why Brazil was strongly favored**:
  - `elo_diff`: -213 (Brazil's Elo way higher)
  - `fifa_diff`: -30 (Brazil FIFA rank #1, Scotland much lower)
  - `form_diff`: -0.8 (Brazil had better recent form)
  - `gs_diff`: -1.8 (Brazil scoring way more)
  - `available_squad_diff`: -1015.33M€ (Brazil's squad vastly more valuable)

---

## 9. CONCLUSION
- ✅ **Current WC match results are actively affecting predictions** (48 FINISHED 2026 WC matches in DB as of 2026-06-24)
- ✅ Features are calculated in real-time for every request
- ❌ No cached features
- ❌ No use of live standings, lineups, or betting odds
- ✅ Injuries and suspensions are considered (via market value impact)
