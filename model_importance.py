import pickle
import os

# Load world cup predictor model
print('=== WORLD CUP PREDICTOR MODEL ===')
wc_model_path = 'models/world_cup_predictor.pkl'
if os.path.exists(wc_model_path):
    with open(wc_model_path, 'rb') as f:
        wc_bundle = pickle.load(f)
    
    wc_model = wc_bundle['model']
    wc_features = wc_bundle['features']
    wc_metrics = wc_bundle.get('metrics', {})
    
    print(f'Features used: {len(wc_features)}')
    print(f'Features list:')
    for i, feat in enumerate(wc_features, 1):
        print(f'  {i:2d}. {feat}')
    
    print(f'\nMetrics: {wc_metrics}')
    
    print(f'\nFeature Importance (Gain):')
    importances = wc_model.feature_importances_
    ranked = sorted(zip(wc_features, importances), key=lambda x: x[1], reverse=True)
    for i, (feat, imp) in enumerate(ranked, 1):
        bar = '█' * int(imp * 200)
        print(f'  {i:2d}. {feat:40s} {imp:.6f}  {bar}')
else:
    print('World cup predictor model not found')

print('\n' + '='*100)
print('=== GOAL PREDICTOR MODEL ===')
goal_model_path = 'models/goal_predictor.pkl'
if os.path.exists(goal_model_path):
    with open(goal_model_path, 'rb') as f:
        goal_bundle = pickle.load(f)
    
    home_model = goal_bundle['home_model']
    away_model = goal_bundle['away_model']
    goal_features = goal_bundle['features']
    goal_metrics = goal_bundle.get('metrics', {})
    
    print(f'Features used: {len(goal_features)}')
    print(f'Features list:')
    for i, feat in enumerate(goal_features, 1):
        print(f'  {i:2d}. {feat}')
    
    print(f'\nMetrics: {goal_metrics}')
    
    print(f'\nFeature Importance - Home Goals Model:')
    home_imp = home_model.feature_importances_
    ranked_home = sorted(zip(goal_features, home_imp), key=lambda x: x[1], reverse=True)
    for i, (feat, imp) in enumerate(ranked_home, 1):
        bar = '█' * int(imp * 100)
        print(f'  {i:2d}. {feat:40s} {imp:.6f}  {bar}')
    
    print(f'\nFeature Importance - Away Goals Model:')
    away_imp = away_model.feature_importances_
    ranked_away = sorted(zip(goal_features, away_imp), key=lambda x: x[1], reverse=True)
    for i, (feat, imp) in enumerate(ranked_away, 1):
        bar = '█' * int(imp * 100)
        print(f'  {i:2d}. {feat:40s} {imp:.6f}  {bar}')
else:
    print('Goal predictor model not found')
