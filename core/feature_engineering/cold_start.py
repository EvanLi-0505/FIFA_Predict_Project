"""Cold-start fallback values for teams with no prior match history.

Ported verbatim from the source notebook, PHASE 6.1
(`cold_start_fill_values` computation) and PHASE 6.2 (application via
`fillna`).
"""

from __future__ import annotations

import pandas as pd

HISTORICAL_FEATURES = [
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


def compute_cold_start_fill_values(model_data: pd.DataFrame) -> dict[str, float]:
    """Compute global fallback values from completed matches.

    `home_matches_available` / `away_matches_available` are intentionally
    NOT included: a cold-start team has zero available matches by
    definition, and that raw 0 is preserved rather than being replaced by
    an average (matches the notebook, which never fills those two columns).
    """

    total_team_appearances = len(model_data) * 2

    overall_win_rate = (
        model_data["result"] != "Draw"
    ).sum() / total_team_appearances

    overall_draw_rate = (
        (model_data["result"] == "Draw").sum() * 2 / total_team_appearances
    )

    overall_avg_goals = (
        model_data["home_score"].sum() + model_data["away_score"].sum()
    ) / total_team_appearances

    return {
        "home_recent_win_rate": overall_win_rate,
        "away_recent_win_rate": overall_win_rate,
        "home_recent_draw_rate": overall_draw_rate,
        "away_recent_draw_rate": overall_draw_rate,
        "home_avg_goals_scored": overall_avg_goals,
        "away_avg_goals_scored": overall_avg_goals,
        "home_avg_goals_conceded": overall_avg_goals,
        "away_avg_goals_conceded": overall_avg_goals,
        "home_recent_goal_difference": 0.0,
        "away_recent_goal_difference": 0.0,
    }


def apply_cold_start(
    data: pd.DataFrame, cold_start_fill_values: dict[str, float]
) -> pd.DataFrame:
    """Fill missing engineered features using the precomputed fallback values."""

    return data.fillna(value=cold_start_fill_values)
