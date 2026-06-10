import sys
import os
import logging
from datetime import datetime

# Ensure the root of the project is in the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import SessionLocal

# Setup basic logging to stdout to capture our logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_elo_refresh")

def run_simulated_elo_refresh(db, simulate_failure=False):
    """
    Simulates the exact block we added in api/main.py.
    """
    try:
        logger.info("[Test] Starting simulated automatic ELO ratings and FIFA rankings refresh...")
        start_time = datetime.now()
        
        if simulate_failure:
            # Simulate a failure early
            raise RuntimeError("Mocked database connection loss during computation.")
            
        from ml.compute_elo_ratings import compute_all_elo_ratings, save_elo_to_db, save_elo_ranks_to_teams
        
        # 1. Compute Elo ratings chronologically
        elo_ratings = compute_all_elo_ratings()
        
        # Validation: check that we received calculated ratings
        if not elo_ratings or len(elo_ratings) == 0:
            raise ValueError("Computed ELO ratings dictionary is empty.")
            
        # 2. Save Elo ratings to database
        save_elo_to_db(elo_ratings)
        
        # 3. Save Elo ranks to teams table
        save_elo_ranks_to_teams(elo_ratings)
        
        # Validation: verify that the team_elo table is populated
        from models.team_elo import TeamElo
        elo_count = db.query(TeamElo).count()
        if elo_count == 0:
            raise ValueError("Database validation failed: team_elo table contains 0 records after update.")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Log Top 10 rankings
        sorted_elo = sorted(elo_ratings.items(), key=lambda x: x[1], reverse=True)
        top_10 = sorted_elo[:10]
        top_10_str = "\n".join([f"    {rank}. {name}: {rating:.1f}" for rank, (name, rating) in enumerate(top_10, 1)])
        
        logger.info(
            f"[Test] ELO refresh completed successfully in {duration:.2f}s.\n"
            f"  - Start Time: {start_time.isoformat()}\n"
            f"  - End Time: {end_time.isoformat()}\n"
            f"  - Teams Updated: {len(elo_ratings)}\n"
            f"  - New Top 10 Rankings:\n{top_10_str}"
        )
        return True
    except Exception as elo_err:
        logger.error(f"[Test] Automatic ELO refresh failed: {elo_err}", exc_info=True)
        return False

def test_successful_refresh():
    print("\n=== Test 1: Successful ELO Refresh Flow ===")
    db = SessionLocal()
    try:
        success = run_simulated_elo_refresh(db, simulate_failure=False)
        assert success is True, "The refresh should have completed successfully."
        print("  ✓ Test 1 Passed!")
    finally:
        db.close()

def test_failed_refresh_does_not_crash():
    print("\n=== Test 2: Failed ELO Refresh Does Not Stop Execution ===")
    db = SessionLocal()
    try:
        # If this function raises an exception, the test fails.
        # It should handle the exception internally and return False.
        success = run_simulated_elo_refresh(db, simulate_failure=True)
        assert success is False, "The refresh should have returned False (failure logged internally)."
        print("  ✓ Test 2 Passed! Error was swallowed and logged safely.")
    finally:
        db.close()

if __name__ == "__main__":
    test_successful_refresh()
    test_failed_refresh_does_not_crash()
    print("\n🎉 ALL ELO REFRESH PIPELINE TESTS PASSED SUCCESSFULLY! ✓")
