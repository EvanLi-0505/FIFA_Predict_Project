"""Model artifact serialization: save/load a trained model with everything
required to reproduce its predictions later (Development Prompt.md Section 28).

A model artifact directory contains:
    model.joblib            - the fitted sklearn estimator
    scaler.joblib            - fitted StandardScaler, only if the model needs it
    metadata.json            - model_type, dataset_version, feature_version,
                               class labels, training timestamp, metrics,
                               feature_columns (ORDER MATTERS),
                               tournament_dummy_columns, cold_start_fill_values

Database-backed versioning (model_versions table, active-model tracking)
lives in the backend service layer, not here. This module only guarantees
that a model directory is self-sufficient for making predictions.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import joblib
from sklearn.base import ClassifierMixin
from sklearn.preprocessing import StandardScaler

from core.config import CLASS_LABELS


@dataclass
class ModelMetadata:
    model_id: str
    model_type: str
    dataset_version: str
    feature_version: str
    feature_columns: list[str]
    tournament_dummy_columns: list[str]
    cold_start_fill_values: dict[str, float]
    class_labels: list[str]
    training_timestamp: str
    metrics: dict[str, Any] = field(default_factory=dict)
    has_scaler: bool = False

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)

    @staticmethod
    def from_json(text: str) -> "ModelMetadata":
        return ModelMetadata(**json.loads(text))


def save_model_artifact(
    output_dir: str | Path,
    model: ClassifierMixin,
    metadata: ModelMetadata,
    scaler: StandardScaler | None = None,
) -> Path:
    """Persist a trained model + its metadata to `output_dir`."""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    joblib.dump(model, output_dir / "model.joblib")

    metadata.has_scaler = scaler is not None
    if scaler is not None:
        joblib.dump(scaler, output_dir / "scaler.joblib")

    (output_dir / "metadata.json").write_text(metadata.to_json(), encoding="utf-8")

    return output_dir


@dataclass
class LoadedModel:
    model: ClassifierMixin
    scaler: StandardScaler | None
    metadata: ModelMetadata


def load_model_artifact(model_dir: str | Path) -> LoadedModel:
    """Load a model artifact directory produced by `save_model_artifact`."""

    model_dir = Path(model_dir)

    metadata_path = model_dir / "metadata.json"
    if not metadata_path.exists():
        raise FileNotFoundError(f"metadata.json not found in {model_dir}")

    metadata = ModelMetadata.from_json(metadata_path.read_text(encoding="utf-8"))

    model_path = model_dir / "model.joblib"
    if not model_path.exists():
        raise FileNotFoundError(f"model.joblib not found in {model_dir}")

    model = joblib.load(model_path)

    scaler = None
    if metadata.has_scaler:
        scaler_path = model_dir / "scaler.joblib"
        if not scaler_path.exists():
            raise FileNotFoundError(
                f"metadata declares has_scaler=True but scaler.joblib is "
                f"missing in {model_dir}"
            )
        scaler = joblib.load(scaler_path)

    if metadata.class_labels != CLASS_LABELS:
        raise ValueError(
            "Loaded model's class labels do not match the current "
            f"CLASS_LABELS configuration: {metadata.class_labels} != "
            f"{CLASS_LABELS}"
        )

    return LoadedModel(model=model, scaler=scaler, metadata=metadata)
