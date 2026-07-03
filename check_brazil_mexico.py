import pandas as pd
import os

df = pd.read_csv(os.path.join(os.path.dirname(__file__), "ml", "dataset_world_cup.csv"))

match = df[(df["home_team"] == "Brazil") & (df["away_team"] == "Mexico")]

print("Match: Brazil vs Mexico")
cols = ["home_team", "away_team"]
kaggle_cols = [col for col in df.columns if "kaggle" in col or "referee_strictness" in col]

print(match[cols + kaggle_cols].to_string())
