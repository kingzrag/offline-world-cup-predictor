"""
Handles backup management of previous versions of datasets
"""

import logging
import os
from pathlib import Path
import shutil
from datetime import datetime

logger = logging.getLogger(__name__)

def create_backup(
    source_dir: Path,
    backup_dir: Path
) -> Path:
    """
    Creates a timestamped backup of the source directory.
    """
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"archive_backup_{timestamp}"
    logger.info(f"Creating backup of {source_dir} → {backup_path}")
    shutil.copytree(source_dir, backup_path)
    logger.info("Backup completed successfully")
    return backup_path

def list_backups(backup_dir: Path) -> list[Path]:
    """Lists all available backups"""
    if not backup_dir.exists():
        return []
    return sorted(
        [p for p in backup_dir.iterdir() if p.is_dir() and p.name.startswith("archive_backup_")],
        reverse=True
    )

def restore_backup(backup_path: Path, target_dir: Path):
    """Restore a backup to a target directory"""
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup path {backup_path} doesn't exist!")
    
    logger.info(f"Restoring backup from {backup_path} → {target_dir}")
    if target_dir.exists():
        shutil.rmtree(target_dir)
    shutil.copytree(backup_path, target_dir)
    logger.info("Backup restored successfully")
