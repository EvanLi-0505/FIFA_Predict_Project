"""End-to-end feature engineering pipeline orchestration.

Wires together preprocessing, historical feature engineering, cold-start
treatment, difference features, and tournament encoding in the exact order
used by the source notebook (Phases 3 through 6.8). This is the single
function both training and prediction code should call to go from a raw
`results.csv`-shaped dataframe to a fully engineered feature set.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from core.feature_engineering.cold_start import (
    apply_cold_start,
    compute_cold_start_fill_values,
)
from core.feature_engineering.differences import add_difference_features
from core.feature_engineering.team_history import generate_historical_features
from core.feature_engineering.tournament import (
    encode_neutral,
    encode_tournament_categories,
)
from core.preprocessing.cleaning import (
    add_match_result_target,
    convert_date_column,
    drop_exact_duplicates,
    sort_chronologically,
    split_completed_and_fixtures,
    validate_match_result_target,
)
from core.schemas.feature_schema import build_feature_columns


@dataclass
class PipelineResult:
    """Every intermediate/final artifact needed for training and prediction."""

    featured_data: pd.DataFrame
    """Full chronological timeline with historical features attached
    (completed matches + unscored fixtures), BEFORE cold-start/difference/
    tournament encoding. Used by `core.prediction.team_state` to look up a
    team's most recent feature state."""

    model_data: pd.DataFrame
    """Completed matches only, fully engineered: cold-start filled,
    difference features added, tournament one-hot encoded, neutral encoded.
    Ready for `X = model_data[feature_columns]`, `y = model_data["result"]`."""

    final_prediction_data: pd.DataFrame
    """Unscored fixtures, engineered the same way as model_data (kept for
    parity with the notebook; the production predictor uses dynamic
    interactive prediction rather than this batch fixture set — see
    Development Prompt.md Stage 0 audit, Conflict A)."""

    feature_columns: list[str]
    """Canonical, ordered list of the 23 predictor variables for this
    dataset version. The Decision Tree is order-sensitive — always use this
    list, never re-derive it."""

    tournament_dummy_columns: list[str]

    cold_start_fill_values: dict[str, float]
    """Must be serialized alongside any trained model — required to featurise
    future matches involving teams unseen at training time."""


def build_completed_matches(df_raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run Phases 3.1-4.2 only: cleaning + target construction, no feature
    engineering. Shared by `run_feature_pipeline` and by
    `core.analytics.team_stats`, which needs cleaned match records (with
    dates parsed and the `result` target attached) but not the expensive
    historical-feature-engineering pass.

    Returns
    -------
    (completed_matches, prediction_fixtures)
    """

    df = convert_date_column(df_raw)
    df = sort_chronologically(df)

    completed_matches, prediction_fixtures = split_completed_and_fixtures(df)
    completed_matches = drop_exact_duplicates(completed_matches)

    completed_matches = add_match_result_target(completed_matches)
    if not validate_match_result_target(completed_matches):
        raise ValueError(
            "Target label validation failed: at least one `result` label "
            "does not match its recorded home_score/away_score."
        )

    return completed_matches, prediction_fixtures


def run_feature_pipeline(df_raw: pd.DataFrame) -> PipelineResult:
    """Run the full Phase 3-6.8 pipeline on a raw results.csv dataframe."""

    completed_matches, prediction_fixtures = build_completed_matches(df_raw)

    timeline = pd.concat(
        [completed_matches, prediction_fixtures], ignore_index=True
    )
    timeline = timeline.sort_values("date").reset_index(drop=True)

    featured_data = generate_historical_features(timeline)

    model_data = featured_data[
        featured_data["home_score"].notna() & featured_data["away_score"].notna()
    ].copy()
    final_prediction_data = featured_data[
        featured_data["home_score"].isna() | featured_data["away_score"].isna()
    ].copy()

    cold_start_fill_values = compute_cold_start_fill_values(model_data)
    model_data = apply_cold_start(model_data, cold_start_fill_values)
    final_prediction_data = apply_cold_start(
        final_prediction_data, cold_start_fill_values
    )

    model_data = add_difference_features(model_data)
    final_prediction_data = add_difference_features(final_prediction_data)

    model_data, final_prediction_data, tournament_dummy_columns = (
        encode_tournament_categories(model_data, final_prediction_data)
    )

    model_data = encode_neutral(model_data)
    final_prediction_data = encode_neutral(final_prediction_data)

    feature_columns = build_feature_columns(tournament_dummy_columns)

    _validate_final_matrix(model_data, feature_columns)

    return PipelineResult(
        featured_data=featured_data,
        model_data=model_data,
        final_prediction_data=final_prediction_data,
        feature_columns=feature_columns,
        tournament_dummy_columns=tournament_dummy_columns,
        cold_start_fill_values=cold_start_fill_values,
    )


def _validate_final_matrix(model_data: pd.DataFrame, feature_columns: list[str]) -> None:
    """PHASE 6.8 validation: no missing/infinite predictor values."""

    X = model_data[feature_columns]

    missing_count = int(X.isnull().sum().sum())
    if missing_count:
        raise ValueError(
            f"Final feature matrix contains {missing_count} missing value(s) "
            "after cold-start treatment."
        )

    infinite_count = int(
        np.isinf(X.select_dtypes(include=np.number)).sum().sum()
    )
    if infinite_count:
        raise ValueError(
            f"Final feature matrix contains {infinite_count} infinite value(s)."
        )
