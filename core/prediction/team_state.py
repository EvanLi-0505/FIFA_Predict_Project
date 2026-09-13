"""Per-team "most recent feature state" index for dynamic prediction.

The source notebook's `get_team_latest_history()` (PHASE 13.2) scans the
entire chronological timeline for every prediction request to find a team's
most recent appearance. That is correct but O(n) per request. This module
precomputes the same information ONCE per dataset/model load as an O(n)
pass over the timeline, producing an O(1)-lookup dict. The result is
mathematically identical: for every team, it captures the feature values
from that team's latest chronological appearance (home or away), using the
role-appropriate columns — exactly what `get_team_latest_history` returns.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

TeamState = dict[str, float]


def build_team_latest_state_index(featured_data: pd.DataFrame) -> dict[str, TeamState]:
    """Build a {team_name: latest_feature_state} index.

    `featured_data` must be sorted chronologically ascending (this is
    guaranteed by `core.feature_engineering.team_history.generate_historical_features`,
    which always returns its result in ascending-date order).
    """

    index: dict[str, TeamState] = {}

    columns_needed = [
        "home_team",
        "away_team",
        "home_recent_win_rate",
        "away_recent_win_rate",
        "home_recent_draw_rate",
        "away_recent_draw_rate",
        "home_avg_goals_scored",
        "away_avg_goals_scored",
        "home_avg_goals_conceded",
        "away_avg_goals_conceded",
        "home_recent_goal_difference",
        "away_recent_goal_difference",
        "home_matches_available",
        "away_matches_available",
    ]

    for row in featured_data[columns_needed].itertuples(index=False):
        index[row.home_team] = {
            "win_rate": row.home_recent_win_rate,
            "draw_rate": row.home_recent_draw_rate,
            "goals_scored": row.home_avg_goals_scored,
            "goals_conceded": row.home_avg_goals_conceded,
            "goal_diff": row.home_recent_goal_difference,
            "exp": row.home_matches_available,
        }
        index[row.away_team] = {
            "win_rate": row.away_recent_win_rate,
            "draw_rate": row.away_recent_draw_rate,
            "goals_scored": row.away_avg_goals_scored,
            "goals_conceded": row.away_avg_goals_conceded,
            "goal_diff": row.away_recent_goal_difference,
            "exp": row.away_matches_available,
        }

    return index


def list_known_teams(team_state_index: dict[str, TeamState]) -> list[str]:
    """All team names with at least one historical appearance, sorted."""

    return sorted(team_state_index.keys())


def save_team_state_index_cache(cache_path: str | Path, team_state_index: dict[str, TeamState]) -> None:
    """Persist a computed index to disk (plain JSON — it's just nested
    str/float dicts) so a later process can skip recomputing it.

    Building this index requires re-running the full historical feature
    engineering pass over the entire dataset (`core.pipeline.
    run_feature_pipeline`), which takes several seconds on the ~50k-row
    built-in dataset — by far the largest contributor to Desktop startup
    time (Development Prompt.md Section 39 / Stage 5 QA). Since the result
    depends only on the dataset a given model was trained on, and that
    dataset never changes after training, it is safe to compute ONCE and
    reuse on every later launch — see `backend/app/services/
    feature_service.py`'s cache-loading logic, which calls this pair of
    functions keyed by model artifact path.
    """

    cache_path = Path(cache_path)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(team_state_index), encoding="utf-8")


def load_team_state_index_cache(cache_path: str | Path) -> dict[str, TeamState] | None:
    """Load a previously saved index, or None if no cache exists yet (or
    it's unreadable — treated the same as "not cached", never fatal:
    the caller always has the option to recompute)."""

    cache_path = Path(cache_path)
    if not cache_path.exists():
        return None

    try:
        return json.loads(cache_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
