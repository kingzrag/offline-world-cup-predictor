import pandas as pd
import os

csv_dir = '/Users/anuragsaikia/prediction/data/archive'
csv_files = ['matches.csv', 'matches_detailed.csv', 'match_events.csv', 
             'match_lineups.csv', 'match_team_stats.csv', 'player_stats.csv', 
             'referees.csv', 'squads_and_players.csv', 'teams.csv']

for csv_file in csv_files:
    file_path = os.path.join(csv_dir, csv_file)
    if os.path.exists(file_path):
        print(f"=== {csv_file} ===")
        df = pd.read_csv(file_path)
        print(f"Shape: {df.shape}")
        print("Columns:")
        print(list(df.columns))
        print()
