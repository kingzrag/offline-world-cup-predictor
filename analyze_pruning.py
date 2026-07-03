import pickle
import pandas as pd
from ml.train_world_cup_model import FEATURES as WC_FEATURES
from ml.train_goal_model import GOAL_FEATURES

# Load models to get feature importance
with open('models/world_cup_predictor.pkl', 'rb') as f:
    wc_bundle = pickle.load(f)
wc_model = wc_bundle['model']
wc_feature_names = wc_bundle.get('feature_names', wc_bundle.get('features', []))
wc_importance = dict(zip(wc_feature_names, wc_model.feature_importances_))

with open('models/goal_predictor.pkl', 'rb') as f:
    goal_bundle = pickle.load(f)
goal_home_model = goal_bundle['home_model']
goal_away_model = goal_bundle['away_model']
goal_feature_names = goal_bundle.get('feature_names', goal_bundle.get('features', []))
goal_home_importance = dict(zip(goal_feature_names, goal_home_model.feature_importances_))
goal_away_importance = dict(zip(goal_feature_names, goal_away_model.feature_importances_))

# Load feature stats
df_wc = pd.read_csv('ml/dataset_world_cup.csv')
df_goals = pd.read_csv('ml/dataset_goals.csv')

# Feature categories
LIVE_FEATURES = [
    'current_minute', 'time_remaining', 'current_score_diff',
    'home_red_cards', 'away_red_cards', 'red_card_diff',
    'home_avg_rating', 'away_avg_rating', 'home_possession',
    'away_possession', 'home_xg', 'away_xg', 'possession_diff', 'xg_diff'
]

SOFASCORE_FEATURES = [
    'home_avg_rating', 'away_avg_rating', 'home_possession',
    'away_possession', 'home_xg', 'away_xg', 'possession_diff', 'xg_diff'
]

BETTING_FEATURES = [
    'home_implied_probability', 'draw_implied_probability', 'away_implied_probability'
]

KAGGLE_FEATURES = [
    'home_kaggle_attack_rating', 'away_kaggle_attack_rating', 'kaggle_attack_rating_diff',
    'home_kaggle_defense_rating', 'away_kaggle_defense_rating', 'kaggle_defense_rating_diff',
    'home_kaggle_discipline_score', 'away_kaggle_discipline_score', 'kaggle_discipline_score_diff',
    'home_kaggle_suspension_risk', 'away_kaggle_suspension_risk', 'kaggle_suspension_risk_diff',
    'home_kaggle_starting_xi_strength', 'away_kaggle_starting_xi_strength', 'kaggle_starting_xi_strength_diff',
    'home_kaggle_bench_strength', 'away_kaggle_bench_strength', 'kaggle_bench_strength_diff',
    'referee_strictness'
]

INTELLIGENCE_FEATURES = [
    'home_goalkeeper_strength', 'away_goalkeeper_strength', 'goalkeeper_strength_diff',
    'home_passing_strength', 'away_passing_strength', 'passing_strength_diff',
    'home_recent_form', 'away_recent_form', 'recent_form_diff',
    'home_aerial_dominance', 'away_aerial_dominance', 'aerial_dominance_diff',
    'home_pressing_strength', 'away_pressing_strength', 'pressing_strength_diff',
    'home_defensive_stability', 'away_defensive_stability', 'defensive_stability_diff',
    'home_attacking_efficiency', 'away_attacking_efficiency', 'attacking_efficiency_diff',
    'home_finishing_quality', 'away_finishing_quality', 'finishing_quality_diff',
    'home_set_piece_strength', 'away_set_piece_strength', 'set_piece_strength_diff',
    'home_squad_availability', 'away_squad_availability', 'squad_availability_diff',
    'home_tactical_stability', 'away_tactical_stability', 'tactical_stability_diff',
    'confidence_score'
]

def analyze_feature(feature, df, importance_dict, model_name):
    """Analyze a single feature for pruning eligibility."""
    if feature not in df.columns:
        return {
            'feature': feature,
            'in_dataset': False,
            'constant': None,
            'always_zero': None,
            'importance': 0.0,
            'category': 'missing',
            'removable': False,
            'reason': 'Not in dataset'
        }
    
    values = df[feature].dropna()
    if len(values) == 0:
        return {
            'feature': feature,
            'in_dataset': True,
            'constant': None,
            'always_zero': None,
            'importance': importance_dict.get(feature, 0.0),
            'category': 'empty',
            'removable': False,
            'reason': 'All values are NaN'
        }
    
    is_constant = values.std() == 0
    is_always_zero = (values == 0).all()
    importance = importance_dict.get(feature, 0.0)
    
    # Determine category
    category = 'other'
    if feature in LIVE_FEATURES:
        category = 'live'
    elif feature in SOFASCORE_FEATURES:
        category = 'sofascore'
    elif feature in BETTING_FEATURES:
        category = 'betting'
    elif feature in KAGGLE_FEATURES:
        category = 'kaggle'
    elif feature in INTELLIGENCE_FEATURES:
        category = 'intelligence'
    
    # Pruning eligibility
    removable = False
    reason = 'Not eligible for removal'
    
    # Check if it's a protected category
    if category in ['live', 'sofascore', 'betting', 'kaggle', 'intelligence']:
        reason = f'Protected category: {category}'
    # Check if it has importance
    elif importance > 0:
        reason = f'Has XGBoost importance: {importance:.4f}'
    # Check if it's not constant
    elif not is_constant:
        reason = f'Not constant (std: {values.std():.4f})'
    # Check if it's not always zero
    elif not is_always_zero:
        reason = f'Not always zero (non-zero count: {(values != 0).sum()})'
    # All conditions met - removable
    else:
        removable = True
        reason = 'Constant, always zero, no importance, not protected'
    
    return {
        'feature': feature,
        'in_dataset': True,
        'constant': is_constant,
        'always_zero': is_always_zero,
        'importance': importance,
        'category': category,
        'removable': removable,
        'reason': reason,
        'std': values.std(),
        'non_zero_count': (values != 0).sum(),
        'total_count': len(values)
    }

# Analyze World Cup features
print("="*80)
print("WORLD CUP MODEL FEATURE ANALYSIS")
print("="*80)

wc_analysis = []
for feature in WC_FEATURES:
    analysis = analyze_feature(feature, df_wc, wc_importance, 'world_cup')
    wc_analysis.append(analysis)

removable_wc = [a for a in wc_analysis if a['removable']]
print(f"\nRemovable features: {len(removable_wc)}")
for a in removable_wc:
    print(f"  - {a['feature']}: {a['reason']}")

print(f"\nProtected zero-importance features:")
protected_zero = [a for a in wc_analysis if a['importance'] == 0 and not a['removable']]
for a in protected_zero:
    print(f"  - {a['feature']}: {a['reason']}")

# Analyze Goal features
print("\n" + "="*80)
print("GOAL MODEL FEATURE ANALYSIS")
print("="*80)

goal_analysis = []
for feature in GOAL_FEATURES:
    analysis = analyze_feature(feature, df_goals, goal_home_importance, 'goal')
    goal_analysis.append(analysis)

removable_goal = [a for a in goal_analysis if a['removable']]
print(f"\nRemovable features: {len(removable_goal)}")
for a in removable_goal:
    print(f"  - {a['feature']}: {a['reason']}")

print(f"\nProtected zero-importance features:")
protected_zero_goal = [a for a in goal_analysis if a['importance'] == 0 and not a['removable']]
for a in protected_zero_goal:
    print(f"  - {a['feature']}: {a['reason']}")

# Summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print(f"World Cup removable features: {len(removable_wc)}")
print(f"Goal removable features: {len(removable_goal)}")

# Get union of removable features
all_removable = set([a['feature'] for a in removable_wc] + [a['feature'] for a in removable_goal])
print(f"Total unique removable features: {len(all_removable)}")
print(f"Removable features: {sorted(all_removable)}")
