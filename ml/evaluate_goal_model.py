import os, sys, pickle, random
import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from math import sqrt

# Ensure project root is in path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(PROJECT_ROOT)

# Load dataset
DATASET_PATH = os.path.join(os.path.dirname(__file__), 'dataset_goals.csv')
if not os.path.exists(DATASET_PATH):
    raise FileNotFoundError(f'Dataset not found at {DATASET_PATH}')

df = pd.read_csv(DATASET_PATH)
# Features used for training (match training script expectations)
FEATURES = [
    "elo_diff",
    "fifa_diff",
    "form_diff",
    "gs_diff",
    "gc_diff",
    "inj_diff",
    "susp_diff",
    "available_squad_diff",
    "starting_xi_value_diff",
    "missing_star_players_diff",
    "elo_momentum_diff",
    "strength_of_schedule_diff",
    "home_adv",
    "h2h_factor",
    "match_stage_weight",
]

X = df[FEATURES].values
Y_home = df['home_score'].values
Y_away = df['away_score'].values

# Train-test split (same random_state as training script)
from sklearn.model_selection import train_test_split
X_train, X_test, y_home_train, y_home_test, y_away_train, y_away_test = train_test_split(
    X, Y_home, Y_away, test_size=0.2, random_state=42, stratify=None
)

# Load model bundle
MODEL_PATH = os.path.join(os.path.dirname(PROJECT_ROOT), 'models', 'goal_predictor.pkl')
with open(MODEL_PATH, 'rb') as f:
    bundle = pickle.load(f)
# Expected keys
home_model = bundle.get('home_model') or bundle.get('model') or bundle.get('home_regressor')
away_model = bundle.get('away_model') or bundle.get('model') or bundle.get('away_regressor')
# If bundle stores models under generic keys, attempt fallback
if not isinstance(home_model, type(away_model)):
    # assume bundle is a dict with keys 'home' and 'away'
    home_model = bundle.get('home')
    away_model = bundle.get('away')
if home_model is None or away_model is None:
    raise RuntimeError('Could not locate home/away models in bundle')

# Predict on test set
pred_home = home_model.predict(X_test)
pred_away = away_model.predict(X_test)

# Compute metrics
mae_home = mean_absolute_error(y_home_test, pred_home)
rmse_home = sqrt(mean_squared_error(y_home_test, pred_home))
r2_home = r2_score(y_home_test, pred_home)

mae_away = mean_absolute_error(y_away_test, pred_away)
rmse_away = sqrt(mean_squared_error(y_away_test, pred_away))
r2_away = r2_score(y_away_test, pred_away)

print('\n=== Goal Model Test Set Metrics ===')
print('Home Goals Model:')
print(f'  MAE : {mae_home:.4f}')
print(f'  RMSE: {rmse_home:.4f}')
print(f'  R²  : {r2_home:.4f}')
print('Away Goals Model:')
print(f'  MAE : {mae_away:.4f}')
print(f'  RMSE: {rmse_away:.4f}')
print(f'  R²  : {r2_away:.4f}')

# Sample 20 random predictions from test set
sample_indices = random.sample(range(len(X_test)), min(20, len(X_test)))
print('\n=== 20 Sample Predictions (Actual vs Predicted) ===')
print('HomeTeam   AwayTeam   ActualHome  PredHome  ErrHome   ActualAway  PredAway  ErrAway')
for idx in sample_indices:
    row = X_test[idx]
    # retrieve team names via original df (need to map back). We'll use the test indices on df.
    original_idx = df.index[X_test.tolist().index(row.tolist())]  # not reliable. Simpler: use df.iloc with X_test mask.
    # We'll just get the corresponding row from the original df using test boolean mask.
    # Generate mask
    mask = (df[FEATURES] == pd.DataFrame(row, columns=FEATURES)).all(axis=1)
    possible = df[mask]
    if not possible.empty:
        home = possible.iloc[0]['home_team']
        away = possible.iloc[0]['away_team']
    else:
        home = 'N/A'
        away = 'N/A'
    ah = y_home_test[idx]
    ph = pred_home[idx]
    ae = y_away_test[idx]
    pe = pred_away[idx]
    print(f'{home:10s} {away:10s} {ah:10.2f} {ph:8.2f} {ah-ph:8.2f} {ae:10.2f} {pe:8.2f} {ae-pe:8.2f}')

# Error distribution summary (absolute errors)
abs_err_home = np.abs(y_home_test - pred_home)
abs_err_away = np.abs(y_away_test - pred_away)
print('\n=== Error Distribution Summary ===')
print('Home Goal MAE Distribution:')
print(f'  Min: {abs_err_home.min():.2f}, Max: {abs_err_home.max():.2f}, Mean: {abs_err_home.mean():.2f}, Std: {abs_err_home.std():.2f}')
print('Away Goal MAE Distribution:')
print(f'  Min: {abs_err_away.min():.2f}, Max: {abs_err_away.max():.2f}, Mean: {abs_err_away.mean():.2f}, Std: {abs_err_away.std():.2f}')

# Example matches predictions using predict_goals function from train_goal_model
from ml.train_goal_model import predict_goals
examples = [
    ("Brazil", "Germany"),
    ("Argentina", "Spain"),
    ("France", "England"),
    ("Portugal", "Netherlands"),
]
print('\n=== Example Match Expected Goals ===')
for home, away in examples:
    try:
        res = predict_goals(home, away)
        print(f'{home:12s} vs {away:12s} -> Home expected: {res["expected_home_goals"]:.2f}, Away expected: {res["expected_away_goals"]:.2f}')
    except Exception as e:
        print(f'Error for {home} vs {away}: {e}')
