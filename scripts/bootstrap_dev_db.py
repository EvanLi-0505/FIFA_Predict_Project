"""Stage 2 end-to-end smoke test: bootstrap a real SQLite DB from the actual
built-in dataset + Stage 1 model artifact (not mocked data).

This is a development convenience script, NOT the final Desktop app-data
location. The Desktop backend (Stage 5) will point `build_sqlite_url` at
the user-data directory (Development Prompt.md Section 9), e.g.
`%APPDATA%/FIFA-Prediction/app.db` — never at a path inside the project.

Usage:
    .venv/Scripts/python.exe scripts/bootstrap_dev_db.py
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.config import BUILTIN_MODEL_SUBDIRS, DEFAULT_BUILTIN_MODEL_SUBDIR  # noqa: E402
from database.bootstrap import bootstrap_database  # noqa: E402
from database.engine import create_db_engine, create_session_factory  # noqa: E402
from database.repositories.sqlalchemy_repositories import (  # noqa: E402
    DatasetRepositoryImpl,
    ModelVersionRepositoryImpl,
)

DEV_DB_PATH = PROJECT_ROOT / "dev-data" / "app.db"
BUILTIN_DATASET_CSV = PROJECT_ROOT / "datasets" / "builtin" / "results.csv"
MODELS_ROOT = PROJECT_ROOT / "models"


def main() -> int:
    DEV_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DEV_DB_PATH.exists():
        DEV_DB_PATH.unlink()
        print(f"Removed existing dev DB at {DEV_DB_PATH}")

    engine = create_db_engine(f"sqlite:///{DEV_DB_PATH.as_posix()}")
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        bootstrap_database(
            engine,
            session,
            builtin_dataset_csv=BUILTIN_DATASET_CSV,
            builtin_model_dirs=[MODELS_ROOT / subdir for subdir in BUILTIN_MODEL_SUBDIRS],
            default_model_dir=MODELS_ROOT / DEFAULT_BUILTIN_MODEL_SUBDIR,
        )

        dataset_repo = DatasetRepositoryImpl()
        model_repo = ModelVersionRepositoryImpl()

        print(f"\nSQLite DB created at: {DEV_DB_PATH}")

        print("\nDatasets:")
        for dataset in dataset_repo.list_all(session):
            print(
                f"  [{'BUILTIN' if dataset.is_builtin else 'upload'}] "
                f"{dataset.version_label:<12} rows={dataset.row_count:<8} "
                f"active={dataset.is_active} valid={dataset.validation_status}"
            )

        print("\nModel versions:")
        for model_version in model_repo.list_all(session):
            print(
                f"  {model_version.model_id:<28} type={model_version.model_type:<20} "
                f"active={model_version.is_active} dataset_id={model_version.dataset_id}"
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
