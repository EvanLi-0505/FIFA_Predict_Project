"""Backend configuration, read from environment variables.

Development default is SQLite (per the user's chosen sequencing: get the
Web stack fully working end-to-end locally before wiring up MySQL). Set
DATABASE_URL to a MySQL URL for production — no code changes needed
anywhere else, since `database/` never contains engine-specific SQL.
"""

from __future__ import annotations

import os
from pathlib import Path

from database.engine import build_sqlite_url

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent

# Built-in models, relative to BUILTIN_MODELS_DIR. decision_tree/v1 is the
# original notebook model (feature_v1); logistic_regression/elo_v1 is the
# Elo-feature model (feature_v2) that new installs start with.
BUILTIN_MODEL_SUBDIRS = ("decision_tree/v1", "logistic_regression/elo_v1")
DEFAULT_BUILTIN_MODEL_SUBDIR = "logistic_regression/elo_v1"


class Settings:
    # --- Database ---------------------------------------------------
    # Dev default: SQLite file under backend/dev-data/. Production (Web):
    # set DATABASE_URL=mysql+pymysql://user:pass@host:3306/dbname
    # `build_sqlite_url` creates the parent directory if missing — do not
    # replace this with a plain f-string, or a fresh checkout with no
    # backend/dev-data/ directory yet will fail to start.
    database_url: str = os.environ.get(
        "DATABASE_URL",
        build_sqlite_url(BACKEND_DIR / "dev-data" / "app.db"),
    )

    # --- Filesystem paths ---------------------------------------------
    builtin_dataset_csv: Path = Path(
        os.environ.get(
            "BUILTIN_DATASET_CSV",
            str(PROJECT_ROOT / "datasets" / "builtin" / "results.csv"),
        )
    )
    user_datasets_dir: Path = Path(
        os.environ.get("USER_DATASETS_DIR", str(PROJECT_ROOT / "datasets" / "user"))
    )
    models_dir: Path = Path(
        os.environ.get("MODELS_DIR", str(PROJECT_ROOT / "models"))
    )
    # Root holding the shipped, protected model artifacts (read-only; the
    # Desktop build bundles them separately from the writable MODELS_DIR).
    builtin_models_dir: Path = Path(
        os.environ.get("BUILTIN_MODELS_DIR", str(PROJECT_ROOT / "models"))
    )

    @property
    def builtin_model_dirs(self) -> list[Path]:
        return [self.builtin_models_dir / subdir for subdir in BUILTIN_MODEL_SUBDIRS]

    @property
    def default_builtin_model_dir(self) -> Path:
        return self.builtin_models_dir / DEFAULT_BUILTIN_MODEL_SUBDIR

    # --- CORS -----------------------------------------------------------
    cors_allow_origins: list[str] = os.environ.get(
        "CORS_ALLOW_ORIGINS", "http://localhost:5173"
    ).split(",")

    # --- Upload limits (Development Prompt.md Section 36) -------------
    max_upload_size_bytes: int = int(
        os.environ.get("MAX_UPLOAD_SIZE_BYTES", str(50 * 1024 * 1024))  # 50 MB
    )


settings = Settings()
