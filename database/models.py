"""SQLAlchemy ORM models: dataset/model/prediction metadata.

Every column uses generic SQLAlchemy types (String, Integer, Float,
Boolean, DateTime, JSON, Text) so the identical schema works unmodified on
both MySQL (Web) and SQLite (Desktop) — see package docstring in
`database/__init__.py` for the full rationale.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Dataset(Base):
    """One row per dataset version (Development Prompt.md Section 13).

    The built-in dataset (`is_builtin=True`) is protected: repository
    methods refuse to delete or overwrite it (see
    `repositories.sqlalchemy_repositories.DatasetRepositoryImpl`).
    """

    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    version_label: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    """e.g. 'builtin_v1', 'user_v1', 'user_v2' — never reused."""

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source: Mapped[str] = mapped_column(String(16), nullable=False)
    """'builtin' or 'upload'."""

    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    validation_status: Mapped[str] = mapped_column(String(16), nullable=False)
    """'valid', 'invalid', or 'pending'."""

    validation_report: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    row_count: Mapped[int] = mapped_column(Integer, nullable=False)
    schema_version: Mapped[str] = mapped_column(String(32), nullable=False)

    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    """Path to the CSV on disk, relative to the datasets/ directory root."""

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    activated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    model_versions: Mapped[list["ModelVersion"]] = relationship(back_populates="dataset")


class ModelVersion(Base):
    """One row per trained model artifact (Development Prompt.md Section 16)."""

    __tablename__ = "model_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    model_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    """e.g. 'decision_tree_v1' — matches core.models.registry.ModelMetadata.model_id."""

    model_type: Mapped[str] = mapped_column(String(32), nullable=False)
    """'decision_tree', 'logistic_regression', or 'random_forest'."""

    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"), nullable=False)
    feature_version: Mapped[str] = mapped_column(String(32), nullable=False)

    artifact_path: Mapped[str] = mapped_column(Text, nullable=False)
    """Directory containing model.joblib + metadata.json, relative to models/."""

    metrics: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    """True only for the model registered by `database.bootstrap` on first
    startup (the validated production Decision Tree). Protected the same
    way as Dataset.is_builtin — never deletable through the UI/API."""

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)

    dataset: Mapped["Dataset"] = relationship(back_populates="model_versions")
    predictions: Mapped[list["Prediction"]] = relationship(back_populates="model_version")


class Prediction(Base):
    """Prediction history (Development Prompt.md Section 20)."""

    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    model_version_id: Mapped[int] = mapped_column(
        ForeignKey("model_versions.id"), nullable=False
    )
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"), nullable=False)
    """Denormalised copy of model_version.dataset_id at prediction time, kept
    even if the model version is later retired, for audit purposes."""

    home_team: Mapped[str] = mapped_column(String(128), nullable=False)
    away_team: Mapped[str] = mapped_column(String(128), nullable=False)
    host_country: Mapped[str] = mapped_column(String(128), nullable=False)
    tournament: Mapped[str] = mapped_column(String(128), nullable=False)
    neutral: Mapped[int] = mapped_column(Integer, nullable=False)

    probabilities: Mapped[dict] = mapped_column(JSON, nullable=False)
    predicted_outcome: Mapped[str] = mapped_column(String(16), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)

    model_version: Mapped["ModelVersion"] = relationship(back_populates="predictions")
