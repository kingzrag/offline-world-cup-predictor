"""
Utilities for interacting with the Kaggle API.
Handles checking for dataset updates, downloading, and managing the dataset, etc.
"""

import logging
from pathlib import Path
import time

logger = logging.getLogger(__name__)

def check_kaggle_authenticated() -> bool:
    """Check if Kaggle API is authenticated"""
    kaggle_dir = Path.home() / ".kaggle"
    kaggle_json = kaggle_dir / "kaggle.json"
    kaggle_json_exists = kaggle_json.exists()
    logger.debug(f"Kaggle API credentials exist: {kaggle_json_exists}")
    return kaggle_json_exists

def check_for_updates(
    dataset: str,
    current_version_file: Path
) -> bool:
    """
    Checks if there's a newer version of the dataset available.
    Uses the last updated timestamp from Kaggle vs our local tracking file.
    """
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
        api = KaggleApi()
        api.authenticate()
        logger.info(f"Checking for updates for dataset: {dataset}")

        # Use dataset_list to get last updated time!
        datasets = api.dataset_list(search=dataset.split("/")[-1])
        matching_dataset = None
        for ds in datasets:
            if ds.ref == dataset:
                matching_dataset = ds
                break
        
        if not matching_dataset:
            raise ValueError(f"Could not find dataset {dataset}")
        
        # Try to get last_updated (snake_case) first, then lastUpdated (camelCase)
        last_updated_kaggle = None
        if hasattr(matching_dataset, 'last_updated'):
            last_updated_kaggle = str(matching_dataset.last_updated)
        elif hasattr(matching_dataset, 'lastUpdated'):
            last_updated_kaggle = str(matching_dataset.lastUpdated)
        
        if not last_updated_kaggle:
            raise AttributeError(f"Could not determine last updated time for dataset {dataset}. "
                                 f"Neither 'last_updated' nor 'lastUpdated' attribute was found in the dataset object. "
                                 f"Available attributes: {dir(matching_dataset)}")
        
        logger.debug(f"Dataset last updated on Kaggle: {last_updated_kaggle}")

        if not current_version_file.exists():
            logger.info("No current version file found; new update available")
            return True
        
        with open(current_version_file) as f:
            current_last_updated = f.read().strip()
        
        if last_updated_kaggle != current_last_updated:
            logger.info(
                f"New version available! Old: {current_last_updated}, New: {last_updated_kaggle}"
            )
            return True
        
        logger.info("Dataset already up to date!")
        return False

    except AttributeError as e:
        logger.error(f"Attribute error accessing Kaggle dataset metadata: {str(e)}")
        logger.error("This may indicate a Kaggle API version incompatibility")
        raise
    except Exception as e:
        logger.exception(f"Failed checking Kaggle dataset update: {str(e)}")
        raise

def download_dataset(
    dataset: str,
    download_dir: Path,
) -> str:
    """Downloads and returns lastUpdatedTime of the dataset"""
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
        api = KaggleApi()
        api.authenticate()

        logger.info(f"Downloading Kaggle dataset: {dataset}")
        download_dir.mkdir(parents=True, exist_ok=True)
        api.dataset_download_files(
            dataset,
            path=str(download_dir),
            unzip=True,
            force=True
        )
        logger.info(f"Dataset downloaded to: {download_dir}")
        
        # Now get the lastUpdatedTime again
        datasets = api.dataset_list(search=dataset.split("/")[-1])
        matching_dataset = None
        for ds in datasets:
            if ds.ref == dataset:
                matching_dataset = ds
                break
        if not matching_dataset:
            raise ValueError("Could not retrieve dataset metadata after download")
        
        # Try to get last_updated (snake_case) first, then lastUpdated (camelCase)
        last_updated = None
        if hasattr(matching_dataset, 'last_updated'):
            last_updated = str(matching_dataset.last_updated)
        elif hasattr(matching_dataset, 'lastUpdated'):
            last_updated = str(matching_dataset.lastUpdated)
        
        if not last_updated:
            raise AttributeError(f"Could not determine last updated time for dataset {dataset}. "
                                 f"Neither 'last_updated' nor 'lastUpdated' attribute was found in the dataset object. "
                                 f"Available attributes: {dir(matching_dataset)}")
        
        logger.info(f"Dataset last updated: {last_updated}")
        
        return last_updated
    except AttributeError as e:
        logger.error(f"Attribute error accessing Kaggle dataset metadata: {str(e)}")
        logger.error("This may indicate a Kaggle API version incompatibility")
        raise
    except Exception as e:
        logger.exception("Failed to download dataset")
        raise
