import pandas as pd
import numpy as np
import pickle

# Load datasets
df_wc = pd.read_csv('ml/dataset_world_cup.csv')
df_goals = pd.read_csv('ml/dataset_goals.csv')

# Load models
with open('models/world_cup_predictor.pkl', 'rb') as f:
    wc_bundle = pickle.load(f)
wc_model = wc_bundle['model']
wc_features = wc_bundle['features']

with open('models/goal_predictor.pkl', 'rb') as f:
    goal_bundle = pickle.load(f)
home_model = goal_bundle['home_model']
away_model = goal_bundle['away_model']
goal_features = goal_bundle['features']

# Feature definitions from features.py
ALL_FEATURES_FROM_EXTRACT = {
    # Phase 1 core
    'elo_diff': 'get_team_elo() - TeamElo database',
    'fifa_diff': 'Team.fifa_ranking - Team database',
    'form_diff': 'get_team_recent_stats() - Match database',
    'gs_diff': 'get_team_recent_stats() - Match database',
    'gc_diff': 'get_team_recent_stats() - Match database',
    'mv_diff': 'Team.squad_market_value - Team database',
    'inj_diff': 'Injury.player_market_value - Injury database',
    'susp_diff': 'Suspension.player_market_value - Suspension database',
    'home_adv': 'Competition code check - Competition database',
    'h2h_factor': 'Match history query - Match database',
    # Phase 2 player intelligence
    'available_squad_diff': 'squad_market_value - injuries - suspensions - Team/Injury/Suspension databases',
    'availability_pct_diff': 'available_squad / squad_market_value - calculated',
    'starting_xi_value_diff': 'top 11 available players - NationalTeamPlayer database',
    'missing_star_players_diff': 'injured/suspended players > 50M - Injury/Suspension/NationalTeamPlayer databases',
    'match_stage_weight': 'STAGE_WEIGHTS dict - Match.stage field',
    # Phase 3 structural
    'home_elo_momentum': 'get_elo_momentum() - TeamElo/Match databases',
    'away_elo_momentum': 'get_elo_momentum() - TeamElo/Match databases',
    'elo_momentum_diff': 'home_elo_momentum - away_elo_momentum - calculated',
    'home_strength_of_schedule': 'get_strength_of_schedule() - TeamElo/Match databases',
    'away_strength_of_schedule': 'get_strength_of_schedule() - TeamElo/Match databases',
    'strength_of_schedule_diff': 'home_sos - away_sos - calculated',
    'world_cup_matches_played_diff': 'get_tournament_experience() - Match/Competition databases',
    'major_tournament_matches_diff': 'get_tournament_experience() - Match/Competition databases',
    'knockout_matches_diff': 'get_tournament_experience() - Match/Competition databases',
    # Phase 4.5 Advanced Goal Intelligence
    'home_attack_rating': 'get_attack_rating() - Match database',
    'away_attack_rating': 'get_attack_rating() - Match database',
    'attack_rating_diff': 'home_attack - away_attack - calculated',
    'home_defence_rating': 'get_defence_rating() - Match database',
    'away_defence_rating': 'get_defence_rating() - Match database',
    'defence_rating_diff': 'home_defence - away_defence - calculated',
    'home_clean_sheet_rate': 'get_clean_sheet_rate() - Match database',
    'away_clean_sheet_rate': 'get_clean_sheet_rate() - Match database',
    'clean_sheet_rate_diff': 'home_clean - away_clean - calculated',
    'home_btts_rate': 'get_btts_rate() - Match database',
    'away_btts_rate': 'get_btts_rate() - Match database',
    'btts_rate_diff': 'home_btts - away_btts - calculated',
    # Injury & Suspension counts
    'home_injury_count': 'len(Injury.query) - Injury database',
    'away_injury_count': 'len(Injury.query) - Injury database',
    'home_suspension_count': 'len(Suspension.query) - Suspension database',
    'away_suspension_count': 'len(Suspension.query) - Suspension database',
    'home_injury_market_value_loss': 'sum(Injury.player_market_value) - Injury database',
    'away_injury_market_value_loss': 'sum(Injury.player_market_value) - Injury database',
    # Standings features
    'home_group_position': 'Standing.position - Standing database',
    'away_group_position': 'Standing.position - Standing database',
    'group_position_diff': 'home_position - away_position - calculated',
    'home_points': 'Standing.points - Standing database',
    'away_points': 'Standing.points - Standing database',
    'points_diff': 'home_points - away_points - calculated',
    'goal_difference_diff': 'Standing.goals_difference - Standing database',
    # Betting odds features
    'home_implied_probability': 'BookmakerOdds.home_odds - BookmakerOdds database',
    'draw_implied_probability': 'BookmakerOdds.draw_odds - BookmakerOdds database',
    'away_implied_probability': 'BookmakerOdds.away_odds - BookmakerOdds database',
    # Live match features
    'current_minute': 'Match.current_minute - Match database',
    'time_remaining': '90 - current_minute - calculated',
    'current_score_diff': 'Match.current_home_score - Match.current_away_score - Match database',
    'home_red_cards': 'Match.home_red_cards - Match database',
    'away_red_cards': 'Match.away_red_cards - Match database',
    'red_card_diff': 'home_red - away_red - calculated',
    # SofaScore features
    'home_avg_rating': 'PlayerMatchPerformance.sofa_score_rating - PlayerMatchPerformance database',
    'away_avg_rating': 'PlayerMatchPerformance.sofa_score_rating - PlayerMatchPerformance database',
    'avg_rating_diff': 'home_avg - away_avg - calculated',
    'home_possession': 'MatchStatistic.home_possession - MatchStatistic database',
    'away_possession': 'MatchStatistic.away_possession - MatchStatistic database',
    'possession_diff': 'home_poss - away_poss - calculated',
    'home_expected_goals': 'MatchStatistic.home_expected_goals - MatchStatistic database',
    'away_expected_goals': 'MatchStatistic.away_expected_goals - MatchStatistic database',
    'expected_goals_diff': 'home_xg - away_xg - calculated',
    # Intelligence Service features
    'home_attacking_strength': 'IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py',
    'away_attacking_strength': 'IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py',
    'attacking_strength_diff': 'home_attack - away_attack - calculated',
    'home_defensive_strength': 'IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py',
    'away_defensive_strength': 'IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py',
    'defensive_strength_diff': 'home_defense - away_defense - calculated',
    'home_midfield_control': 'IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py',
    'away_midfield_control': 'IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py',
    'midfield_control_diff': 'home_midfield - away_midfield - calculated',
    'home_goalkeeper_performance': 'IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py',
    'away_goalkeeper_performance': 'IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py',
    'goalkeeper_performance_diff': 'home_gk - away_gk - calculated',
    'home_passing_dominance': 'IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py',
    'away_passing_dominance': 'IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py',
    'passing_dominance_diff': 'home_passing - away_passing - calculated',
    'home_pressing_intensity': 'IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py',
    'away_pressing_intensity': 'IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py',
    'pressing_intensity_diff': 'home_pressing - away_pressing - calculated',
    'home_set_piece_threat': 'IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py',
    'away_set_piece_threat': 'IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py',
    'set_piece_threat_diff': 'home_set_piece - away_set_piece - calculated',
    'home_discipline_score': 'IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py',
    'away_discipline_score': 'IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py',
    'discipline_score_diff': 'home_discipline - away_discipline - calculated',
    'home_fatigue_score': 'IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py',
    'away_fatigue_score': 'IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py',
    'fatigue_score_diff': 'home_fatigue - away_fatigue - calculated',
    'home_substitution_impact': 'IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py',
    'away_substitution_impact': 'IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py',
    'substitution_impact_diff': 'home_sub - away_sub - calculated',
    'home_player_availability_score': 'IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py',
    'away_player_availability_score': 'IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py',
    'availability_score_diff': 'home_avail - away_avail - calculated',
    'home_injury_impact': 'IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py',
    'away_injury_impact': 'IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py',
    'injury_impact_diff': 'home_inj_impact - away_inj_impact - calculated',
    'home_suspension_impact': 'IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py',
    'away_suspension_impact': 'IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py',
    'suspension_impact_diff': 'home_susp_impact - away_susp_impact - calculated',
    'home_formation_stability': 'IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py',
    'away_formation_stability': 'IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py',
    'formation_stability_diff': 'home_formation - away_formation - calculated',
    'home_momentum_score': 'IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py',
    'away_momentum_score': 'IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py',
    'momentum_score_diff': 'home_momentum - away_momentum - calculated',
    'home_goalkeeper_strength': 'IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py',
    'away_goalkeeper_strength': 'IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py',
    'goalkeeper_strength_diff': 'home_gk_str - away_gk_str - calculated',
    'home_passing_strength': 'IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py',
    'away_passing_strength': 'IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py',
    'passing_strength_diff': 'home_pass_str - away_pass_str - calculated',
    'home_recent_form': 'IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py',
    'away_recent_form': 'IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py',
    'recent_form_diff': 'home_recent - away_recent - calculated',
    'home_aerial_dominance': 'IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py',
    'away_aerial_dominance': 'IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py',
    'aerial_dominance_diff': 'home_aerial - away_aerial - calculated',
    'home_pressing_strength': 'IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py',
    'away_pressing_strength': 'IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py',
    'pressing_strength_diff': 'home_press_str - away_press_str - calculated',
    'home_defensive_stability': 'IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py',
    'away_defensive_stability': 'IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py',
    'defensive_stability_diff': 'home_def_stab - away_def_stab - calculated',
    'home_attacking_efficiency': 'IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py',
    'away_attacking_efficiency': 'IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py',
    'attacking_efficiency_diff': 'home_att_eff - away_att_eff - calculated',
    'home_finishing_quality': 'IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py',
    'away_finishing_quality': 'IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py',
    'finishing_quality_diff': 'home_finish - away_finish - calculated',
    'home_set_piece_strength': 'IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py',
    'away_set_piece_strength': 'IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py',
    'set_piece_strength_diff': 'home_set_str - away_set_str - calculated',
    'home_squad_availability': 'IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py',
    'away_squad_availability': 'IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py',
    'squad_availability_diff': 'home_squad_avail - away_squad_avail - calculated',
    'home_tactical_stability': 'IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py',
    'away_tactical_stability': 'IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py',
    'tactical_stability_diff': 'home_tactical - away_tactical - calculated',
    'confidence_score': 'IntelligenceService.calculate_match_intelligence() - services/intelligence_service.py',
    # Kaggle features
    'home_kaggle_attack_rating': 'calculate_team_attack_rating() - ml/kaggle_features.py',
    'away_kaggle_attack_rating': 'calculate_team_attack_rating() - ml/kaggle_features.py',
    'kaggle_attack_rating_diff': 'home_kaggle_attack - away_kaggle_attack - calculated',
    'home_kaggle_defense_rating': 'calculate_team_defense_rating() - ml/kaggle_features.py',
    'away_kaggle_defense_rating': 'calculate_team_defense_rating() - ml/kaggle_features.py',
    'kaggle_defense_rating_diff': 'home_kaggle_defense - away_kaggle_defense - calculated',
    'home_kaggle_discipline_score': 'calculate_discipline_score() - ml/kaggle_features.py',
    'away_kaggle_discipline_score': 'calculate_discipline_score() - ml/kaggle_features.py',
    'kaggle_discipline_score_diff': 'home_kaggle_discipline - away_kaggle_discipline - calculated',
    'home_kaggle_suspension_risk': 'calculate_suspension_risk() - ml/kaggle_features.py',
    'away_kaggle_suspension_risk': 'calculate_suspension_risk() - ml/kaggle_features.py',
    'kaggle_suspension_risk_diff': 'home_kaggle_susp - away_kaggle_susp - calculated',
    'home_kaggle_starting_xi_strength': 'calculate_starting_xi_strength() - ml/kaggle_features.py',
    'away_kaggle_starting_xi_strength': 'calculate_starting_xi_strength() - ml/kaggle_features.py',
    'kaggle_starting_xi_strength_diff': 'home_kaggle_xi - away_kaggle_xi - calculated',
    'home_kaggle_bench_strength': 'calculate_bench_strength() - ml/kaggle_features.py',
    'away_kaggle_bench_strength': 'calculate_bench_strength() - ml/kaggle_features.py',
    'kaggle_bench_strength_diff': 'home_kaggle_bench - away_kaggle_bench - calculated',
    'referee_strictness': 'calculate_referee_strictness() - ml/kaggle_features.py',
}

print('=== FEATURE PIPELINE AUDIT ===\n')

audit_results = []

for feature, source in ALL_FEATURES_FROM_EXTRACT.items():
    # Check if feature reaches dataset_world_cup.csv
    in_wc = feature in df_wc.columns
    # Check if feature reaches dataset_goals.csv
    in_goals = feature in df_goals.columns
    
    # Get statistics from dataset_world_cup.csv
    if in_wc:
        series = df_wc[feature]
        wc_min = series.min()
        wc_max = series.max()
        wc_mean = series.mean()
        wc_std = series.std()
        wc_zero_count = (series == 0).sum()
        wc_non_zero_count = (series != 0).sum()
        wc_missing_count = series.isna().sum()
        wc_total = len(df_wc)
        
        if wc_missing_count == wc_total:
            wc_status = 'MISSING'
        elif wc_std == 0:
            wc_status = 'CONSTANT'
        elif wc_zero_count > wc_total * 0.9:
            wc_status = 'MOSTLY_ZERO'
        elif wc_zero_count == wc_total:
            wc_status = 'ALWAYS_ZERO'
        else:
            wc_status = 'HEALTHY'
    else:
        wc_status = 'NOT_IN_DATASET'
        wc_min = wc_max = wc_mean = wc_std = wc_zero_count = wc_non_zero_count = wc_missing_count = wc_total = None
    
    # Get statistics from dataset_goals.csv
    if in_goals:
        series = df_goals[feature]
        goals_min = series.min()
        goals_max = series.max()
        goals_mean = series.mean()
        goals_std = series.std()
        goals_zero_count = (series == 0).sum()
        goals_non_zero_count = (series != 0).sum()
        goals_missing_count = series.isna().sum()
        goals_total = len(df_goals)
        
        if goals_missing_count == goals_total:
            goals_status = 'MISSING'
        elif goals_std == 0:
            goals_status = 'CONSTANT'
        elif goals_zero_count > goals_total * 0.9:
            goals_status = 'MOSTLY_ZERO'
        elif goals_zero_count == goals_total:
            goals_status = 'ALWAYS_ZERO'
        else:
            goals_status = 'HEALTHY'
    else:
        goals_status = 'NOT_IN_DATASET'
        goals_min = goals_max = goals_mean = goals_std = goals_zero_count = goals_non_zero_count = goals_missing_count = goals_total = None
    
    # Check if feature reaches XGBoost training
    in_wc_training = feature in wc_features
    in_goals_training = feature in goal_features
    
    # Get feature importance if available
    wc_importance = None
    if in_wc_training:
        idx = wc_features.index(feature)
        wc_importance = wc_model.feature_importances_[idx]
    
    goals_home_importance = None
    goals_away_importance = None
    if in_goals_training:
        idx = goal_features.index(feature)
        goals_home_importance = home_model.feature_importances_[idx]
        goals_away_importance = away_model.feature_importances_[idx]
    
    audit_results.append({
        'feature': feature,
        'source': source,
        'wc_status': wc_status,
        'wc_min': wc_min,
        'wc_max': wc_max,
        'wc_mean': wc_mean,
        'wc_std': wc_std,
        'wc_zero_count': wc_zero_count,
        'wc_non_zero_count': wc_non_zero_count,
        'wc_missing_count': wc_missing_count,
        'wc_total': wc_total,
        'goals_status': goals_status,
        'goals_min': goals_min,
        'goals_max': goals_max,
        'goals_mean': goals_mean,
        'goals_std': goals_std,
        'goals_zero_count': goals_zero_count,
        'goals_non_zero_count': goals_non_zero_count,
        'goals_missing_count': goals_missing_count,
        'goals_total': goals_total,
        'in_wc_training': in_wc_training,
        'in_goals_training': in_goals_training,
        'wc_importance': wc_importance,
        'goals_home_importance': goals_home_importance,
        'goals_away_importance': goals_away_importance,
    })

# Print detailed audit
for result in audit_results:
    print(f"\n{'='*100}")
    print(f"Feature: {result['feature']}")
    print(f"Source: {result['source']}")
    print(f"\nDataset World Cup:")
    print(f"  Status: {result['wc_status']}")
    if result['wc_status'] != 'NOT_IN_DATASET':
        print(f"  Min: {result['wc_min']:.4f}, Max: {result['wc_max']:.4f}, Mean: {result['wc_mean']:.4f}, Std: {result['wc_std']:.4f}")
        print(f"  Zero: {result['wc_zero_count']}, NonZero: {result['wc_non_zero_count']}, Missing: {result['wc_missing_count']}/{result['wc_total']}")
    print(f"\nDataset Goals:")
    print(f"  Status: {result['goals_status']}")
    if result['goals_status'] != 'NOT_IN_DATASET':
        print(f"  Min: {result['goals_min']:.4f}, Max: {result['goals_max']:.4f}, Mean: {result['goals_mean']:.4f}, Std: {result['goals_std']:.4f}")
        print(f"  Zero: {result['goals_zero_count']}, NonZero: {result['goals_non_zero_count']}, Missing: {result['goals_missing_count']}/{result['goals_total']}")
    print(f"\nTraining:")
    print(f"  In WC Training: {result['in_wc_training']}")
    if result['in_wc_training']:
        print(f"  WC Importance: {result['wc_importance']:.6f}")
    print(f"  In Goals Training: {result['in_goals_training']}")
    if result['in_goals_training']:
        print(f"  Goals Home Importance: {result['goals_home_importance']:.6f}")
        print(f"  Goals Away Importance: {result['goals_away_importance']:.6f}")

print(f"\n{'='*100}")
print("SUMMARY STATISTICS")
print(f"{'='*100}")

# Count by status
wc_status_counts = {}
goals_status_counts = {}
for result in audit_results:
    wc_status_counts[result['wc_status']] = wc_status_counts.get(result['wc_status'], 0) + 1
    goals_status_counts[result['goals_status']] = goals_status_counts.get(result['goals_status'], 0) + 1

print("\nDataset World Cup Status Counts:")
for status, count in sorted(wc_status_counts.items()):
    print(f"  {status}: {count}")

print("\nDataset Goals Status Counts:")
for status, count in sorted(goals_status_counts.items()):
    print(f"  {status}: {count}")

# Count training usage
wc_training_count = sum(1 for r in audit_results if r['in_wc_training'])
goals_training_count = sum(1 for r in audit_results if r['in_goals_training'])

print(f"\nTraining Usage:")
print(f"  In WC Training: {wc_training_count}/{len(audit_results)}")
print(f"  In Goals Training: {goals_training_count}/{len(audit_results)}")

# Save results
import json
with open('feature_audit_results.json', 'w') as f:
    json.dump(audit_results, f, indent=2, default=str)

print(f"\nSaved detailed results to feature_audit_results.json")
