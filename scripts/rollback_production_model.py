#!/usr/bin/env python3
"""
scripts/rollback_production_model.py
====================================
Production-grade rollback mechanism for world_cup_predictor.pkl.

Steps:
  1. Verify backup artifact exists
  2. Verify backup SHA-256 checksum against certified baseline
  3. Create an emergency snapshot of the active production model
  4. Perform atomic replacement (tmp file -> os.replace)
  5. Verify restored production SHA-256 checksum
  6. Return exit code 0 on success, 1 on failure
"""

import os
import sys
import shutil
import hashlib
import tempfile
from datetime import datetime, timezone

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROD_MODEL_PATH = os.path.join(_ROOT, "models", "world_cup_predictor.pkl")
DEFAULT_BACKUP_PATH = os.path.join(_ROOT, "models", "world_cup_predictor_backup_v1.pkl")
BACKUPS_DIR = os.path.join(_ROOT, "models", "backups")

# Certified original production baseline SHA-256
BASELINE_PROD_SHA256 = "3c1c3aeee447233190de72e1e4c9b07ccac04939e059852ec960d6283d000cff"

def compute_sha256(file_path: str) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def rollback(backup_path: str = DEFAULT_BACKUP_PATH, expected_sha: str = BASELINE_PROD_SHA256) -> bool:
    print(f"[{datetime.now(timezone.utc).isoformat()}] Initiating production rollback...")
    
    # Step 1: Verify backup exists
    if not os.path.exists(backup_path):
        print(f"ERROR: Backup file not found at: {backup_path}")
        return False
    
    # Step 2: Verify backup checksum
    backup_sha = compute_sha256(backup_path)
    print(f"Backup SHA-256: {backup_sha}")
    if expected_sha and backup_sha != expected_sha:
        print(f"ERROR: Backup checksum mismatch! Expected: {expected_sha}, Got: {backup_sha}")
        return False
    print("✓ Backup integrity verified.")
    
    # Step 3: Snapshot current active model before overwriting
    os.makedirs(BACKUPS_DIR, exist_ok=True)
    if os.path.exists(PROD_MODEL_PATH):
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        pre_rollback_snap = os.path.join(BACKUPS_DIR, f"world_cup_predictor_pre_rollback_{ts}.pkl")
        shutil.copy2(PROD_MODEL_PATH, pre_rollback_snap)
        print(f"✓ Pre-rollback active model snapshotted to: {pre_rollback_snap}")
    
    # Step 4: Atomic restoration
    prod_dir = os.path.dirname(PROD_MODEL_PATH)
    with tempfile.NamedTemporaryFile(dir=prod_dir, delete=False, prefix="prod_rollback_", suffix=".tmp") as tmp_f:
        tmp_path = tmp_f.name
        with open(backup_path, "rb") as src_f:
            shutil.copyfileobj(src_f, tmp_f)
    
    # Verify tmp file checksum before atomic swap
    tmp_sha = compute_sha256(tmp_path)
    if tmp_sha != backup_sha:
        print(f"ERROR: Corrupted staging copy ({tmp_sha}) during rollback.")
        os.remove(tmp_path)
        return False
        
    os.replace(tmp_path, PROD_MODEL_PATH)
    print(f"✓ Atomic replacement to {PROD_MODEL_PATH} completed.")
    
    # Step 5: Verify restored production checksum
    restored_sha = compute_sha256(PROD_MODEL_PATH)
    print(f"Restored Production SHA-256: {restored_sha}")
    if restored_sha != backup_sha:
        print(f"ERROR: Post-restoration checksum verification failed!")
        return False
        
    print("==================================================")
    print("SUCCESS: Production model rollback completed successfully.")
    print(f"Active Production SHA-256: {restored_sha}")
    print("==================================================")
    return True

if __name__ == "__main__":
    success = rollback()
    sys.exit(0 if success else 1)
