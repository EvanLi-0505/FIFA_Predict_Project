"""Dataset management service (Development Prompt.md Sections 11-15).

Implements the upload workflow: user uploads CSV -> new dataset version
created -> validated -> activation is a separate, explicit step. The
built-in dataset is never touched by any function here except reads.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.services import team_stats_service
from core.dataset.io import load_raw_dataset
from core.validation.dataset_validation import ValidationReport, validate_dataset
from database.models import Dataset
from database.repositories.sqlalchemy_repositories import DatasetRepositoryImpl

_dataset_repo = DatasetRepositoryImpl()

SCHEMA_VERSION = "raw_v1"


class DatasetUploadError(ValueError):
    """Raised for malformed or oversized uploads, before any DB write."""


@dataclass
class UploadResult:
    dataset: Dataset
    validation: ValidationReport


def list_datasets(session: Session) -> list[Dataset]:
    return _dataset_repo.list_all(session)


def get_dataset(session: Session, dataset_id: int) -> Dataset | None:
    return _dataset_repo.get_by_id(session, dataset_id)


def upload_dataset(
    session: Session, *, original_filename: str, file_bytes: bytes, display_name: str | None = None
) -> UploadResult:
    """Save an uploaded CSV as a new dataset version and validate it.

    Does NOT activate the dataset — that is a separate, explicit step
    (Development Prompt.md Section 15).
    """

    if len(file_bytes) == 0:
        raise DatasetUploadError("Uploaded file is empty.")

    if len(file_bytes) > settings.max_upload_size_bytes:
        raise DatasetUploadError(
            f"Uploaded file exceeds the {settings.max_upload_size_bytes:,}-byte limit."
        )

    if not original_filename.lower().endswith(".csv"):
        raise DatasetUploadError("Only .csv files are accepted.")

    settings.user_datasets_dir.mkdir(parents=True, exist_ok=True)

    # `next_user_version_label` (a SELECT) and `.create()` (an INSERT) are
    # two separate statements — two uploads racing each other could both
    # compute the same "next" label and both try to insert it, the loser
    # hitting the version_label UNIQUE constraint (same class of race as
    # `database.bootstrap`'s, see its module docstring). Retrying with a
    # freshly recomputed label turns that into "try again" instead of a
    # 500. In practice this only matters for near-simultaneous uploads
    # (e.g. two browser tabs, or a client that retries on timeout) — the
    # UI itself only ever submits one upload at a time.
    last_error: IntegrityError | None = None
    for _attempt in range(3):
        version_label = _dataset_repo.next_user_version_label(session)
        destination_path = settings.user_datasets_dir / f"{version_label}.csv"
        # Filename sanitisation (Development Prompt.md Section 36): the
        # on-disk filename is derived entirely from the server-generated
        # version label, never from user input, so path traversal /
        # injection via filename is not possible regardless of what
        # `original_filename` contains.
        destination_path.write_bytes(file_bytes)

        try:
            df_raw = load_raw_dataset(destination_path)
            validation_report = validate_dataset(df_raw)
            row_count = validation_report.row_count
        except Exception as error:  # noqa: BLE001 - surfaced as a failed validation, not a crash
            validation_report = ValidationReport(is_valid=False, row_count=0)
            validation_report.add_error("file", f"Could not parse uploaded file: {error}")
            row_count = 0

        try:
            dataset = _dataset_repo.create(
                session,
                version_label=version_label,
                name=display_name or original_filename,
                source="upload",
                is_builtin=False,
                validation_status="valid" if validation_report.is_valid else "invalid",
                row_count=row_count,
                schema_version=SCHEMA_VERSION,
                file_path=str(destination_path.resolve()),
                validation_report={
                    "is_valid": validation_report.is_valid,
                    "issues": [
                        {"field": issue.field, "message": issue.message}
                        for issue in validation_report.issues
                    ],
                },
            )
        except IntegrityError as error:
            session.rollback()
            destination_path.unlink(missing_ok=True)
            last_error = error
            continue

        session.commit()
        return UploadResult(dataset=dataset, validation=validation_report)

    raise DatasetUploadError(
        "Could not allocate a dataset version after several attempts "
        f"(concurrent uploads?): {last_error}"
    )


def activate_dataset(session: Session, dataset_id: int) -> Dataset:
    """Mark a dataset as the current default (Section 15 workflow step).

    Note: this has NO effect on live predictions by itself — predictions
    always use the ACTIVE MODEL's own training dataset (see
    `feature_service`'s module docstring). Activating a dataset changes
    what Dataset Management shows as current, what a subsequent
    `POST /api/models/train` call would default to training on, AND what
    the Team Explorer page (`team_stats_service`) browses/compares, since
    that feature has no model involved and simply reflects the active
    dataset directly.
    """

    dataset = _dataset_repo.activate(session, dataset_id)
    session.commit()
    team_stats_service.invalidate_cache()
    return dataset


def delete_dataset(session: Session, dataset_id: int) -> None:
    dataset = _dataset_repo.get_by_id(session, dataset_id)

    # Built-in protection takes precedence over every other rule, checked
    # here (not just inside the repository) so the API can return the more
    # specific 403 rather than a generic 400 when both conditions hold.
    if dataset is not None and dataset.is_builtin:
        raise PermissionError(
            "The built-in dataset is protected and cannot be deleted "
            "(Development Prompt.md Section 11)."
        )

    if dataset is not None and dataset.is_active:
        raise ValueError(
            "Cannot delete the currently active dataset. Activate a "
            "different dataset first."
        )

    _dataset_repo.delete(session, dataset_id)  # defence in depth: also raises PermissionError for builtin
    session.commit()

    if dataset is not None:
        file_path = Path(dataset.file_path)
        if file_path.exists() and not dataset.is_builtin:
            file_path.unlink()
