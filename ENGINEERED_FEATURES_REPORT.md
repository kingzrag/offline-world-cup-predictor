# Engineered Features Report

Generated: 2026-06-26T14:17:55.930661Z

## Scope

Coverage below is measured across **315 finished international matches with enrichment data** (`match_statistics`, `player_match_performances`, or `match_lineups`).
A feature is counted as available for a match only when **both home and away team values** had supporting inputs.

## Engineered Feature Catalog

| Feature | Calculation formula | Database fields used | Providers contributing data | Matches available | Availability % |
|---|---|---|---|---:|---:|
| `goalkeeper_strength` | 0.35*gk_rating_score + 0.25*saves_score + 0.20*clean_sheet_rate + 0.20*conceded_score | `player_match_performances.rating`, `player_match_performances.sofa_score_rating`, `player_match_performances.saves`, `player_match_performances.position`, `matches.home_score`, `matches.away_score` | StatsBomb, SofaScore, FootballData | 278 | 88.25% |
| `passing_strength` | 0.35*pass_accuracy + 0.20*passes_norm + 0.25*successful_passes_norm + 0.20*possession_norm | `match_statistics.home_pass_accuracy`, `match_statistics.away_pass_accuracy`, `match_statistics.home_passes`, `match_statistics.away_passes`, `match_statistics.home_successful_passes`, `match_statistics.away_successful_passes`, `match_statistics.home_possession`, `match_statistics.away_possession` | StatsBomb, FBref, API-Football, SofaScore | 234 | 74.29% |
| `recent_form` | 0.50*points_ratio + 0.25*goal_diff_score + 0.25*xg_diff_score over last 5 matches | `matches.winner`, `matches.home_score`, `matches.away_score`, `match_statistics.home_expected_goals`, `match_statistics.away_expected_goals` | FootballData, StatsBomb, SofaScore | 278 | 88.25% |
| `aerial_dominance` | 0.70*aerial_win_pct + 0.30*aerial_volume_norm | `player_match_performances.aerial_duels`, `player_match_performances.aerial_duels_won`, `match_statistics.home_aerial_duels`, `match_statistics.away_aerial_duels` | StatsBomb, FBref | 234 | 74.29% |
| `pressing_strength` | 0.30*tackles_norm + 0.25*interceptions_norm + 0.45*pressures_norm | `match_statistics.home_tackles`, `match_statistics.away_tackles`, `match_statistics.home_interceptions`, `match_statistics.away_interceptions`, `match_statistics.home_pressures`, `match_statistics.away_pressures`, `player_match_performances.pressures` | StatsBomb, FBref | 234 | 74.29% |
| `defensive_stability` | 0.35*clean_sheet_rate + 0.30*inverse_xga + 0.25*inverse_goals_conceded + 0.10*blocks_norm | `matches.home_score`, `matches.away_score`, `match_statistics.home_expected_goals`, `match_statistics.away_expected_goals`, `player_match_performances.blocks`, `player_match_performances.clearances` | FootballData, StatsBomb, FBref | 278 | 88.25% |
| `attacking_efficiency` | 0.30*xg_norm + 0.30*goals_norm + 0.20*shots_on_target_rate + 0.20*conversion_rate | `matches.home_score`, `matches.away_score`, `match_statistics.home_expected_goals`, `match_statistics.away_expected_goals`, `match_statistics.home_shots`, `match_statistics.away_shots`, `match_statistics.home_shots_on_target`, `match_statistics.away_shots_on_target` | FootballData, StatsBomb, SofaScore | 278 | 88.25% |
| `finishing_quality` | 0.70*(goals/xG)_norm + 0.30*shots_on_target_rate; big chances are unavailable and omitted | `matches.home_score`, `matches.away_score`, `match_statistics.home_expected_goals`, `match_statistics.away_expected_goals`, `match_statistics.home_shots`, `match_statistics.away_shots`, `match_statistics.home_shots_on_target`, `match_statistics.away_shots_on_target` | FootballData, StatsBomb, SofaScore | 278 | 88.25% |
| `set_piece_strength` | 0.55*corners_norm + 0.45*aerial_win_pct | `match_statistics.home_corners`, `match_statistics.away_corners`, `player_match_performances.aerial_duels`, `player_match_performances.aerial_duels_won` | StatsBomb, FBref | 234 | 74.29% |
| `midfield_control` | 0.40*pass_accuracy + 0.20*successful_passes_norm + 0.15*passes_norm + 0.25*possession_norm | `match_statistics.home_pass_accuracy`, `match_statistics.away_pass_accuracy`, `match_statistics.home_successful_passes`, `match_statistics.away_successful_passes`, `match_statistics.home_passes`, `match_statistics.away_passes`, `match_statistics.home_possession`, `match_statistics.away_possession` | StatsBomb, FBref, API-Football, SofaScore | 234 | 74.29% |
| `squad_availability` | 0.50*player_availability + 0.30*available_starters_ratio + 0.10*(1-injury_impact) + 0.10*(1-suspension_impact) | `injuries.player_name`, `injuries.player_market_value`, `suspensions.player_name`, `suspensions.player_market_value`, `national_team_players.player_name`, `national_team_players.market_value` | Transfermarkt | 315 | 100.00% |
| `tactical_stability` | 0.55*formation_consistency + 0.45*lineup_consistency | `match_lineups.formation`, `match_lineups.starting_xi` | StatsBomb, SofaScore | 234 | 74.29% |

## Notes

- Existing intelligence fields remain unchanged and backward-compatible.
- These engineered features are internal ML features only; frontend behavior is unchanged.
- `midfield_control` already existed and was strengthened using pass volume + successful passes + possession.
- `goalkeeper_strength`, `passing_strength`, and `recent_form` extend existing metrics without removing `goalkeeper_performance`, `passing_dominance`, or `momentum_score`.
- `big chances scored` is not currently stored in PostgreSQL, so `finishing_quality` excludes it and relies on goals/xG + shot quality proxies.
- `recoveries` are not currently stored as a dedicated field, so `pressing_strength` uses tackles, interceptions, and pressures.
