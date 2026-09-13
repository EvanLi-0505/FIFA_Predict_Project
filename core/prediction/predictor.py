"""Dynamic interactive match prediction.

Ported from the source notebook, PHASE 13.2-13.4 ("DYNAMIC FEATURE
EXTRACTION LOGIC" / "INTERACTIVE MATCH INPUT & FEATURE CONSTRUCTION" /
"DYNAMIC MODEL INFERENCE"). This is the workflow confirmed as the migration
target in the Stage 0 audit (see Development Prompt.md, Conflict B
resolution): the user supplies home team, away team, host country, and
tournament; the system looks up each team's most recent historical feature
state and predicts the match outcome — it does NOT batch-predict a fixed
list of known future fixtures.

The only behavioural change from the notebook is replacing the interactive
`input()` calls with explicit function parameters, and replacing the
per-request O(n) `get_team_latest_history` scan with an O(1) lookup into a
precomputed `team_state_index` (see `core.prediction.team_state`).
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sklearn.base import ClassifierMixin
from sklearn.preprocessing import StandardScaler

from core.feature_engineering.differences import add_difference_features
from core.feature_engineering.tournament import categorize_tournament
from core.models.training import predict_with_model
from core.prediction.team_state import TeamState


@dataclass
class PredictionResult:
    home_team: str
    away_team: str
    host_country: str
    tournament: str
    tournament_category: str
    neutral: int
    probabilities: dict[str, float]
    predicted_outcome: str
    confidence: float


def _resolve_team_state(
    team_name: str, team_state_index: dict[str, TeamState], cold_start_fill_values: dict
) -> TeamState:
    """Return a team's latest known state, or the cold-start fallback."""

    state = team_state_index.get(team_name)
    if state is not None:
        return state

    return {
        "win_rate": cold_start_fill_values["home_recent_win_rate"],
        "draw_rate": cold_start_fill_values["home_recent_draw_rate"],
        "goals_scored": cold_start_fill_values["home_avg_goals_scored"],
        "goals_conceded": cold_start_fill_values["home_avg_goals_conceded"],
        "goal_diff": cold_start_fill_values["home_recent_goal_difference"],
        "exp": 0,
    }


def build_dynamic_feature_row(
    home_team: str,
    away_team: str,
    host_country: str,
    tournament: str,
    team_state_index: dict[str, TeamState],
    cold_start_fill_values: dict,
    tournament_dummy_columns: list[str],
    feature_columns: list[str],
) -> tuple[pd.DataFrame, int, str]:
    """Construct a single-row feature matrix for a hypothetical match.

    Returns (X_dynamic, neutral, tournament_category).
    """

    neutral = int(home_team != host_country)

    home_state = _resolve_team_state(home_team, team_state_index, cold_start_fill_values)
    away_state = _resolve_team_state(away_team, team_state_index, cold_start_fill_values)

    dynamic_row = pd.DataFrame(
        [
            {
                "home_recent_win_rate": home_state["win_rate"],
                "away_recent_win_rate": away_state["win_rate"],
                "home_recent_draw_rate": home_state["draw_rate"],
                "away_recent_draw_rate": away_state["draw_rate"],
                "home_avg_goals_scored": home_state["goals_scored"],
                "away_avg_goals_scored": away_state["goals_scored"],
                "home_avg_goals_conceded": home_state["goals_conceded"],
                "away_avg_goals_conceded": away_state["goals_conceded"],
                "home_recent_goal_difference": home_state["goal_diff"],
                "away_recent_goal_difference": away_state["goal_diff"],
                "home_matches_available": home_state["exp"],
                "away_matches_available": away_state["exp"],
                "neutral": neutral,
            }
        ]
    )

    dynamic_row = add_difference_features(dynamic_row)

    tournament_category = categorize_tournament(tournament)
    for column in tournament_dummy_columns:
        dynamic_row[column] = 1 if column == f"tournament_{tournament_category}" else 0

    X_dynamic = dynamic_row[feature_columns].copy()

    return X_dynamic, neutral, tournament_category


def predict_match(
    home_team: str,
    away_team: str,
    host_country: str,
    tournament: str,
    model: ClassifierMixin,
    scaler: StandardScaler | None,
    team_state_index: dict[str, TeamState],
    cold_start_fill_values: dict,
    tournament_dummy_columns: list[str],
    feature_columns: list[str],
) -> PredictionResult:
    """Predict the outcome of a hypothetical match from the home team's
    perspective (Home Win / Draw / Home Loss), with class probabilities."""

    X_dynamic, neutral, tournament_category = build_dynamic_feature_row(
        home_team=home_team,
        away_team=away_team,
        host_country=host_country,
        tournament=tournament,
        team_state_index=team_state_index,
        cold_start_fill_values=cold_start_fill_values,
        tournament_dummy_columns=tournament_dummy_columns,
        feature_columns=feature_columns,
    )

    predictions, probabilities = predict_with_model(model, scaler, X_dynamic)

    predicted_outcome = predictions[0]
    class_probabilities = probabilities[0]
    classes = model.classes_

    probability_by_class = {
        classes[i]: float(class_probabilities[i]) for i in range(len(classes))
    }

    return PredictionResult(
        home_team=home_team,
        away_team=away_team,
        host_country=host_country,
        tournament=tournament,
        tournament_category=tournament_category,
        neutral=neutral,
        probabilities=probability_by_class,
        predicted_outcome=predicted_outcome,
        confidence=float(max(class_probabilities)),
    )
