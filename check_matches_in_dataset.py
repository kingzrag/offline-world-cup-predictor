import pandas as pd
import os

df = pd.read_csv(os.path.join(os.path.dirname(__file__), "ml", "dataset_world_cup.csv"))

print("First 50 matches:")
print(df[["home_team", "away_team"]].head(50))
