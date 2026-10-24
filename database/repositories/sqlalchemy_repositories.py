"""SQLAlchemy-backed repository implementations.

These are the ONLY concrete repository classes in the project. They contain
zero engine-specific SQL — every query goes through the SQLAlchemy ORM
(`select()`, relationship loading), so the exact same code runs unmodified
against MySQL (Web) and SQLite (Desktop). This is what satisfies
Development Prompt.md Section 10's requirement for a single repository
abstraction shared by both platforms.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from database.models import Dataset, ModelVersion, Prediction
from database.repositories.interfaces import (
    DatasetRepository,
    ModelVersionRepository,
    PredictionRepository,
)


class DatasetRepositoryImpl(DatasetRepository):
    def create(
        self,
        session: Session,
        *,
        version_label: str,
        name: str,
        source: str,
        is_builtin: bool,
        validation_status: str,
        row_count: int,
        schema_version: str,
        file_path: str,
        validation_report: dict | None = None,
    ) -> Dataset:
        dataset = Dataset(
            version_label=version_label,
            name=name,
            source=source,
            is_builtin=is_builtin,
            is_active=False,
            validation_status=validation_status,
            validation_report=validation_report,
            row_count=row_count,
            schema_version=schema_version,
            file_path=file_path,
        )
        session.add(dataset)
        session.flush()
        return dataset

    def get_by_id(self, session: Session, dataset_id: int) -> Dataset | None:
        return session.get(Dataset, dataset_id)

    def get_by_version_label(self, session: Session, version_label: str) -> Dataset | None:
        return session.execute(
            select(Dataset).where(Dataset.version_label == version_label)
        ).scalar_one_or_none()

    def get_active(self, session: Session) -> Dataset | None:
        return session.execute(
            select(Dataset).where(Dataset.is_active.is_(True))
        ).scalar_one_or_none()

    def get_builtin(self, session: Session) -> Dataset | None:
        return session.execute(
            select(Dataset).where(Dataset.is_builtin.is_(True))
        ).scalar_one_or_none()

    def list_all(self, session: Session) -> list[Dataset]:
        return list(
            session.execute(select(Dataset).order_by(Dataset.created_at)).scalars()
        )

    def activate(self, session: Session, dataset_id: int) -> Dataset:
        target = session.get(Dataset, dataset_id)
        if target is None:
            raise ValueError(f"Dataset {dataset_id} does not exist.")
        if target.validation_status != "valid":
            raise ValueError(
                f"Cannot activate dataset {dataset_id}: "
                f"validation_status={target.validation_status!r}, expected 'valid'."
            )

        for dataset in session.execute(select(Dataset)).scalars():
            dataset.is_active = dataset.id == dataset_id

        target.activated_at = datetime.now(timezone.utc)
        session.flush()
        return target

    def delete(self, session: Session, dataset_id: int) -> None:
        target = session.get(Dataset, dataset_id)
        if target is None:
            return
        if target.is_builtin:
            raise PermissionError(
                "The built-in dataset is protected and cannot be deleted "
                "(Development Prompt.md Section 11)."
            )
        session.delete(target)
        session.flush()

    def next_user_version_label(self, session: Session) -> str:
        existing = session.execute(
            select(Dataset.version_label).where(Dataset.source == "upload")
        ).scalars()

        max_index = 0
        for label in existing:
            if label.startswith("user_v"):
                try:
                    max_index = max(max_index, int(label.removeprefix("user_v")))
                except ValueError:
                    continue

        return f"user_v{max_index + 1}"


class ModelVersionRepositoryImpl(ModelVersionRepository):
    def create(
        self,
        session: Session,
        *,
        model_id: str,
        model_type: str,
        dataset_id: int,
        feature_version: str,
        artifact_path: str,
        metrics: dict | None = None,
        is_builtin: bool = False,
    ) -> ModelVersion:
        model_version = ModelVersion(
            model_id=model_id,
            model_type=model_type,
            dataset_id=dataset_id,
            feature_version=feature_version,
            artifact_path=artifact_path,
            metrics=metrics,
            is_active=False,
            is_builtin=is_builtin,
        )
        session.add(model_version)
        session.flush()
        return model_version

    def get_by_id(self, session: Session, model_version_id: int) -> ModelVersion | None:
        return session.get(ModelVersion, model_version_id)

    def get_by_model_id(self, session: Session, model_id: str) -> ModelVersion | None:
        return session.execute(
            select(ModelVersion).where(ModelVersion.model_id == model_id)
        ).scalar_one_or_none()

    def get_active(self, session: Session) -> ModelVersion | None:
        return session.execute(
            select(ModelVersion).where(ModelVersion.is_active.is_(True))
        ).scalar_one_or_none()

    def list_all(self, session: Session) -> list[ModelVersion]:
        return list(
            session.execute(
                select(ModelVersion).order_by(ModelVersion.created_at)
            ).scalars()
        )

    def list_by_dataset(self, session: Session, dataset_id: int) -> list[ModelVersion]:
        return list(
            session.execute(
                select(ModelVersion).where(ModelVersion.dataset_id == dataset_id)
            ).scalars()
        )

    def activate(self, session: Session, model_version_id: int) -> ModelVersion:
        target = session.get(ModelVersion, model_version_id)
        if target is None:
            raise ValueError(f"Model version {model_version_id} does not exist.")

        for model_version in session.execute(select(ModelVersion)).scalars():
            model_version.is_active = model_version.id == model_version_id

        session.flush()
        return target

    def next_model_id(self, session: Session, model_type: str) -> str:
        existing = session.execute(
            select(ModelVersion.model_id).where(ModelVersion.model_type == model_type)
        ).scalars()

        prefix = f"{model_type}_v"
        max_index = 0
        for model_id in existing:
            if model_id.startswith(prefix):
                try:
                    max_index = max(max_index, int(model_id.removeprefix(prefix)))
                except ValueError:
                    continue

        return f"{prefix}{max_index + 1}"

    def delete(self, session: Session, model_version_id: int) -> None:
        target = session.get(ModelVersion, model_version_id)
        if target is None:
            return
        if target.is_builtin:
            raise PermissionError(
                "This is a protected built-in model and cannot be deleted."
            )
        if target.is_active:
            raise ValueError(
                "Cannot delete the currently active model. Activate a "
                "different model first."
            )

        prediction_count = session.execute(
            select(func.count())
            .select_from(Prediction)
            .where(Prediction.model_version_id == model_version_id)
        ).scalar_one()
        if prediction_count > 0:
            raise ValueError(
                f"Cannot delete this model version: {prediction_count} prediction "
                "history record(s) still reference it. Delete that history first."
            )

        session.delete(target)
        session.flush()


class PredictionRepositoryImpl(PredictionRepository):
    def create(
        self,
        session: Session,
        *,
        model_version_id: int,
        dataset_id: int,
        home_team: str,
        away_team: str,
        host_country: str,
        tournament: str,
        neutral: int,
        probabilities: dict,
        predicted_outcome: str,
        confidence: float,
    ) -> Prediction:
        prediction = Prediction(
            model_version_id=model_version_id,
            dataset_id=dataset_id,
            home_team=home_team,
            away_team=away_team,
            host_country=host_country,
            tournament=tournament,
            neutral=neutral,
            probabilities=probabilities,
            predicted_outcome=predicted_outcome,
            confidence=confidence,
        )
        session.add(prediction)
        session.flush()
        return prediction

    def list_recent(self, session: Session, limit: int = 50) -> list[Prediction]:
        return list(
            session.execute(
                select(Prediction).order_by(Prediction.created_at.desc()).limit(limit)
            ).scalars()
        )

    def get_by_id(self, session: Session, prediction_id: int) -> Prediction | None:
        return session.get(Prediction, prediction_id)

    def delete(self, session: Session, prediction_id: int) -> None:
        target = session.get(Prediction, prediction_id)
        if target is None:
            return
        session.delete(target)
        session.flush()

    def delete_all(self, session: Session) -> int:
        count = session.execute(select(func.count()).select_from(Prediction)).scalar_one()
        session.execute(Prediction.__table__.delete())
        session.flush()
        return count

    def count_by_outcome(self, session: Session) -> dict[str, int]:
        rows = session.execute(
            select(Prediction.predicted_outcome, func.count())
            .group_by(Prediction.predicted_outcome)
        ).all()
        return {outcome: count for outcome, count in rows}

    def list_all_confidences(self, session: Session) -> list[float]:
        return list(session.execute(select(Prediction.confidence)).scalars())
