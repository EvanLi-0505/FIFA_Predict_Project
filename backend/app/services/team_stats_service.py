"""Team browsing/comparison service, backing the Team Explorer page.

Unlike predictions (which always use the ACTIVE MODEL's own training
dataset — see `feature_service`'s docstring for why), team browsing is a
read-only exploration feature with no model involved, so it simply reflects
whichever dataset is currently flagged active in Dataset Management. This
cache is invalidated by `dataset_service.activate_dataset`.
"""

from __future__ import annotations

import threading

import pandas as pd
from sqlalchemy.orm import Session

from core.analytics.team_stats import (
    TeamStats,
    compare_teams as compare_teams_core,
    compute_team_stats,
    get_team_matches as get_team_matches_core,
    list_all_team_names,
)
from core.analytics.team_stats import TeamMatchRecord
from core.dataset.io import load_raw_dataset
from core.pipeline import build_completed_matches
from database.repositories.sqlalchemy_repositories import DatasetRepositoryImpl

_dataset_repo = DatasetRepositoryImpl()

MAX_COMPARE_TEAMS = 5

_cache_lock = threading.Lock()
_cached_completed_matches: pd.DataFrame | None = None
_cached_dataset_id: int | None = None
_cached_dataset_version_label: str | None = None


class NoActiveDatasetError(RuntimeError):
    pass


class TooManyTeamsError(ValueError):
    pass


def _get_completed_matches(session: Session) -> tuple[pd.DataFrame, str]:
    global _cached_completed_matches, _cached_dataset_id, _cached_dataset_version_label

    active_dataset = _dataset_repo.get_active(session)
    if active_dataset is None:
        raise NoActiveDatasetError("No active dataset configured.")

    with _cache_lock:
        if _cached_completed_matches is not None and _cached_dataset_id == active_dataset.id:
            return _cached_completed_matches, _cached_dataset_version_label

        df_raw = load_raw_dataset(active_dataset.file_path)
        completed_matches, _ = build_completed_matches(df_raw)

        _cached_completed_matches = completed_matches
        _cached_dataset_id = active_dataset.id
        _cached_dataset_version_label = active_dataset.version_label

        return completed_matches, active_dataset.version_label


def invalidate_cache() -> None:
    global _cached_completed_matches, _cached_dataset_id, _cached_dataset_version_label
    with _cache_lock:
        _cached_completed_matches = None
        _cached_dataset_id = None
        _cached_dataset_version_label = None


def list_teams(session: Session) -> list[str]:
    completed_matches, _ = _get_completed_matches(session)
    return list_all_team_names(completed_matches)


def get_team_matches(
    session: Session, team_name: str, limit: int | None = None
) -> list[TeamMatchRecord]:
    completed_matches, _ = _get_completed_matches(session)
    return get_team_matches_core(completed_matches, team_name, limit=limit)


def get_team_stats(session: Session, team_name: str) -> TeamStats | None:
    completed_matches, _ = _get_completed_matches(session)
    return compute_team_stats(completed_matches, team_name)


def compare_teams(session: Session, team_names: list[str]) -> list[TeamStats]:
    if len(team_names) == 0:
        raise ValueError("Provide at least one team to compare.")
    if len(team_names) > MAX_COMPARE_TEAMS:
        raise TooManyTeamsError(
            f"Cannot compare more than {MAX_COMPARE_TEAMS} teams at once."
        )

    completed_matches, _ = _get_completed_matches(session)
    return compare_teams_core(completed_matches, team_names)
