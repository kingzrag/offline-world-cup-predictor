#!/usr/bin/env python3
"""
Full pipeline to download and update the dataset!
"""

import logging
import os
import sys
import shutil
from pathlib import Path

# Add root path!
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.kaggle_utils import check_for_updates, download_dataset
from scripts.backup_manager import create_backup, restore_backup
from scripts.data_validator import validate_dataset
from scripts.csv_to_sqlite import create_database_from_csvs, verify_database

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(PROJECT_ROOT / "dataset_update.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


DATASET_NAME = "mominullptr/fifa-world-cup-2026-dataset"
DATA_DIR = PROJECT_ROOT / "data"
ARCHIVE_DIR = DATA_DIR / "archive"
BACKUP_DIR = DATA_DIR / "backups"
TEMP_DOWNLOAD_DIR = DATA_DIR / "temp_download"
LAST_UPDATE_FILE = DATA_DIR / ".last_kaggle_update.txt"
DATABASE_PATH = DATA_DIR / "fifa_world_cup_2026.db"


def main():
    logger.info("Starting dataset update pipeline")
    backup_path = None
    try:
        # Step 1: Check for updates!
        if not check_for_updates(DATASET_NAME, LAST_UPDATE_FILE):
            logger.info("No update needed!")
            return 0
        logger.info("Proceeding with dataset update")

        # Step 2: Backup!
        logger.info("Creating backup...")
        if ARCHIVE_DIR.exists():
            backup_path = create_backup(ARCHIVE_DIR, BACKUP_DIR)
        
        # Step 3: Download new dataset to temp location
        logger.info("Downloading dataset to temp location...")
        if TEMP_DOWNLOAD_DIR.exists():
            shutil.rmtree(TEMP_DOWNLOAD_DIR)
        last_updated = download_dataset(DATASET_NAME, TEMP_DOWNLOAD_DIR)
        
        # Step4: Verify download (sometimes Kaggle unzips into a subfolder)!
        temp_contents = list(TEMP_DOWNLOAD_DIR.iterdir())
        actual_archive_dir = TEMP_DOWNLOAD_DIR
        if len(temp_contents) == 1 and temp_contents[0].is_dir():
            actual_archive_dir = temp_contents[0]
        
        logger.info(f"Checking dataset at {actual_archive_dir}")
        if not validate_dataset(actual_archive_dir):
            logger.error("Data validation failed! Restoring backup...")
            if backup_path:
                restore_backup(backup_path, ARCHIVE_DIR)
            return 1
        
        # Step5: Generate SQLite database from CSV files
        logger.info("Generating SQLite database from CSV files...")
        if not create_database_from_csvs(actual_archive_dir, DATABASE_PATH):
            logger.error("Database generation failed! Restoring backup...")
            if backup_path:
                restore_backup(backup_path, ARCHIVE_DIR)
            return 1
        
        # Step6: Verify database was created correctly
        logger.info("Verifying database...")
        if not verify_database(DATABASE_PATH):
            logger.error("Database verification failed! Restoring backup...")
            if backup_path:
                restore_backup(backup_path, ARCHIVE_DIR)
            return 1
        
        # Step7: Replace existing archive!
        logger.info("Replacing existing archive...")
        if ARCHIVE_DIR.exists():
            shutil.rmtree(ARCHIVE_DIR)
        shutil.copytree(actual_archive_dir, ARCHIVE_DIR)
        
        # Step8: Update last update file!
        with open(LAST_UPDATE_FILE, "w") as f:
            f.write(last_updated)
        
        logger.info("Dataset updated successfully!")
        
        # Step9: Run feature engineering and retrain!
        logger.info("Building ML dataset...")
        from ml.build_dataset_world_cup import build_dataset as build_world_cup_dataset
        build_world_cup_dataset()
        
        logger.info("Training world cup predictor...")
        from ml.train_world_cup_model import train_model as train_world_cup
        train_world_cup()
        
        # Step10: Cleanup!
        logger.info("Cleaning up temporary directory...")
        shutil.rmtree(TEMP_DOWNLOAD_DIR)
        
        logger.info("All pipeline steps completed successfully!")
        return 0

    except Exception:
        logger.exception("Dataset update failed! Restoring backup if available.")
        if backup_path:
            try:
                restore_backup(backup_path, ARCHIVE_DIR)
                logger.info("Successfully restored backup!")
            except Exception as backup_exception:
                logger.exception("Failed to restore backup! Your project may be in an inconsistent state.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

