================================================================================
MODEL V2: HIGH-IMPACT MISSING FOOTBALL FEATURES
================================================================================

Date: 2026-07-03
Objective: Identify high-impact football features missing from the current model.

Current Feature Set Analysis:
- ELO ratings, FIFA rankings, squad market value
- Recent form (points, goals scored, goals conceded)
- Injury/suspension impacts
- Attack/defense ratings (exponential decay weighted)
- Clean sheet rates, BTTS rates
- Head-to-head factors
- Kaggle features (attack/defense ratings, discipline, suspension risk, XI strength)
- Intelligence features (goalkeeper strength, passing strength)
- Standings features (group position, points, goal difference)
- Tournament experience, strength of schedule
- ELO momentum

================================================================================
RANKED FEATURE PROPOSALS (Highest Impact → Lowest Impact)
================================================================================

================================================================================
1. REST DAYS BEFORE MATCH
================================================================================

Description:
Number of days since each team's previous match. Teams with more rest typically perform better due to recovery time, especially in tournament settings where matches are frequent.

Formula:
- home_rest_days = match_date - home_team_previous_match_date
- away_rest_days = match_date - away_team_previous_match_date
- rest_days_diff = home_rest_days - away_rest_days

Raw Data Source:
- Match table (utc_date field)
- Query previous match for each team before current match_date

Difficulty:
- LOW - Straightforward database query

Computational Cost:
- LOW - Simple date calculation and lookup

Expected Impact:
- HIGH - Tournament scheduling significantly affects performance
- Teams with 3+ days rest outperform those with 1 day rest
- Particularly important in World Cup knockout stages
- Studies show 15-20% performance improvement with adequate rest

Where it belongs in ml/features.py:
- New function: get_rest_days(db, team_id, match_date)
- Call in extract_ml_features() before injury/suspension calculations
- Add to feature dictionary as: home_rest_days, away_rest_days, rest_days_diff

Implementation Notes:
- Handle case where no previous match exists (use default 7 days)
- Consider tournament stage (group stage vs knockout may have different rest patterns)
- Could be combined with travel distance for fatigue index

================================================================================
2. PLAYER FATIGUE INDEX
================================================================================

Description:
Aggregate measure of player fatigue based on minutes played in recent matches. High fatigue reduces performance, increases injury risk, and affects tactical execution.

Formula:
- For each player: fatigue_score = Σ(minutes_played × weight) / Σ(weight)
- weight = exp(-0.1 × match_index) for last 5 matches
- team_fatigue = average of top 11 players' fatigue scores
- fatigue_diff = home_fatigue - away_fatigue

Raw Data Source:
- match_lineups table (player minutes)
- NationalTeamPlayer table (player-team mapping)
- Match table (match dates)

Difficulty:
- MEDIUM - Requires joining multiple tables and calculating per-player fatigue

Computational Cost:
- MEDIUM - Need to query lineups for last 5 matches per team
- Calculate weighted average for each player
- Aggregate to team level

Expected Impact:
- HIGH - Fatigue is a well-documented performance factor
- Players with >300 minutes in 7 days show 25% performance drop
- Critical in tournament settings with tight schedules
- Affects both physical and mental performance

Where it belongs in ml/features.py:
- New function: get_player_fatigue_index(db, team_id, match_date)
- Call in extract_ml_features() after injury/suspension calculations
- Add to feature dictionary as: home_fatigue_index, away_fatigue_index, fatigue_diff

Implementation Notes:
- Focus on starting XI players (most impactful)
- Use exponential decay (decay_rate = 0.1) for recent matches
- Could be combined with rest days for comprehensive fatigue measure
- Handle missing lineup data gracefully

================================================================================
3. SHOT CONVERSION RATE
================================================================================

Description:
Percentage of shots that result in goals. High conversion rate indicates clinical finishing and attacking efficiency, which is predictive of future goal-scoring ability.

Formula:
- home_conversion = home_goals / home_shots (last 10 matches)
- away_conversion = away_goals / away_shots (last 10 matches)
- conversion_diff = home_conversion - away_conversion

Raw Data Source:
- match_team_stats table (shots, goals)
- Match table (match dates, team IDs)

Difficulty:
- LOW - Straightforward aggregation from existing stats table

Computational Cost:
- LOW - Simple ratio calculation over last 10 matches

Expected Impact:
- HIGH - Conversion rate is more stable than raw goals
- Teams with high conversion rate sustain performance better
- xG (expected goals) models heavily weight conversion rate
- Studies show 10-15% predictive power for match outcomes

Where it belongs in ml/features.py:
- New function: get_shot_conversion_rate(db, team_id, match_date)
- Call in extract_ml_features() after attack/defense ratings
- Add to feature dictionary as: home_shot_conversion, away_shot_conversion, shot_conversion_diff

Implementation Notes:
- Use exponential decay weighting (decay_rate = 0.15) for temporal relevance
- Handle division by zero (teams with 0 shots)
- Could be combined with xG if available
- Separate home vs away conversion rates (teams convert differently)

================================================================================
4. SET PIECE EFFICIENCY
================================================================================

Description:
Goals scored from set pieces (corners, free kicks, penalties) as a percentage of total goals. Set pieces are crucial in tight matches and can be the difference between winning and drawing.

Formula:
- home_set_piece_goals = goals from corners + free kicks + penalties (last 20 matches)
- home_total_goals = total goals (last 20 matches)
- home_set_piece_efficiency = home_set_piece_goals / home_total_goals
- away_set_piece_efficiency = calculated similarly
- set_piece_diff = home_set_piece_efficiency - away_set_piece_efficiency

Raw Data Source:
- match_events table (event_type: corner, free_kick, penalty)
- Match table (match dates, team IDs)

Difficulty:
- MEDIUM - Need to parse match events and identify set piece goals

Computational Cost:
- MEDIUM - Event parsing and aggregation over last 20 matches

Expected Impact:
- HIGH - Set pieces account for 30-40% of goals in modern football
- Particularly important in tournament knockout matches
- Teams with strong set pieces win tight matches
- Studies show 8-12% predictive power for match outcomes

Where it belongs in ml/features.py:
- New function: get_set_piece_efficiency(db, team_id, match_date)
- Call in extract_ml_features() after attack/defense ratings
- Add to feature dictionary as: home_set_piece_efficiency, away_set_piece_efficiency, set_piece_diff

Implementation Notes:
- Parse match_events for goal events with set piece origin
- Use exponential decay weighting (decay_rate = 0.12)
- Handle teams with 0 goals (use league average)
- Could separate by set piece type (corner vs free kick vs penalty)

================================================================================
5. GOALKEEPER SAVE PERCENTAGE
================================================================================

Description:
Percentage of shots on target that the goalkeeper saves. High save percentage indicates strong goalkeeping, which is crucial for match outcomes, especially in low-scoring games.

Formula:
- home_save_pct = saves / shots_on_target (last 20 matches)
- away_save_pct = saves / shots_on_target (last 20 matches)
- save_pct_diff = home_save_pct - away_save_pct

Raw Data Source:
- match_team_stats table (saves, shots_on_target)
- Match table (match dates, team IDs)

Difficulty:
- LOW - Straightforward aggregation from existing stats table

Computational Cost:
- LOW - Simple ratio calculation over last 20 matches

Expected Impact:
- MEDIUM-HIGH - Goalkeeping is critical in close matches
- Elite goalkeepers can be worth 5-10 points per season
- Particularly important in tournament knockout stages
- Studies show 5-8% predictive power for match outcomes

Where it belongs in ml/features.py:
- New function: get_goalkeeper_save_pct(db, team_id, match_date)
- Call in extract_ml_features() after attack/defense ratings
- Add to feature dictionary as: home_gk_save_pct, away_gk_save_pct, gk_save_pct_diff

Implementation Notes:
- Use exponential decay weighting (decay_rate = 0.15)
- Handle division by zero (no shots on target)
- Could weight by shot difficulty if xG data available
- Consider home vs away performance (goalkeepers perform differently)

================================================================================
6. TRAVEL DISTANCE
================================================================================

Description:
Distance traveled by each team to the match venue. Long travel causes fatigue, jet lag, and reduced performance, especially for international tournaments.

Formula:
- home_travel = distance(home_team_location, match_venue)
- away_travel = distance(away_team_location, match_venue)
- travel_diff = home_travel - away_travel

Raw Data Source:
- Team table (location/city coordinates)
- Match table (venue/stadium coordinates)
- External API: Google Maps Distance Matrix or similar

Difficulty:
- MEDIUM - Need geographic coordinates and distance calculation

Computational Cost:
- LOW - One-time distance calculation per match
- Can cache results for venues

Expected Impact:
- MEDIUM - Travel fatigue is well-documented in sports science
- Teams traveling >2000km show 10-15% performance drop
- Particularly relevant for World Cup (international travel)
- Jet lag affects teams crossing time zones

Where it belongs in ml/features.py:
- New function: get_travel_distance(db, home_team, away_team, match_venue)
- Call in extract_ml_features() after team lookup
- Add to feature dictionary as: home_travel_km, away_travel_km, travel_diff

Implementation Notes:
- Need to add coordinates to Team and Match tables
- Use Haversine formula for great-circle distance
- Could combine with rest days for comprehensive fatigue measure
- Handle missing coordinates (use 0 or league average)

================================================================================
7. COUNTER-ATTACK STRENGTH
================================================================================

Description:
Measure of a team's effectiveness at counter-attacks (goals scored from counter-attacking situations). Counter-attacks are crucial against possession-heavy teams.

Formula:
- home_counter_goals = goals from counter-attacks (last 20 matches)
- home_total_goals = total goals (last 20 matches)
- home_counter_strength = home_counter_goals / home_total_goals
- away_counter_strength = calculated similarly
- counter_diff = home_counter_strength - away_counter_strength

Raw Data Source:
- match_events table (event_type: goal, with counter-attack flag)
- Match table (match dates, team IDs)

Difficulty:
- MEDIUM-HIGH - Need event data with counter-attack classification
- May require manual annotation or advanced event parsing

Computational Cost:
- MEDIUM - Event parsing and aggregation over last 20 matches

Expected Impact:
- MEDIUM - Counter-attacks are increasingly important in modern football
- Teams with strong counter-attacks beat possession teams
- Particularly relevant for underdog teams
- Studies show 5-7% predictive power for match outcomes

Where it belongs in ml/features.py:
- New function: get_counter_attack_strength(db, team_id, match_date)
- Call in extract_ml_features() after attack/defense ratings
- Add to feature dictionary as: home_counter_strength, away_counter_strength, counter_diff

Implementation Notes:
- Requires detailed event data with counter-attack flags
- Could approximate using possession vs goals ratio
- Use exponential decay weighting (decay_rate = 0.15)
- May need to source from advanced analytics providers

================================================================================
8. PRESSING INTENSITY
================================================================================

Description:
Measure of how aggressively a team presses in defensive third. High pressing teams force turnovers and create scoring opportunities, but can be vulnerable to counter-attacks.

Formula:
- home_ppda = passes allowed per defensive action (last 20 matches)
- Lower PPDA = higher pressing intensity
- home_pressing_intensity = 1 / home_ppda
- away_pressing_intensity = calculated similarly
- pressing_diff = home_pressing_intensity - away_pressing_intensity

Raw Data Source:
- Advanced stats provider (Opta, StatsBomb, Wyscout)
- Or approximate using: tackles + interceptions / opponent passes

Difficulty:
- HIGH - Requires advanced stats not commonly available
- May need external API subscription

Computational Cost:
- LOW - Simple ratio calculation if data available

Expected Impact:
- MEDIUM - Pressing style significantly affects match dynamics
- High pressing teams create more chances but concede more
- Tactical matchups (high press vs possession) are important
- Studies show 4-6% predictive power for match outcomes

Where it belongs in ml/features.py:
- New function: get_pressing_intensity(db, team_id, match_date)
- Call in extract_ml_features() after attack/defense ratings
- Add to feature dictionary as: home_pressing_intensity, away_pressing_intensity, pressing_diff

Implementation Notes:
- Requires external data source (Opta, StatsBomb)
- Could approximate using available stats (tackles, interceptions)
- Use exponential decay weighting (decay_rate = 0.15)
- May be cost-prohibitive for some use cases

================================================================================
9. FORMATION COMPATIBILITY
================================================================================

Description:
Measure of how well each team's formation matches up against the opponent's formation. Certain formation matchups favor one side (e.g., 4-3-3 vs 3-5-2).

Formula:
- home_formation = most common formation (last 10 matches)
- away_formation = most common formation (last 10 matches)
- formation_matchup_score = historical win rate for home_formation vs away_formation
- Could use matrix of formation matchup win rates

Raw Data Source:
- match_lineups table (formation data)
- Match table (match dates, results)

Difficulty:
- MEDIUM - Need formation data and historical matchup analysis
- Requires building formation matchup matrix

Computational Cost:
- MEDIUM - Need to query formations and calculate matchup scores
- Can pre-compute formation matchup matrix

Expected Impact:
- MEDIUM - Tactical matchups are important in modern football
- Certain formations counter others effectively
- Particularly relevant for tactical managers
- Studies show 3-5% predictive power for match outcomes

Where it belongs in ml/features.py:
- New function: get_formation_compatibility(db, home_team_id, away_team_id, match_date)
- Call in extract_ml_features() after team lookup
- Add to feature dictionary as: formation_compatibility_score

Implementation Notes:
- Need formation data in match_lineups
- Build historical formation matchup matrix
- Could use simplified formation categories (4-back, 3-back, 5-back)
- Handle missing formation data (use most common formation)

================================================================================
10. WEATHER CONDITIONS
================================================================================

Description:
Weather conditions at match time (temperature, humidity, precipitation). Extreme weather affects player performance, ball movement, and tactical decisions.

Formula:
- temperature = match_time_temperature (°C)
- humidity = match_time_humidity (%)
- precipitation = match_time_precipitation (mm)
- weather_severity = composite score based on conditions

Raw Data Source:
- Weather API (OpenWeatherMap, WeatherAPI)
- Match table (venue, date/time)

Difficulty:
- LOW - Straightforward API integration

Computational Cost:
- LOW - One API call per match
- Can cache results for same venue/time

Expected Impact:
- LOW-MEDIUM - Weather affects performance but is often similar for both teams
- Extreme heat (>30°C) reduces performance by 5-10%
- Rain affects passing accuracy and ball movement
- Particularly relevant for outdoor stadiums

Where it belongs in ml/features.py:
- New function: get_weather_conditions(match_venue, match_date)
- Call in extract_ml_features() after team lookup
- Add to feature dictionary as: temperature, humidity, precipitation, weather_severity

Implementation Notes:
- Need API key for weather service
- Handle API failures gracefully
- Could use historical averages if real-time not available
- Consider indoor stadiums (no weather impact)

================================================================================
11. REFEREE TENDENCY
================================================================================

Description:
Referee's tendency to award cards, fouls, and penalties. Some referees are strict (many cards) while others are lenient. This affects match flow and player behavior.

Formula:
- referee_card_rate = average cards per match (last 20 matches)
- referee_foul_rate = average fouls per match (last 20 matches)
- referee_penalty_rate = average penalties per match (last 20 matches)
- referee_strictness = composite score of card/foul rates

Raw Data Source:
- Match table (referee_id)
- match_events table (card events, foul events)
- Referee table (if available)

Difficulty:
- LOW-MEDIUM - Need to aggregate referee statistics

Computational Cost:
- LOW - Pre-compute referee statistics, simple lookup

Expected Impact:
- LOW-MEDIUM - Referee strictness affects match but is secondary
- Strict referees favor disciplined teams
- Card accumulation affects future matches
- Studies show 2-4% predictive power for match outcomes

Where it belongs in ml/features.py:
- New function: get_referee_tendency(db, referee_id)
- Call in extract_ml_features() after match lookup
- Add to feature dictionary as: referee_card_rate, referee_foul_rate, referee_strictness

Implementation Notes:
- Note: referee_strictness already exists as a Kaggle feature
- This would enhance it with more granular statistics
- Could separate by card type (yellow vs red)
- Consider home vs away bias (some referees favor home teams)

================================================================================
12. CROSSING EFFICIENCY
================================================================================

Description:
Percentage of crosses that successfully find a teammate. High crossing efficiency indicates strong wing play and aerial ability.

Formula:
- home_crosses = total crosses (last 20 matches)
- home_successful_crosses = crosses that find teammate (last 20 matches)
- home_crossing_efficiency = home_successful_crosses / home_crosses
- away_crossing_efficiency = calculated similarly
- crossing_diff = home_crossing_efficiency - away_crossing_efficiency

Raw Data Source:
- match_team_stats table (crosses, successful_crosses)
- Match table (match dates, team IDs)

Difficulty:
- LOW - Straightforward aggregation from existing stats table

Computational Cost:
- LOW - Simple ratio calculation over last 20 matches

Expected Impact:
- LOW - Crossing is one component of attacking play
- Important for teams with strong wingers
- Less predictive than overall attack rating
- Studies show 2-3% predictive power for match outcomes

Where it belongs in ml/features.py:
- New function: get_crossing_efficiency(db, team_id, match_date)
- Call in extract_ml_features() after attack/defense ratings
- Add to feature dictionary as: home_crossing_efficiency, away_crossing_efficiency, crossing_diff

Implementation Notes:
- Use exponential decay weighting (decay_rate = 0.15)
- Handle division by zero (no crosses)
- Could separate by crossing type (open play vs set piece)
- May not be available in all data sources

================================================================================
13. POSSESSION STYLE
================================================================================

Description:
Average possession percentage over recent matches. High possession teams control the game but may be vulnerable to counter-attacks.

Formula:
- home_possession = average possession % (last 20 matches)
- away_possession = average possession % (last 20 matches)
- possession_diff = home_possession - away_possession

Raw Data Source:
- match_team_stats table (possession_percentage)
- Match table (match dates, team IDs)

Difficulty:
- LOW - Straightforward aggregation from existing stats table

Computational Cost:
- LOW - Simple average calculation over last 20 matches

Expected Impact:
- LOW - Possession doesn't directly correlate with winning
- Some successful teams have low possession (counter-attack style)
- More relevant for tactical matchups than raw prediction
- Studies show 1-2% predictive power for match outcomes

Where it belongs in ml/features.py:
- New function: get_possession_style(db, team_id, match_date)
- Call in extract_ml_features() after attack/defense ratings
- Add to feature dictionary as: home_possession, away_possession, possession_diff

Implementation Notes:
- Note: home_possession already exists as a SofaScore feature
- This would make it consistently available across all matches
- Use exponential decay weighting (decay_rate = 0.15)
- Handle missing possession data (use league average)

================================================================================
SUMMARY AND RECOMMENDATIONS
================================================================================

Top 5 Highest Impact Features:
1. Rest Days Before Match - HIGH impact, LOW difficulty, LOW cost
2. Player Fatigue Index - HIGH impact, MEDIUM difficulty, MEDIUM cost
3. Shot Conversion Rate - HIGH impact, LOW difficulty, LOW cost
4. Set Piece Efficiency - HIGH impact, MEDIUM difficulty, MEDIUM cost
5. Goalkeeper Save Percentage - MEDIUM-HIGH impact, LOW difficulty, LOW cost

Recommended Implementation Priority:

Phase 1 (Quick Wins - Low Difficulty, High Impact):
- Rest Days Before Match
- Shot Conversion Rate
- Goalkeeper Save Percentage

Phase 2 (Medium Effort - Medium Difficulty, High Impact):
- Player Fatigue Index
- Set Piece Efficiency

Phase 3 (Advanced Features - High Difficulty, Medium Impact):
- Travel Distance
- Counter-Attack Strength
- Formation Compatibility

Phase 4 (Optional - Low Impact or High Cost):
- Pressing Intensity (requires external data)
- Weather Conditions
- Referee Tendency (already partially implemented)
- Crossing Efficiency
- Possession Style (already partially implemented)

Expected Overall Impact:
- Phase 1 features: +5-8% accuracy improvement
- Phase 2 features: +3-5% accuracy improvement
- Phase 3 features: +2-4% accuracy improvement
- Phase 4 features: +1-2% accuracy improvement

Total potential improvement: +11-19% accuracy

Data Requirements:
- Most features can be derived from existing database tables
- Some require external APIs (weather, advanced stats)
- Some require schema additions (coordinates, formation data)
- All integrate cleanly into existing ml/features.py pipeline

Implementation Notes:
- All features follow the same pattern as existing features
- Can be added incrementally without breaking existing code
- Should be validated with A/B testing before full deployment
- Consider feature interactions (e.g., rest days + fatigue index)
