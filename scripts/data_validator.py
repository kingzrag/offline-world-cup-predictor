"""
Data validation module to check that the required files are present!
"""
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

REQUIRED_FILES = [
    "match_events.csv",
    "match_lineups.csv",
    "match_team_stats.csv",
    "matches.csv",
    "matches_detailed.csv",
    "player_stats.csv",
    "referees.csv",
    "squads_and_players.csv",
    "teams.csv",
    "tournament_stages.csv",
    "venues.csv",
]

def validate_dataset(data_dir: Path) -> bool:
    """
    Validates that all required files are present in the given directory
    """
    logger.info(f"Validating dataset at: {data_dir}")
    all_good = True
    for filename in REQUIRED_FILES:
        filepath = data_dir / filename
        if not filepath.exists():
            logger.error(f"Required file is missing: {filename}")
            all_good = False
        else:
            logger.debug(f"File exists: {filename}")

    if all_good:
        logger.info("All required files are present!")
        return True
    
    return False
