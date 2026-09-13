"""Comparative team-strength difference features.

Ported verbatim from the source notebook, PHASE 6.3
(`add_difference_features`).
"""

from __future__ import annotations

import pandas as pd

DIFFERENCE_FEATURES = [
    "win_rate_difference",
    "draw_rate_difference",
    "goals_scored_difference",
    "goals_conceded_difference",
    "goal_difference_difference",
    "experience_difference",
]


def add_difference_features(data: pd.DataFrame) -> pd.DataFrame:
    """Create home-minus-away relative team-strength indicators."""

    data = data.copy()

    data["win_rate_difference"] = (
        data["home_recent_win_rate"] - data["away_recent_win_rate"]
    )
    data["draw_rate_difference"] = (
        data["home_recent_draw_rate"] - data["away_recent_draw_rate"]
    )
    data["goals_scored_difference"] = (
        data["home_avg_goals_scored"] - data["away_avg_goals_scored"]
    )
    data["goals_conceded_difference"] = (
        data["home_avg_goals_conceded"] - data["away_avg_goals_conceded"]
    )
    data["goal_difference_difference"] = (
        data["home_recent_goal_difference"] - data["away_recent_goal_difference"]
    )
    data["experience_difference"] = (
        data["home_matches_available"] - data["away_matches_available"]
    )

    return data
