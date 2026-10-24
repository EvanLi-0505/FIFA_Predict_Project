"""Canonical predictor-variable list and ordering.

Ported verbatim from the source notebook, PHASE 6.7
("DEFINE FINAL PREDICTOR VARIABLES"). The Decision Tree is sensitive to
column order, so `build_feature_columns` must always be used to construct
`feature_columns` — never re-derive this list ad hoc elsewhere.
"""

from __future__ import annotations

from core.config import ELO_FEATURE_VERSION, ORIGINAL_FEATURE_VERSION
from core.feature_engineering.differences import DIFFERENCE_FEATURES
from core.feature_engineering.elo import ELO_FEATURES

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


def build_feature_columns(
    tournament_dummy_columns: list[str], feature_version: str = ORIGINAL_FEATURE_VERSION
) -> list[str]:
    """Build the full ordered predictor list: base + difference (+ Elo for
    feature_v2) + context.

    `tournament_dummy_columns` must come from
    `core.feature_engineering.tournament.encode_tournament_categories`,
    which determines the exact dummy column names/order present for a given
    dataset version.
    """

    context_features = ["neutral"] + tournament_dummy_columns

    if feature_version == ORIGINAL_FEATURE_VERSION:
        return BASE_FEATURES + DIFFERENCE_FEATURES + context_features
    if feature_version == ELO_FEATURE_VERSION:
        return BASE_FEATURES + DIFFERENCE_FEATURES + ELO_FEATURES + context_features
    raise ValueError(f"Unknown feature_version {feature_version!r}.")
