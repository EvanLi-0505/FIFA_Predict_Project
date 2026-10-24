"""Historical upsets for the Upset Risk page (see core/analytics/upset.py).

Computed with the ACTIVE model over the dataset it was trained on — the
same model/dataset pairing live predictions use. Cached in memory per
active model and on disk next to the model artifact (written at training
time, or here on first use for models trained before v2.1.0).
"""

from __future__ import annotations

import threading
from pathlib import Path

from sqlalchemy.orm import Session

from backend.app.services.feature_service import get_inference_context
from core.analytics.upset import (
    UPSET_HISTORY_CACHE_FILENAME,
    compute_upset_history,
    load_upset_history_cache,
    save_upset_history_cache,
    team_upset_history,
)
from core.dataset.io import load_raw_dataset
from core.pipeline import run_feature_pipeline
from database.repositories.sqlalchemy_repositories import (
    DatasetRepositoryImpl,
    ModelVersionRepositoryImpl,
)

_dataset_repo = DatasetRepositoryImpl()
_model_repo = ModelVersionRepositoryImpl()

_cache_lock = threading.Lock()
_cached_history: dict | None = None
_cached_model_version_id: int | None = None


def _get_history(session: Session) -> dict:
    global _cached_history, _cached_model_version_id

    context = get_inference_context(session)
    with _cache_lock:
        if _cached_history is not None and _cached_model_version_id == context.model_version_id:
            return _cached_history

        model_version = _model_repo.get_by_id(session, context.model_version_id)
        cache_path = Path(model_version.artifact_path) / UPSET_HISTORY_CACHE_FILENAME
        history = load_upset_history_cache(cache_path)
        if history is None:
            dataset = _dataset_repo.get_by_id(session, context.dataset_id)
            pipeline_result = run_feature_pipeline(
                load_raw_dataset(dataset.file_path), model_version.feature_version
            )
            history = compute_upset_history(
                context.model, context.scaler, pipeline_result.model_data, context.feature_columns
            )
            save_upset_history_cache(cache_path, history)

        _cached_history = history
        _cached_model_version_id = context.model_version_id
        return history


def get_team_upsets(session: Session, team: str, *, limit: int) -> dict:
    return team_upset_history(_get_history(session), team, limit)
