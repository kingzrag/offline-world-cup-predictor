"""
CSV to SQLite database conversion module.
Automatically generates SQLite database from CSV files.
"""

import logging
import sqlite3
from pathlib import Path
from typing import List, Dict
import pandas as pd

logger = logging.getLogger(__name__)

REQUIRED_CSV_FILES = [
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


def create_database_from_csvs(csv_dir: Path, db_path: Path) -> bool:
    """
    Creates a SQLite database from CSV files in the given directory.
    
    Args:
        csv_dir: Directory containing the CSV files
        db_path: Path where the SQLite database should be created
        
    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Creating SQLite database at: {db_path}")
    logger.info(f"Reading CSV files from: {csv_dir}")
    
    try:
        # Remove existing database if it exists
        if db_path.exists():
            logger.info(f"Removing existing database: {db_path}")
            db_path.unlink()
        
        # Create database directory if it doesn't exist
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Connect to database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        imported_tables = []
        failed_imports = []
        
        # Process each CSV file
        for csv_file in REQUIRED_CSV_FILES:
            csv_path = csv_dir / csv_file
            if not csv_path.exists():
                logger.error(f"CSV file not found: {csv_file}")
                failed_imports.append(csv_file)
                continue
            
            try:
                # Read CSV into pandas DataFrame
                logger.info(f"Importing {csv_file}...")
                df = pd.read_csv(csv_path)
                
                # Table name is CSV filename without extension
                table_name = csv_file.replace('.csv', '')
                
                # Write to SQLite
                df.to_sql(table_name, conn, if_exists='replace', index=False)
                imported_tables.append(table_name)
                logger.info(f"Successfully imported {csv_file} as table '{table_name}' ({len(df)} rows)")
                
            except Exception as e:
                logger.error(f"Failed to import {csv_file}: {str(e)}")
                failed_imports.append(csv_file)
        
        # Verify all tables were imported
        logger.info("Verifying imported tables...")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = {row[0] for row in cursor.fetchall()}
        
        expected_tables = {f.replace('.csv', '') for f in REQUIRED_CSV_FILES}
        missing_tables = expected_tables - existing_tables
        
        if missing_tables:
            logger.error(f"Missing tables after import: {missing_tables}")
            conn.close()
            return False
        
        if failed_imports:
            logger.error(f"Failed to import {len(failed_imports)} CSV files: {failed_imports}")
            conn.close()
            return False
        
        # Get row counts for verification
        logger.info("Table row counts:")
        for table in sorted(existing_tables):
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            logger.info(f"  {table}: {count} rows")
        
        conn.commit()
        conn.close()
        
        logger.info(f"Successfully created SQLite database with {len(imported_tables)} tables")
        return True
        
    except Exception as e:
        logger.exception(f"Failed to create SQLite database: {str(e)}")
        # Clean up partial database
        if db_path.exists():
            try:
                db_path.unlink()
                logger.info("Cleaned up partial database")
            except Exception as cleanup_error:
                logger.error(f"Failed to cleanup partial database: {cleanup_error}")
        return False


def verify_database(db_path: Path) -> bool:
    """
    Verifies that the SQLite database contains all required tables.
    
    Args:
        db_path: Path to the SQLite database
        
    Returns:
        True if all tables exist, False otherwise
    """
    logger.info(f"Verifying database at: {db_path}")
    
    if not db_path.exists():
        logger.error(f"Database file does not exist: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = {row[0] for row in cursor.fetchall()}
        
        expected_tables = {f.replace('.csv', '') for f in REQUIRED_CSV_FILES}
        missing_tables = expected_tables - existing_tables
        
        if missing_tables:
            logger.error(f"Missing tables in database: {missing_tables}")
            conn.close()
            return False
        
        logger.info(f"All {len(expected_tables)} required tables present in database")
        conn.close()
        return True
        
    except Exception as e:
        logger.exception(f"Failed to verify database: {str(e)}")
        return False
