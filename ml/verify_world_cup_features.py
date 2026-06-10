"""
Diagnostics script to verify feature distribution and coverage.
"""

import sys
import os
import pandas as pd

# Add root folder to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import logger

def verify_features():
    dataset_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dataset_world_cup.csv")
    if not os.path.exists(dataset_path):
        logger.error(f"Dataset file {dataset_path} does not exist. Please run build_dataset_world_cup first.")
        return
        
    df = pd.read_csv(dataset_path)
    logger.info(f"Loaded dataset with {len(df)} rows.")
    
    target_features = ["mv_diff", "inj_diff", "susp_diff"]
    other_features = ["elo_diff", "fifa_diff", "form_diff", "gs_diff", "gc_diff", "home_adv", "h2h_factor"]
    
    print("\n" + "="*60)
    print("  WORLD CUP FEATURE DIAGNOSTICS & VERIFICATION")
    print("="*60)
    
    # Check all features are present
    all_features = target_features + other_features
    missing_cols = [col for col in all_features if col not in df.columns]
    if missing_cols:
        print(f"ERROR: Missing columns in dataset: {missing_cols}")
        return
        
    # Print statistics
    stats = df[all_features].describe().round(4)
    print("\n=== Feature Statistics (describe) ===")
    print(stats.to_string())
    
    print("\n=== Non-Zero Counts ===")
    for col in all_features:
        non_zero = (df[col] != 0).sum()
        pct = (non_zero / len(df)) * 100
        print(f"  {col:15s} : {non_zero:5d}/{len(df)} ({pct:.2f}% non-zero)")
        
    print("\n=== Verification Checks ===")
    for col in target_features:
        # Check non-zero count is significant
        non_zero = (df[col] != 0).sum()
        if non_zero > 100:
            print(f"  ✅ {col} has high coverage ({non_zero} non-zero rows)")
        elif non_zero > 0:
            print(f"  ⚠️ {col} has low coverage ({non_zero} non-zero rows)")
        else:
            print(f"  ❌ {col} has ZERO coverage")
            
    print("="*60 + "\n")

if __name__ == "__main__":
    verify_features()
