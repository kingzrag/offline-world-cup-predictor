import pandas as pd
import os

df = pd.read_csv(os.path.join(os.path.dirname(__file__), "ml", "dataset_world_cup.csv"))

print("Columns in dataset:")
print(df.columns.tolist())

print("\n--- New Zealand vs South Korea rows ---")
matches = df[(df["home_team"] == "New Zealand") & (df["away_team"] == "South Korea")]

if len(matches) > 0:
    print(matches[["home_team", "away_team", 
                   "home_kaggle_attack_rating", "away_kaggle_attack_rating", 
                   "home_kaggle_defense_rating", "away_kaggle_defense_rating",
                   "home_kaggle_discipline_score", "away_kaggle_discipline_score",
                   "home_kaggle_starting_xi_strength", "away_kaggle_starting_xi_strength",
                   "home_kaggle_bench_strength", "away_kaggle_bench_strength"]].to_string())

else:
    print("Not found")
