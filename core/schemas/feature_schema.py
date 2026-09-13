"""Canonical predictor-variable list and ordering.

Ported verbatim from the source notebook, PHASE 6.7
("DEFINE FINAL PREDICTOR VARIABLES"). The Decision Tree is sensitive to
column order, so `build_feature_columns` must always be used to construct
`feature_columns` — never re-derive this list ad hoc elsewhere.
"""

from __future__ import annotations

from core.feature_engineering.differences import DIFFERENCE_FEATURES

# Original historical team-performance features (10)
BASE_FEATURES = [
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


def build_feature_columns(tournament_dummy_columns: list[str]) -> list[str]:
    """Build the full ordered predictor list: base + difference + context.

    `tournament_dummy_columns` must come from
    `core.feature_engineering.tournament.encode_tournament_categories`,
    which determines the exact dummy column names/order present for a given
    dataset version.
    """

    context_features = ["neutral"] + tournament_dummy_columns

    return BASE_FEATURES + DIFFERENCE_FEATURES + context_features
