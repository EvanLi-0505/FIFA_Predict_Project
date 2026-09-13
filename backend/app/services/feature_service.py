"""In-memory cache of the "ready to predict" bundle for the active model.

Rebuilding the full feature pipeline (historical feature engineering over
the whole dataset) on every prediction request would make the API far too
slow — this module rebuilds it once per active-model change and reuses it
for every subsequent request until invalidated (`invalidate_cache` is
called by dataset/model activation and training endpoints).

IMPORTANT correctness note: the feature schema used for prediction
(`feature_columns`, `tournament_dummy_columns`, `cold_start_fill_values`)
comes from the ACTIVE MODEL's own frozen metadata (recorded at training
time), NOT from re-running the feature pipeline on whatever dataset
happens to be flagged "active" in the `datasets` table. A model's
predictions must stay reproducible regardless of what else changes in the
system later (Development Prompt.md Section 29/43) — only the team
historical-state index needs to be (re)computed from a dataset, and it is
always computed from the dataset the ACTIVE MODEL was actually trained on
(`model_version.dataset_id`), never from an unrelated "currently active"
dataset. The `datasets.is_active` flag is purely a UI/workflow concept
(what Dataset Management shows as current, what a new upload defaults
against) — it has no bearing on how an already-trained model predicts.

Single-process cache: correct for the Desktop backend (always one process)
and for a single-worker Web deployment. If the Web backend is later run
with multiple worker processes, each process holds its own cache — that is
still correct (all rebuild from the same DB-recorded active model), just
not shared, which is an acceptable tradeoff at this project's scale.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path

from sklearn.base import ClassifierMixin
from sklearn.preprocessing import StandardScaler
from sqlalchemy.orm import Session

from core.dataset.io import load_raw_dataset
from core.models.registry import load_model_artifact
from core.pipeline import run_feature_pipeline
from core.prediction.team_state import (
    TeamState,
    build_team_latest_state_index,
    list_known_teams,
    load_team_state_index_cache,
    save_team_state_index_cache,
)
from database.repositories.sqlalchemy_repositories import (
    DatasetRepositoryImpl,
    ModelVersionRepositoryImpl,
)

TEAM_STATE_CACHE_FILENAME = "team_state_cache.json"

_dataset_repo = DatasetRepositoryImpl()
_model_repo = ModelVersionRepositoryImpl()


@dataclass
class InferenceContext:
    dataset_id: int
    dataset_version_label: str
    model_version_id: int
    model_id: str
    model_type: str

    model: ClassifierMixin
    scaler: StandardScaler | None

    feature_columns: list[str]
    tournament_dummy_columns: list[str]
    cold_start_fill_values: dict[str, float]

    team_state_index: dict[str, TeamState]
    known_teams: list[str]


_cache_lock = threading.Lock()
_cached_context: InferenceContext | None = None
_cached_model_version_id: int | None = None


class NoActiveConfigurationError(RuntimeError):
    """Raised when there is no active model to predict with."""


def get_inference_context(session: Session, *, force_reload: bool = False) -> InferenceContext:
    global _cached_context, _cached_model_version_id

    active_model = _model_repo.get_active(session)
    if active_model is None:
        raise NoActiveConfigurationError(
            "No active model configured. Train and activate a model before predicting."
        )

    with _cache_lock:
        if (
            not force_reload
            and _cached_context is not None
            and _cached_model_version_id == active_model.id
        ):
            return _cached_context

        training_dataset = _dataset_repo.get_by_id(session, active_model.dataset_id)
        if training_dataset is None:
            raise NoActiveConfigurationError(
                f"Active model {active_model.model_id!r} references dataset "
                f"id={active_model.dataset_id}, which no longer exists."
            )

        # The historical-feature-engineering pass this needs is the single
        # most expensive thing this app does (several seconds on the ~50k
        # row built-in dataset — the dominant cost of Desktop app startup,
        # since it's warmed eagerly at launch; see backend/app/main.py's
        # lifespan). Its result depends only on which dataset the ACTIVE
        # MODEL was trained on, which never changes after training, so it
        # is cached to disk (see team_state.py's save/load functions) right
        # next to that model's own artifact — reused on every later launch
        # instead of recomputed, until a genuinely different model becomes
        # active (a different artifact_path -> a different cache file).
        cache_path = Path(active_model.artifact_path) / TEAM_STATE_CACHE_FILENAME
        team_state_index = load_team_state_index_cache(cache_path)
        if team_state_index is None:
            df_raw = load_raw_dataset(training_dataset.file_path)
            pipeline_result = run_feature_pipeline(df_raw)
            team_state_index = build_team_latest_state_index(pipeline_result.featured_data)
            save_team_state_index_cache(cache_path, team_state_index)

        loaded_model = load_model_artifact(active_model.artifact_path)

        context = InferenceContext(
            dataset_id=training_dataset.id,
            dataset_version_label=training_dataset.version_label,
            model_version_id=active_model.id,
            model_id=active_model.model_id,
            model_type=active_model.model_type,
            model=loaded_model.model,
            scaler=loaded_model.scaler,
            feature_columns=loaded_model.metadata.feature_columns,
            tournament_dummy_columns=loaded_model.metadata.tournament_dummy_columns,
            cold_start_fill_values=loaded_model.metadata.cold_start_fill_values,
            team_state_index=team_state_index,
            known_teams=list_known_teams(team_state_index),
        )

        _cached_context = context
        _cached_model_version_id = active_model.id
        return context


def invalidate_cache() -> None:
    """Force the next `get_inference_context` call to rebuild from scratch.

    Must be called after any model activation or model training — otherwise
    predictions would keep using the stale cached context.
    """

    global _cached_context, _cached_model_version_id
    with _cache_lock:
        _cached_context = None
        _cached_model_version_id = None
