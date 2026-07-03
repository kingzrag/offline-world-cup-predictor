
#!/usr/bin/env python3
import pandas as pd
import numpy as np
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ML_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ml")
DATASET_PATH_WC = os.path.join(ML_DIR, "dataset_world_cup.csv")
DATASET_PATH_GOAL = os.path.join(ML_DIR, "dataset_goals.csv")

TARGET_WC = "target"
TARGET_HOME_GOAL = "home_score"
TARGET_AWAY_GOAL = "away_score"

def analyze_dataset(df, dataset_name, target_cols):
    print(f"\n--- Analyzing {dataset_name} ---")
    print(f"Shape: {df.shape}")

    # Correlation with target (retained for context, but main focus is stats)
    print("\nCorrelation with Target (Top/Bottom 10):")
    for target in target_cols:
        if target in df.columns:
            correlations = df.corr(numeric_only=True)[target].sort_values(ascending=False)
            print(f"  Target: {target}")
            print(correlations.head(10))
            print(correlations.tail(10))
        else:
            print(f"  Target column '{target}' not found in {dataset_name}.")

    print("\n--- Feature Statistics and Counts ---")
    for col in df.columns:
        if col in target_cols:
            continue # Skip target columns for these stats

        print(f"\nFeature: {col}")
        
        # Source function (will be manually added to report)
        # Value changes across dataset (inferred from std dev and unique count)
        
        # Min, Max, Mean, Std Dev
        if pd.api.types.is_numeric_dtype(df[col]):
            print(f"  Min: {df[col].min():.4f}")
            print(f"  Max: {df[col].max():.4f}")
            print(f"  Mean: {df[col].mean():.4f}")
            print(f"  Std Dev: {df[col].std():.4f}")
            
            # Zero, Non-zero counts
            zero_count = (df[col] == 0).sum()
            non_zero_count = (df[col] != 0).sum()
            print(f"  Zero Rows: {zero_count} ({zero_count/len(df)*100:.2f}%)")
            print(f"  Non-Zero Rows: {non_zero_count} ({non_zero_count/len(df)*100:.2f}%)")
        else:
            print(f"  (Non-numeric feature, skipping numerical stats)")

        # Missing rows
        missing_count = df[col].isnull().sum()
        print(f"  Missing Rows: {missing_count} ({missing_count/len(df)*100:.2f}%)")
        
        # Check if constant
        if df[col].nunique() == 1:
            print(f"  Status: CONSTANT (Value: {df[col].iloc[0]})")
        elif pd.api.types.is_numeric_dtype(df[col]) and df[col].std() == 0:
            print(f"  Status: CONSTANT (Std Dev is 0, Value: {df[col].iloc[0]})")
        else:
            print(f"  Status: VARYING")


def main():
    print("="*80)
    print("  FEATURE PIPELINE VALIDATION: STATISTICAL ANALYSIS")
    print("="*80)

    # World Cup Dataset
    try:
        df_wc = pd.read_csv(DATASET_PATH_WC)
        analyze_dataset(df_wc, "World Cup Dataset", [TARGET_WC])
    except FileNotFoundError:
        print(f"Error: World Cup dataset not found at {DATASET_PATH_WC}")
    
    # Goal Dataset
    try:
        df_goal = pd.read_csv(DATASET_PATH_GOAL)
        analyze_dataset(df_goal, "Goal Dataset", [TARGET_HOME_GOAL, TARGET_AWAY_GOAL])
    except FileNotFoundError:
        print(f"Error: Goal dataset not found at {DATASET_PATH_GOAL}")

if __name__ == "__main__":
    main()
