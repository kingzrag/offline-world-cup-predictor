# Database Audit Report

Generated: 2026-06-26T13:02:37.704930Z

## Required Totals

- **Total Competitions**: 26
- **Total International Matches**: 10,735
- **Total Players**: 4,165
- **Total Player Performances**: 18,800
- **Total Match Statistics**: 398
- **Total Lineups**: 796
- **Total Injuries**: 55
- **Total Suspensions**: 1
- **Total Xg Records**: 5,796
  - match statistics: 398
  - player performances: 5,398
- **Total Passing Records**: 12,033
  - match statistics: 397
  - player performances: 11,636
- **Total Goalkeeper Records**: 806
- **Total Interceptions**: 5,246
  - match statistics: 397
  - player performances: 4,849
- **Total Tackles**: 7,196
  - match statistics: 397
  - player performances: 6,799
- **Total Aerial Duels**: 6,474
  - match statistics: 397
  - player performances: 6,077

## Column Completeness

### `competitions`

| Column | Type | Populated Rows | Empty Rows | % Complete |
|---|---:|---:|---:|---:|
| `id` | `INTEGER` | 26 | 0 | 100.00% |
| `api_id` | `VARCHAR(50)` | 14 | 12 | 53.85% |
| `name` | `VARCHAR(100)` | 26 | 0 | 100.00% |
| `code` | `VARCHAR(20)` | 26 | 0 | 100.00% |
| `area` | `VARCHAR(100)` | 16 | 10 | 61.54% |
| `created_at` | `DATETIME` | 26 | 0 | 100.00% |
| `updated_at` | `DATETIME` | 26 | 0 | 100.00% |

### `teams`

| Column | Type | Populated Rows | Empty Rows | % Complete |
|---|---:|---:|---:|---:|
| `id` | `INTEGER` | 344 | 0 | 100.00% |
| `api_id` | `VARCHAR(50)` | 70 | 274 | 20.35% |
| `name` | `VARCHAR(100)` | 344 | 0 | 100.00% |
| `short_name` | `VARCHAR(50)` | 70 | 274 | 20.35% |
| `tla` | `VARCHAR(10)` | 68 | 276 | 19.77% |
| `crest_url` | `VARCHAR(255)` | 68 | 276 | 19.77% |
| `founded` | `INTEGER` | 53 | 291 | 15.41% |
| `venue` | `VARCHAR(100)` | 51 | 293 | 14.83% |
| `transfermarkt_url` | `VARCHAR(255)` | 68 | 276 | 19.77% |
| `fifa_ranking` | `INTEGER` | 303 | 41 | 88.08% |
| `market_value` | `FLOAT` | 130 | 214 | 37.79% |
| `squad_market_value` | `FLOAT` | 283 | 61 | 82.27% |
| `created_at` | `DATETIME` | 344 | 0 | 100.00% |
| `updated_at` | `DATETIME` | 344 | 0 | 100.00% |

### `players`

| Column | Type | Populated Rows | Empty Rows | % Complete |
|---|---:|---:|---:|---:|
| `id` | `INTEGER` | 4,165 | 0 | 100.00% |
| `api_id` | `VARCHAR(50)` | 4,165 | 0 | 100.00% |
| `team_id` | `INTEGER` | 4,165 | 0 | 100.00% |
| `name` | `VARCHAR(100)` | 4,165 | 0 | 100.00% |
| `position` | `VARCHAR(50)` | 3,372 | 793 | 80.96% |
| `date_of_birth` | `DATE` | 428 | 3,737 | 10.28% |
| `nationality` | `VARCHAR(50)` | 428 | 3,737 | 10.28% |
| `role` | `VARCHAR(50)` | 428 | 3,737 | 10.28% |
| `created_at` | `DATETIME` | 4,165 | 0 | 100.00% |
| `updated_at` | `DATETIME` | 4,165 | 0 | 100.00% |

### `matches`

| Column | Type | Populated Rows | Empty Rows | % Complete |
|---|---:|---:|---:|---:|
| `id` | `INTEGER` | 20,892 | 0 | 100.00% |
| `api_id` | `VARCHAR(50)` | 20,654 | 238 | 98.86% |
| `api_football_id` | `VARCHAR(50)` | 0 | 20,892 | 0.00% |
| `sofa_score_id` | `VARCHAR(50)` | 0 | 20,892 | 0.00% |
| `statsbomb_id` | `VARCHAR(50)` | 397 | 20,495 | 1.90% |
| `competition_id` | `INTEGER` | 20,892 | 0 | 100.00% |
| `home_team_id` | `INTEGER` | 20,892 | 0 | 100.00% |
| `away_team_id` | `INTEGER` | 20,892 | 0 | 100.00% |
| `utc_date` | `DATETIME` | 20,892 | 0 | 100.00% |
| `status` | `VARCHAR(50)` | 20,892 | 0 | 100.00% |
| `stage` | `VARCHAR(50)` | 690 | 20,202 | 3.30% |
| `group` | `VARCHAR(50)` | 72 | 20,820 | 0.34% |
| `home_score` | `INTEGER` | 20,873 | 19 | 99.91% |
| `away_score` | `INTEGER` | 20,873 | 19 | 99.91% |
| `winner` | `VARCHAR(50)` | 20,873 | 19 | 99.91% |
| `live_minute` | `INTEGER` | 0 | 20,892 | 0.00% |
| `current_minute` | `INTEGER` | 0 | 20,892 | 0.00% |
| `home_red_cards` | `INTEGER` | 20,892 | 0 | 100.00% |
| `away_red_cards` | `INTEGER` | 20,892 | 0 | 100.00% |
| `home_yellow_cards` | `INTEGER` | 20,892 | 0 | 100.00% |
| `away_yellow_cards` | `INTEGER` | 20,892 | 0 | 100.00% |
| `current_home_score` | `INTEGER` | 0 | 20,892 | 0.00% |
| `current_away_score` | `INTEGER` | 0 | 20,892 | 0.00% |
| `home_formation` | `VARCHAR(20)` | 398 | 20,494 | 1.91% |
| `away_formation` | `VARCHAR(20)` | 398 | 20,494 | 1.91% |
| `home_possession` | `FLOAT` | 398 | 20,494 | 1.91% |
| `away_possession` | `FLOAT` | 398 | 20,494 | 1.91% |
| `home_expected_goals` | `FLOAT` | 398 | 20,494 | 1.91% |
| `away_expected_goals` | `FLOAT` | 398 | 20,494 | 1.91% |
| `created_at` | `DATETIME` | 20,892 | 0 | 100.00% |
| `updated_at` | `DATETIME` | 20,892 | 0 | 100.00% |

### `match_statistics`

| Column | Type | Populated Rows | Empty Rows | % Complete |
|---|---:|---:|---:|---:|
| `id` | `INTEGER` | 398 | 0 | 100.00% |
| `match_id` | `INTEGER` | 398 | 0 | 100.00% |
| `home_possession` | `FLOAT` | 398 | 0 | 100.00% |
| `away_possession` | `FLOAT` | 398 | 0 | 100.00% |
| `home_shots` | `INTEGER` | 398 | 0 | 100.00% |
| `away_shots` | `INTEGER` | 398 | 0 | 100.00% |
| `home_shots_on_target` | `INTEGER` | 398 | 0 | 100.00% |
| `away_shots_on_target` | `INTEGER` | 398 | 0 | 100.00% |
| `home_corners` | `INTEGER` | 398 | 0 | 100.00% |
| `away_corners` | `INTEGER` | 398 | 0 | 100.00% |
| `home_expected_goals` | `FLOAT` | 398 | 0 | 100.00% |
| `away_expected_goals` | `FLOAT` | 398 | 0 | 100.00% |
| `home_fouls` | `INTEGER` | 398 | 0 | 100.00% |
| `away_fouls` | `INTEGER` | 398 | 0 | 100.00% |
| `home_offsides` | `INTEGER` | 398 | 0 | 100.00% |
| `away_offsides` | `INTEGER` | 398 | 0 | 100.00% |
| `home_passes` | `INTEGER` | 397 | 1 | 99.75% |
| `away_passes` | `INTEGER` | 397 | 1 | 99.75% |
| `home_successful_passes` | `INTEGER` | 397 | 1 | 99.75% |
| `away_successful_passes` | `INTEGER` | 397 | 1 | 99.75% |
| `home_pass_accuracy` | `FLOAT` | 397 | 1 | 99.75% |
| `away_pass_accuracy` | `FLOAT` | 397 | 1 | 99.75% |
| `home_tackles` | `INTEGER` | 397 | 1 | 99.75% |
| `away_tackles` | `INTEGER` | 397 | 1 | 99.75% |
| `home_interceptions` | `INTEGER` | 397 | 1 | 99.75% |
| `away_interceptions` | `INTEGER` | 397 | 1 | 99.75% |
| `home_aerial_duels` | `INTEGER` | 397 | 1 | 99.75% |
| `away_aerial_duels` | `INTEGER` | 396 | 2 | 99.50% |
| `home_pressures` | `INTEGER` | 397 | 1 | 99.75% |
| `away_pressures` | `INTEGER` | 397 | 1 | 99.75% |
| `home_carries` | `INTEGER` | 397 | 1 | 99.75% |
| `away_carries` | `INTEGER` | 397 | 1 | 99.75% |
| `data_source` | `VARCHAR(50)` | 397 | 1 | 99.75% |
| `created_at` | `DATETIME` | 398 | 0 | 100.00% |
| `updated_at` | `DATETIME` | 398 | 0 | 100.00% |

### `match_lineups`

| Column | Type | Populated Rows | Empty Rows | % Complete |
|---|---:|---:|---:|---:|
| `id` | `INTEGER` | 796 | 0 | 100.00% |
| `match_id` | `INTEGER` | 796 | 0 | 100.00% |
| `team_id` | `INTEGER` | 796 | 0 | 100.00% |
| `formation` | `VARCHAR(20)` | 796 | 0 | 100.00% |
| `starting_xi` | `TEXT` | 796 | 0 | 100.00% |
| `substitutes` | `TEXT` | 796 | 0 | 100.00% |
| `coach_name` | `VARCHAR(100)` | 794 | 2 | 99.75% |
| `sofa_score_id` | `VARCHAR(50)` | 0 | 796 | 0.00% |
| `created_at` | `DATETIME` | 796 | 0 | 100.00% |
| `updated_at` | `DATETIME` | 796 | 0 | 100.00% |

### `match_events`

| Column | Type | Populated Rows | Empty Rows | % Complete |
|---|---:|---:|---:|---:|
| `id` | `INTEGER` | 4,417 | 0 | 100.00% |
| `match_id` | `INTEGER` | 4,417 | 0 | 100.00% |
| `team_id` | `INTEGER` | 4,417 | 0 | 100.00% |
| `type` | `VARCHAR(18)` | 4,417 | 0 | 100.00% |
| `minute` | `INTEGER` | 4,417 | 0 | 100.00% |
| `extra_minute` | `INTEGER` | 0 | 4,417 | 0.00% |
| `description` | `VARCHAR(255)` | 4,417 | 0 | 100.00% |
| `player_name` | `VARCHAR(100)` | 4,417 | 0 | 100.00% |
| `player_id` | `INTEGER` | 0 | 4,417 | 0.00% |
| `assist_player_name` | `VARCHAR(100)` | 0 | 4,417 | 0.00% |
| `assist_player_id` | `INTEGER` | 0 | 4,417 | 0.00% |
| `substitute_in_player_name` | `VARCHAR(100)` | 0 | 4,417 | 0.00% |
| `substitute_in_player_id` | `INTEGER` | 0 | 4,417 | 0.00% |
| `sofa_score_id` | `VARCHAR(50)` | 3 | 4,414 | 0.07% |
| `created_at` | `DATETIME` | 4,417 | 0 | 100.00% |
| `updated_at` | `DATETIME` | 4,417 | 0 | 100.00% |

### `player_match_performances`

| Column | Type | Populated Rows | Empty Rows | % Complete |
|---|---:|---:|---:|---:|
| `id` | `INTEGER` | 18,800 | 0 | 100.00% |
| `match_id` | `INTEGER` | 18,800 | 0 | 100.00% |
| `team_id` | `INTEGER` | 18,800 | 0 | 100.00% |
| `player_id` | `INTEGER` | 18,797 | 3 | 99.98% |
| `player_name` | `VARCHAR(100)` | 18,800 | 0 | 100.00% |
| `rating` | `FLOAT` | 0 | 18,800 | 0.00% |
| `position` | `VARCHAR(50)` | 11,784 | 7,016 | 62.68% |
| `is_starter` | `INTEGER` | 18,800 | 0 | 100.00% |
| `minutes_played` | `INTEGER` | 8,755 | 10,045 | 46.57% |
| `goals` | `INTEGER` | 18,800 | 0 | 100.00% |
| `assists` | `INTEGER` | 18,800 | 0 | 100.00% |
| `shots` | `INTEGER` | 18,800 | 0 | 100.00% |
| `shots_on_target` | `INTEGER` | 18,800 | 0 | 100.00% |
| `passes` | `INTEGER` | 18,800 | 0 | 100.00% |
| `successful_passes` | `INTEGER` | 18,796 | 4 | 99.98% |
| `pass_accuracy` | `FLOAT` | 11,636 | 7,164 | 61.89% |
| `tackles` | `INTEGER` | 18,800 | 0 | 100.00% |
| `interceptions` | `INTEGER` | 18,800 | 0 | 100.00% |
| `saves` | `INTEGER` | 18,800 | 0 | 100.00% |
| `fouls_committed` | `INTEGER` | 18,800 | 0 | 100.00% |
| `fouls_drawn` | `INTEGER` | 18,800 | 0 | 100.00% |
| `yellow_cards` | `INTEGER` | 18,800 | 0 | 100.00% |
| `red_cards` | `INTEGER` | 18,800 | 0 | 100.00% |
| `offsides` | `INTEGER` | 18,800 | 0 | 100.00% |
| `corners` | `INTEGER` | 18,800 | 0 | 100.00% |
| `aerial_duels` | `INTEGER` | 18,796 | 4 | 99.98% |
| `aerial_duels_won` | `INTEGER` | 18,796 | 4 | 99.98% |
| `key_passes` | `INTEGER` | 18,796 | 4 | 99.98% |
| `pressures` | `INTEGER` | 18,796 | 4 | 99.98% |
| `carries` | `INTEGER` | 18,796 | 4 | 99.98% |
| `dribbles_completed` | `INTEGER` | 0 | 18,800 | 0.00% |
| `clearances` | `INTEGER` | 0 | 18,800 | 0.00% |
| `blocks` | `INTEGER` | 0 | 18,800 | 0.00% |
| `sofa_score_id` | `VARCHAR(50)` | 4 | 18,796 | 0.02% |
| `sofa_score_rating` | `FLOAT` | 4 | 18,796 | 0.02% |
| `fbref_id` | `VARCHAR(100)` | 0 | 18,800 | 0.00% |
| `statsbomb_id` | `VARCHAR(100)` | 18,796 | 4 | 99.98% |
| `statsbomb_xg` | `FLOAT` | 18,796 | 4 | 99.98% |
| `created_at` | `DATETIME` | 18,800 | 0 | 100.00% |
| `updated_at` | `DATETIME` | 18,800 | 0 | 100.00% |

### `injuries`

| Column | Type | Populated Rows | Empty Rows | % Complete |
|---|---:|---:|---:|---:|
| `id` | `INTEGER` | 55 | 0 | 100.00% |
| `player_name` | `VARCHAR(100)` | 55 | 0 | 100.00% |
| `team_id` | `INTEGER` | 55 | 0 | 100.00% |
| `team_name` | `VARCHAR(100)` | 55 | 0 | 100.00% |
| `injury_type` | `VARCHAR(255)` | 55 | 0 | 100.00% |
| `expected_return_date` | `DATE` | 34 | 21 | 61.82% |
| `days_out` | `INTEGER` | 34 | 21 | 61.82% |
| `player_market_value` | `FLOAT` | 15 | 40 | 27.27% |
| `last_updated` | `DATETIME` | 55 | 0 | 100.00% |

### `suspensions`

| Column | Type | Populated Rows | Empty Rows | % Complete |
|---|---:|---:|---:|---:|
| `id` | `INTEGER` | 1 | 0 | 100.00% |
| `player_name` | `VARCHAR(100)` | 1 | 0 | 100.00% |
| `team_id` | `INTEGER` | 1 | 0 | 100.00% |
| `team_name` | `VARCHAR(100)` | 1 | 0 | 100.00% |
| `suspension_reason` | `VARCHAR(255)` | 1 | 0 | 100.00% |
| `matches_remaining` | `INTEGER` | 0 | 1 | 0.00% |
| `player_market_value` | `FLOAT` | 0 | 1 | 0.00% |
| `last_updated` | `DATETIME` | 1 | 0 | 100.00% |
| `sofa_score_id` | `VARCHAR(50)` | 0 | 1 | 0.00% |
| `source` | `VARCHAR(50)` | 1 | 0 | 100.00% |
| `status` | `VARCHAR(8)` | 1 | 0 | 100.00% |
| `matches_banned` | `INTEGER` | 0 | 1 | 0.00% |
| `reason` | `VARCHAR(255)` | 1 | 0 | 100.00% |
| `official_date` | `DATE` | 0 | 1 | 0.00% |

### `national_team_players`

| Column | Type | Populated Rows | Empty Rows | % Complete |
|---|---:|---:|---:|---:|
| `id` | `INTEGER` | 7,075 | 0 | 100.00% |
| `team_id` | `INTEGER` | 7,075 | 0 | 100.00% |
| `player_name` | `VARCHAR(100)` | 7,075 | 0 | 100.00% |
| `position` | `VARCHAR(50)` | 7,075 | 0 | 100.00% |
| `age` | `INTEGER` | 7,075 | 0 | 100.00% |
| `market_value` | `FLOAT` | 7,075 | 0 | 100.00% |
| `transfermarkt_url` | `VARCHAR(255)` | 7,075 | 0 | 100.00% |
| `created_at` | `DATETIME` | 7,075 | 0 | 100.00% |
| `updated_at` | `DATETIME` | 7,075 | 0 | 100.00% |

### `standings`

| Column | Type | Populated Rows | Empty Rows | % Complete |
|---|---:|---:|---:|---:|
| `id` | `INTEGER` | 68 | 0 | 100.00% |
| `competition_id` | `INTEGER` | 68 | 0 | 100.00% |
| `team_id` | `INTEGER` | 68 | 0 | 100.00% |
| `position` | `INTEGER` | 68 | 0 | 100.00% |
| `played_games` | `INTEGER` | 68 | 0 | 100.00% |
| `won` | `INTEGER` | 68 | 0 | 100.00% |
| `draw` | `INTEGER` | 68 | 0 | 100.00% |
| `lost` | `INTEGER` | 68 | 0 | 100.00% |
| `points` | `INTEGER` | 68 | 0 | 100.00% |
| `goals_for` | `INTEGER` | 68 | 0 | 100.00% |
| `goals_against` | `INTEGER` | 68 | 0 | 100.00% |
| `goals_difference` | `INTEGER` | 68 | 0 | 100.00% |
| `created_at` | `DATETIME` | 68 | 0 | 100.00% |
| `updated_at` | `DATETIME` | 68 | 0 | 100.00% |
