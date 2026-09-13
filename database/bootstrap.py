"""First-run bootstrap: create tables, register the built-in dataset and
the Stage 1 production model artifact.

Both the Web and Desktop backends call `bootstrap_database` once at
startup. It is idempotent — safe to call on every process start.
"""

from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.dataset.io import load_raw_dataset
from core.validation.dataset_validation import validate_dataset
from database.engine import create_all_tables
from database.models import Dataset
from database.repositories.sqlalchemy_repositories import (
    DatasetRepositoryImpl,
    ModelVersionRepositoryImpl,
)

BUILTIN_VERSION_LABEL = "builtin_v1"
BUILTIN_SCHEMA_VERSION = "raw_v1"


def bootstrap_database(
    engine: Engine,
    session: Session,
    *,
    builtin_dataset_csv: str | Path,
    initial_model_dir: str | Path | None = None,
    initial_model_id: str | None = None,
) -> None:
    """Create tables (if needed) and seed the built-in dataset + model.

    Parameters
    ----------
    builtin_dataset_csv : path to the protected built-in dataset CSV
        (`datasets/builtin/results.csv`), stored relative to the project's
        datasets root in the `datasets.file_path` column.
    initial_model_dir : path to a model artifact directory produced by
        `core.models.registry.save_model_artifact`
        (`models/decision_tree/v1/`), registered as the initially active
        model. Optional — omit to bootstrap the dataset only.
    """

    create_all_tables(engine)

    dataset_repo = DatasetRepositoryImpl()

    builtin = dataset_repo.get_by_version_label(session, BUILTIN_VERSION_LABEL)
    if builtin is None:
        try:
            builtin = _register_builtin_dataset(session, dataset_repo, builtin_dataset_csv)
        except IntegrityError:
            # Two processes bootstrapping the same database at once — e.g.
            # a Desktop double-launch that briefly evaded the single-instance
            # lock, or multiple Web worker processes starting together
            # against shared MySQL. Both raced past the `is None` check
            # above; the loser lands here instead of crashing — the winner
            # already committed the row, so just use that one.
            session.rollback()
            builtin = dataset_repo.get_by_version_label(session, BUILTIN_VERSION_LABEL)
            if builtin is None:
                raise  # the row still doesn't exist — a real failure, not a race
    else:
        _resync_builtin_dataset_path(session, builtin, builtin_dataset_csv)

    if builtin.validation_status == "valid" and not _has_active_dataset(session):
        dataset_repo.activate(session, builtin.id)

    if initial_model_dir is not None:
        _register_initial_model(
            session, builtin, initial_model_dir, initial_model_id
        )

    session.commit()


def _resync_builtin_dataset_path(
    session: Session, builtin: Dataset, current_csv_path: str | Path
) -> None:
    """Keep the built-in dataset's `file_path` pointing at wherever the CSV
    actually ships with THIS install, self-healing on every startup.

    `_register_builtin_dataset` only runs once, on the very first launch —
    every later launch reuses whatever `file_path` was written back then.
    That value can go stale (and stay stale forever, since nothing else
    ever revisits it) whenever the on-disk location legitimately changes:
    the app is reinstalled to a different drive/folder (Development
    Prompt.md Section 26 asks for exactly this — a user-chosen install
    location), an update moves resource layout, or — as found during Stage
    5 desktop QA — a transient path-resolution glitch on one specific
    launch got permanently baked into the user's database, silently
    breaking every dataset-dependent endpoint (`/api/teams`, predictions,
    Team Explorer) on every subsequent launch with no way to recover short
    of deleting the user's whole database by hand. Re-validating against
    the CURRENT path on every startup instead means a bad path only ever
    breaks the one launch it happens on.
    """

    current_csv_path = str(Path(current_csv_path))
    if builtin.file_path == current_csv_path:
        return

    df_raw = load_raw_dataset(current_csv_path)
    validation_report = validate_dataset(df_raw)

    builtin.file_path = current_csv_path
    builtin.row_count = validation_report.row_count
    builtin.validation_status = "valid" if validation_report.is_valid else "invalid"
    builtin.validation_report = {
        "is_valid": validation_report.is_valid,
        "issues": [
            {"field": issue.field, "message": issue.message}
            for issue in validation_report.issues
        ],
    }
    session.flush()


def _has_active_dataset(session: Session) -> bool:
    return DatasetRepositoryImpl().get_active(session) is not None


def _register_builtin_dataset(
    session: Session, dataset_repo: DatasetRepositoryImpl, csv_path: str | Path
) -> Dataset:
    csv_path = Path(csv_path)

    df_raw = load_raw_dataset(csv_path)
    validation_report = validate_dataset(df_raw)

    return dataset_repo.create(
        session,
        version_label=BUILTIN_VERSION_LABEL,
        name="Built-in Dataset (protected)",
        source="builtin",
        is_builtin=True,
        validation_status="valid" if validation_report.is_valid else "invalid",
        row_count=validation_report.row_count,
        schema_version=BUILTIN_SCHEMA_VERSION,
        file_path=str(csv_path),
        validation_report={
            "is_valid": validation_report.is_valid,
            "issues": [
                {"field": issue.field, "message": issue.message}
                for issue in validation_report.issues
            ],
        },
    )


def _register_initial_model(
    session: Session,
    builtin_dataset: Dataset,
    model_dir: str | Path,
    model_id_override: str | None,
) -> None:
    model_dir = Path(model_dir)
    metadata_path = model_dir / "metadata.json"
    if not metadata_path.exists():
        raise FileNotFoundError(f"metadata.json not found in {model_dir}")

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    model_id = model_id_override or metadata["model_id"]

    model_repo = ModelVersionRepositoryImpl()

    existing = model_repo.get_by_model_id(session, model_id)
    if existing is not None:
        # Same self-healing rationale as _resync_builtin_dataset_path above.
        resolved_model_dir = str(model_dir)
        if existing.artifact_path != resolved_model_dir:
            existing.artifact_path = resolved_model_dir
            session.flush()
        if model_repo.get_active(session) is None:
            model_repo.activate(session, existing.id)
        return

    try:
        model_version = model_repo.create(
            session,
            model_id=model_id,
            model_type=metadata["model_type"],
            dataset_id=builtin_dataset.id,
            feature_version=metadata["feature_version"],
            artifact_path=str(model_dir),
            is_builtin=True,
            metrics=metadata.get("metrics"),
        )
    except IntegrityError:
        # Same concurrent-bootstrap race as the dataset registration above.
        session.rollback()
        model_version = model_repo.get_by_model_id(session, model_id)
        if model_version is None:
            raise

    model_repo.activate(session, model_version.id)
