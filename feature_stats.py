import pandas as pd
import numpy as np

# Load dataset_world_cup.csv
print('=== DATASET_WORLD_CUP.CSV ANALYSIS ===')
df_wc = pd.read_csv('ml/dataset_world_cup.csv')
print(f'Total rows: {len(df_wc)}')
print(f'Total columns: {len(df_wc.columns)}')

# Get all features (exclude home_team, away_team, target)
feature_cols = [col for col in df_wc.columns if col not in ['home_team', 'away_team', 'target']]

print(f'\n=== FEATURE STATISTICS (dataset_world_cup.csv) ===')
for col in feature_cols:
    series = df_wc[col]
    min_val = series.min()
    max_val = series.max()
    mean_val = series.mean()
    std_val = series.std()
    zero_count = (series == 0).sum()
    non_zero_count = (series != 0).sum()
    missing_count = series.isna().sum()
    
    # Determine feature status
    if missing_count == len(df_wc):
        status = 'MISSING'
    elif std_val == 0:
        status = 'CONSTANT'
    elif zero_count > len(df_wc) * 0.9:
        status = 'MOSTLY_ZERO'
    elif zero_count == len(df_wc):
        status = 'ALWAYS_ZERO'
    else:
        status = 'HEALTHY'
    
    print(f'{col:40s} | Min: {min_val:8.4f} | Max: {max_val:8.4f} | Mean: {mean_val:8.4f} | Std: {std_val:8.4f} | Zero: {zero_count:4d} | NonZero: {non_zero_count:4d} | Missing: {missing_count:4d} | {status}')

print('\n' + '='*100)
print('=== DATASET_GOALS.CSV ANALYSIS ===')
df_goals = pd.read_csv('ml/dataset_goals.csv')
print(f'Total rows: {len(df_goals)}')
print(f'Total columns: {len(df_goals.columns)}')

# Get all features (exclude home_team, away_team, home_score, away_score)
feature_cols_goals = [col for col in df_goals.columns if col not in ['home_team', 'away_team', 'home_score', 'away_score']]

print(f'\n=== FEATURE STATISTICS (dataset_goals.csv) ===')
for col in feature_cols_goals:
    series = df_goals[col]
    min_val = series.min()
    max_val = series.max()
    mean_val = series.mean()
    std_val = series.std()
    zero_count = (series == 0).sum()
    non_zero_count = (series != 0).sum()
    missing_count = series.isna().sum()
    
    # Determine feature status
    if missing_count == len(df_goals):
        status = 'MISSING'
    elif std_val == 0:
        status = 'CONSTANT'
    elif zero_count > len(df_goals) * 0.9:
        status = 'MOSTLY_ZERO'
    elif zero_count == len(df_goals):
        status = 'ALWAYS_ZERO'
    else:
        status = 'HEALTHY'
    
    print(f'{col:40s} | Min: {min_val:8.4f} | Max: {max_val:8.4f} | Mean: {mean_val:8.4f} | Std: {std_val:8.4f} | Zero: {zero_count:4d} | NonZero: {non_zero_count:4d} | Missing: {missing_count:4d} | {status}')
