"""
ml/src/utils/paths.py
Flowshield — Centralized Path Abstraction Utility
Smart India Hackathon 2026 (PS ID: 26192)

Dynamically anchors to repository root and provides canonical, robust paths
for datasets, models, configurations, reports, experiments, and logs.
"""

import os
from pathlib import Path


def _find_repo_root() -> Path:
    """Traverse up to find repository root containing .git, apps/, or ml/."""
    curr = Path(__file__).resolve().parent
    for _ in range(6):
        if (curr / "ml").exists() and (curr / "apps").exists():
            return curr
        if (curr / ".git").exists():
            return curr
        if curr.parent == curr:
            break
        curr = curr.parent
    # Fallback to current working directory or 4 levels up
    return Path(__file__).resolve().parent.parent.parent.parent


def get_repo_root() -> Path:
    """Returns repository root Path."""
    return MLPaths.REPO_ROOT


class MLPaths:
    REPO_ROOT: Path = _find_repo_root()
    ML_ROOT: Path = REPO_ROOT / "ml"
    
    # Configs
    CONFIGS_DIR: Path = ML_ROOT / "configs"
    
    # Source package
    SRC_DIR: Path = ML_ROOT / "src"
    
    # Data hierarchy
    DATA_DIR: Path = ML_ROOT / "data"
    DATA_RAW_DIR: Path = DATA_DIR / "raw"
    DATA_INTERIM_DIR: Path = DATA_DIR / "interim"
    DATA_PROCESSED_DIR: Path = DATA_DIR / "processed"
    DATA_SPLITS_DIR: Path = DATA_DIR / "splits"
    DATA_SYNTHETIC_DIR: Path = DATA_DIR / "synthetic"
    
    # Models hierarchy
    MODELS_DIR: Path = ML_ROOT / "models"
    MODELS_PROD_DIR: Path = MODELS_DIR / "production"
    MODELS_CANDIDATES_DIR: Path = MODELS_DIR / "candidates"
    MODELS_BASELINE_BACKUP_DIR: Path = MODELS_DIR / "baseline_backup"
    MODELS_BACKUP_DIR: Path = MODELS_BASELINE_BACKUP_DIR
    MODELS_ARCHIVED_DIR: Path = MODELS_DIR / "archived"
    
    # Experiments
    EXPERIMENTS_DIR: Path = ML_ROOT / "experiments"
    
    # Reports
    REPORTS_DIR: Path = ML_ROOT / "reports"
    
    # Scripts & Tests
    SCRIPTS_DIR: Path = ML_ROOT / "scripts"
    TESTS_DIR: Path = ML_ROOT / "tests"
    NOTEBOOKS_DIR: Path = ML_ROOT / "notebooks"
    LOGS_DIR: Path = ML_ROOT / "logs"

    # Multi-region model hierarchy
    FLOOD_MODELS_DIR: Path = MODELS_DIR / "flood"

    # Region configs
    REGION_CONFIGS_DIR: Path = ML_ROOT / "configs" / "regions"

    @classmethod
    def region_model_dir(cls, region_slug: str) -> Path:
        """Returns path to a region's model artifacts directory."""
        return cls.FLOOD_MODELS_DIR / region_slug

    @classmethod
    def region_data_dir(cls, region_slug: str) -> Path:
        """Returns path to a region's raw data directory."""
        return cls.DATA_RAW_DIR / region_slug

    @classmethod
    def region_splits_dir(cls, region_slug: str) -> Path:
        """Returns path to a region's train/val/test splits."""
        return cls.DATA_SPLITS_DIR / region_slug

    @classmethod
    def ensure_region_dirs(cls, region_slug: str) -> None:
        """Create all directory paths for a specific region."""
        for d in [
            cls.region_model_dir(region_slug),
            cls.region_data_dir(region_slug),
            cls.region_splits_dir(region_slug),
        ]:
            os.makedirs(d, exist_ok=True)

    @classmethod
    def ensure_all_dirs(cls) -> None:
        """Create all required directory paths if they do not exist."""
        dirs = [
            cls.CONFIGS_DIR,
            cls.SRC_DIR,
            cls.DATA_RAW_DIR,
            cls.DATA_INTERIM_DIR,
            cls.DATA_PROCESSED_DIR,
            cls.DATA_SPLITS_DIR,
            cls.DATA_SYNTHETIC_DIR,
            cls.MODELS_PROD_DIR,
            cls.MODELS_CANDIDATES_DIR,
            cls.MODELS_BASELINE_BACKUP_DIR,
            cls.MODELS_ARCHIVED_DIR,
            cls.EXPERIMENTS_DIR,
            cls.REPORTS_DIR,
            cls.SCRIPTS_DIR,
            cls.TESTS_DIR,
            cls.NOTEBOOKS_DIR,
            cls.LOGS_DIR,
        ]
        for d in dirs:
            os.makedirs(d, exist_ok=True)
