"""Repository interfaces (Development Prompt.md Section 10).

Service-layer code (built in Stage 3) must depend only on these interfaces,
never on `database.repositories.sqlalchemy_repositories` directly, and
never construct raw SQL. Every method takes an explicit `Session` — session
lifetime (one per web request, one long-lived session for desktop) is the
caller's responsibility, not the repository's.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

from database.models import Dataset, ModelVersion, Prediction


class DatasetRepository(ABC):
    @abstractmethod
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
    ) -> Dataset: ...

    @abstractmethod
    def get_by_id(self, session: Session, dataset_id: int) -> Dataset | None: ...

    @abstractmethod
    def get_by_version_label(
        self, session: Session, version_label: str
    ) -> Dataset | None: ...

    @abstractmethod
    def get_active(self, session: Session) -> Dataset | None: ...

    @abstractmethod
    def get_builtin(self, session: Session) -> Dataset | None: ...

    @abstractmethod
    def list_all(self, session: Session) -> list[Dataset]: ...

    @abstractmethod
    def activate(self, session: Session, dataset_id: int) -> Dataset:
        """Mark one dataset active, deactivating every other dataset.

        Must not be blocked for the built-in dataset — protection only
        applies to delete/overwrite, not activation (Development Prompt.md
        Section 11 lists Edit/Delete/Overwrite as forbidden, not Activate).
        """
        ...

    @abstractmethod
    def delete(self, session: Session, dataset_id: int) -> None:
        """Delete a dataset. Must raise PermissionError for is_builtin=True
        (Development Prompt.md Section 11: 'never deleted through the UI')."""
        ...

    @abstractmethod
    def next_user_version_label(self, session: Session) -> str:
        """Return the next unused 'user_vN' label (Section 12)."""
        ...


class ModelVersionRepository(ABC):
    @abstractmethod
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
    ) -> ModelVersion: ...

    @abstractmethod
    def get_by_id(self, session: Session, model_version_id: int) -> ModelVersion | None: ...

    @abstractmethod
    def get_by_model_id(self, session: Session, model_id: str) -> ModelVersion | None: ...

    @abstractmethod
    def get_active(self, session: Session) -> ModelVersion | None: ...

    @abstractmethod
    def list_all(self, session: Session) -> list[ModelVersion]: ...

    @abstractmethod
    def list_by_dataset(self, session: Session, dataset_id: int) -> list[ModelVersion]: ...

    @abstractmethod
    def activate(self, session: Session, model_version_id: int) -> ModelVersion:
        """Mark one model version active, deactivating every other model version."""
        ...

    @abstractmethod
    def next_model_id(self, session: Session, model_type: str) -> str:
        """Return the next unused '{model_type}_vN' id, e.g. 'decision_tree_v2'."""
        ...

    @abstractmethod
    def delete(self, session: Session, model_version_id: int) -> None:
        """Delete a model version. Must raise PermissionError for
        is_builtin=True, and ValueError if it is the currently active model."""
        ...


class PredictionRepository(ABC):
    @abstractmethod
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
    ) -> Prediction: ...

    @abstractmethod
    def list_recent(self, session: Session, limit: int = 50) -> list[Prediction]: ...

    @abstractmethod
    def get_by_id(self, session: Session, prediction_id: int) -> Prediction | None: ...

    @abstractmethod
    def delete(self, session: Session, prediction_id: int) -> None: ...

    @abstractmethod
    def delete_all(self, session: Session) -> int:
        """Delete every prediction history record. Returns the number deleted."""
        ...

    @abstractmethod
    def count_by_outcome(self, session: Session) -> dict[str, int]:
        """Return {'Home Win': n, 'Draw': n, 'Home Loss': n} across all history."""
        ...

    @abstractmethod
    def list_all_confidences(self, session: Session) -> list[float]:
        """Return every stored confidence value, for histogram bucketing."""
        ...
