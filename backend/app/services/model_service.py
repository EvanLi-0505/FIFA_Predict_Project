"""Model training and management service (Development Prompt.md Section 16).

Training always retrains on ALL completed matches of the chosen dataset
(matching PHASE 13.1 of the source notebook / `core.models.training.
retrain_on_all_completed_matches`), so the deployed model is trained on
every available match, not just a train-split subset. The held-out
chronological split is still run first purely to compute evaluation
metrics attached to the model_versions record.
"""

from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.services import feature_service
from core.analytics.upset import (
    UPSET_HISTORY_CACHE_FILENAME,
    compute_upset_history,
    save_upset_history_cache,
)
from core.config import (
    CLASS_LABELS,
    DEFAULT_FEATURE_VERSION,
    SUPPORTED_FEATURE_VERSIONS,
    TRAIN_RATIO,
)
from core.dataset.io import load_raw_dataset
from core.models.definitions import MODEL_FACTORIES
from core.models.registry import ModelMetadata, save_model_artifact
from core.models.split import chronological_train_test_split
from core.models.training import (
    evaluate_predictions,
    fit_model,
    predict_with_model,
    retrain_on_all_completed_matches,
)
from core.pipeline import run_feature_pipeline
from core.prediction.team_state import build_team_latest_state_index, save_team_state_index_cache
from backend.app.services.feature_service import TEAM_STATE_CACHE_FILENAME
from database.models import ModelVersion
from database.repositories.sqlalchemy_repositories import (
    DatasetRepositoryImpl,
    ModelVersionRepositoryImpl,
)

_dataset_repo = DatasetRepositoryImpl()
_model_repo = ModelVersionRepositoryImpl()


class ModelTrainingError(ValueError):
    pass


def list_models(session: Session) -> list[ModelVersion]:
    return _model_repo.list_all(session)


def get_model(session: Session, model_version_id: int) -> ModelVersion | None:
    return _model_repo.get_by_id(session, model_version_id)


def train_model(
    session: Session,
    *,
    dataset_id: int,
    model_type: str = "logistic_regression",
    feature_version: str = DEFAULT_FEATURE_VERSION,
) -> ModelVersion:
    if model_type not in MODEL_FACTORIES:
        raise ModelTrainingError(
            f"Unknown model_type {model_type!r}. Expected one of "
            f"{sorted(MODEL_FACTORIES)}."
        )
    if feature_version not in SUPPORTED_FEATURE_VERSIONS:
        raise ModelTrainingError(
            f"Unknown feature_version {feature_version!r}. Expected one of "
            f"{list(SUPPORTED_FEATURE_VERSIONS)}."
        )

    dataset = _dataset_repo.get_by_id(session, dataset_id)
    if dataset is None:
        raise ModelTrainingError(f"Dataset {dataset_id} does not exist.")
    if dataset.validation_status != "valid":
        raise ModelTrainingError(
            f"Cannot train on dataset {dataset_id}: "
            f"validation_status={dataset.validation_status!r}."
        )

    df_raw = load_raw_dataset(dataset.file_path)
    pipeline_result = run_feature_pipeline(df_raw, feature_version)

    model_factory = MODEL_FACTORIES[model_type]

    # Held-out chronological evaluation (metrics only — see module docstring)
    X = pipeline_result.model_data[pipeline_result.feature_columns].copy()
    y = pipeline_result.model_data["result"].copy()
    split = chronological_train_test_split(pipeline_result.model_data, X, y, TRAIN_RATIO)

    eval_model = model_factory()
    eval_model, eval_scaler = fit_model(model_type, eval_model, split.X_train, split.y_train)

    overall_predictions, _ = predict_with_model(eval_model, eval_scaler, split.X_test)
    overall_metrics = evaluate_predictions(split.y_test, overall_predictions)

    # The FIFA World Cup evaluation subset (Phases 8.5/9.4/10.4 of the
    # source notebook) assumes the dataset contains World Cup matches. A
    # generic user-uploaded dataset may not (e.g. a regional league
    # dataset) — sklearn's predict()/predict_proba() raise on a 0-row
    # input, so this must be skipped rather than crashing the whole
    # training run.
    if len(split.X_test_world_cup) > 0:
        world_cup_predictions, _ = predict_with_model(
            eval_model, eval_scaler, split.X_test_world_cup
        )
        world_cup_metrics_dict = evaluate_predictions(
            split.y_test_world_cup, world_cup_predictions
        ).to_dict()
    else:
        world_cup_metrics_dict = None

    # Deployment model: retrained on every completed match
    model, scaler = retrain_on_all_completed_matches(
        model_type=model_type,
        model_factory=model_factory,
        model_data=pipeline_result.model_data,
        feature_columns=pipeline_result.feature_columns,
    )

    # The expensive part (training itself) is done — everything from here
    # is just ID allocation + file writes + a DB insert, so it's cheap to
    # retry as a unit. `next_model_id` (a SELECT) and `.create()` (an
    # INSERT) are two separate statements — two concurrent "Train" calls
    # (e.g. the API hit directly/twice, bypassing the UI's own disabled-
    # while-training guard) could both compute the same "next" id and race
    # on the model_id UNIQUE constraint (same class of race as
    # `database.bootstrap`'s — see its module docstring). Retrying with a
    # freshly recomputed id turns that into "try again" instead of a 500.
    last_error: IntegrityError | None = None
    for _attempt in range(3):
        model_id = _model_repo.next_model_id(session, model_type)
        artifact_dir = settings.models_dir / model_type / model_id

        metadata = ModelMetadata(
            model_id=model_id,
            model_type=model_type,
            dataset_version=dataset.version_label,
            feature_version=feature_version,
            feature_columns=pipeline_result.feature_columns,
            tournament_dummy_columns=pipeline_result.tournament_dummy_columns,
            cold_start_fill_values=pipeline_result.cold_start_fill_values,
            class_labels=CLASS_LABELS,
            training_timestamp=datetime.now(timezone.utc).isoformat(),
            metrics={
                "held_out_split_date": str(split.split_date.date()),
                "overall_test": overall_metrics.to_dict(),
                "world_cup_test": world_cup_metrics_dict,
                "trained_on_records": len(pipeline_result.model_data),
            },
        )

        save_model_artifact(artifact_dir, model, metadata, scaler)

        # Pre-populate the team-state cache (see feature_service.py's
        # docstring) right now, while `pipeline_result.featured_data` is
        # already sitting in memory from training — computing it is
        # otherwise the dominant cost of the FIRST prediction/launch after
        # this model becomes active. Without this, switching to a newly
        # trained model still works correctly (feature_service recomputes
        # on a cache miss), it would just pay the ~7s cost once at that
        # point instead of never.
        save_team_state_index_cache(
            artifact_dir / TEAM_STATE_CACHE_FILENAME,
            build_team_latest_state_index(
                pipeline_result.featured_data, pipeline_result.elo_ratings
            ),
        )
        save_upset_history_cache(
            artifact_dir / UPSET_HISTORY_CACHE_FILENAME,
            compute_upset_history(
                model, scaler, pipeline_result.model_data, pipeline_result.feature_columns
            ),
        )

        try:
            model_version = _model_repo.create(
                session,
                model_id=model_id,
                model_type=model_type,
                dataset_id=dataset.id,
                feature_version=feature_version,
                artifact_path=str(artifact_dir.resolve()),
                metrics=metadata.metrics,
            )
        except IntegrityError as error:
            session.rollback()
            shutil.rmtree(artifact_dir, ignore_errors=True)
            last_error = error
            continue

        session.commit()
        return model_version

    raise ModelTrainingError(
        f"Could not allocate a model id after several attempts (concurrent training?): {last_error}"
    )


def activate_model(session: Session, model_version_id: int) -> ModelVersion:
    model_version = _model_repo.activate(session, model_version_id)
    session.commit()
    feature_service.invalidate_cache()
    return model_version


def delete_model(session: Session, model_version_id: int) -> None:
    """Delete a model version.

    Blocked by the repository (PermissionError/ValueError) for the
    protected built-in model, the currently active model, or a model with
    existing prediction history — see
    `database.repositories.sqlalchemy_repositories.ModelVersionRepositoryImpl.delete`.
    """

    model_version = _model_repo.get_by_id(session, model_version_id)
    _model_repo.delete(session, model_version_id)  # raises before any file I/O if blocked
    session.commit()

    if model_version is not None:
        artifact_dir = Path(model_version.artifact_path)
        if artifact_dir.exists():
            shutil.rmtree(artifact_dir)
