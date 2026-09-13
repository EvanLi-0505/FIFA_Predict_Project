"""Regression test: core/ must keep reproducing the notebook's methodology.

This intentionally re-checks a subset of what
`scripts/validate_against_notebook.py` checks, packaged as a pytest test so
it runs in CI / pre-commit rather than only being run manually.
"""

from __future__ import annotations

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BUILTIN_DATASET_PATH = PROJECT_ROOT / "datasets" / "builtin" / "results.csv"


@pytest.fixture(scope="module")
def pipeline_result():
    from core.dataset.io import load_raw_dataset
    from core.pipeline import run_feature_pipeline

    df_raw = load_raw_dataset(BUILTIN_DATASET_PATH)
    return run_feature_pipeline(df_raw)


def test_feature_columns_are_23_in_documented_order(pipeline_result):
    expected = [
        "home_recent_win_rate", "away_recent_win_rate",
        "home_recent_draw_rate", "away_recent_draw_rate",
        "home_avg_goals_scored", "away_avg_goals_scored",
        "home_avg_goals_conceded", "away_avg_goals_conceded",
        "home_recent_goal_difference", "away_recent_goal_difference",
        "home_matches_available", "away_matches_available",
        "win_rate_difference", "draw_rate_difference",
        "goals_scored_difference", "goals_conceded_difference",
        "goal_difference_difference", "experience_difference",
        "neutral",
        "tournament_Friendly", "tournament_Other Competitive",
        "tournament_World Cup", "tournament_World Cup Qualification",
    ]
    assert pipeline_result.feature_columns == expected


def test_no_missing_or_infinite_values_in_final_matrix(pipeline_result):
    import numpy as np

    X = pipeline_result.model_data[pipeline_result.feature_columns]
    assert X.isnull().sum().sum() == 0
    assert np.isinf(X.select_dtypes(include=np.number)).sum().sum() == 0


def test_first_chronological_match_has_zero_history(pipeline_result):
    first_match = pipeline_result.featured_data.iloc[0]
    assert first_match["home_matches_available"] == 0
    assert first_match["away_matches_available"] == 0


def test_date_parsing_does_not_drop_mixed_format_rows(pipeline_result):
    # Regression guard for the mixed ISO/slash date format bug found during
    # Stage 1 validation: naive pd.to_datetime(errors="coerce") without an
    # explicit format silently turned ~99.7% of this dataset's dates into
    # NaT. This must never happen again.
    assert pipeline_result.featured_data["date"].isnull().sum() == 0


def test_decision_tree_prediction_is_deterministic(pipeline_result):
    from core.models.definitions import make_decision_tree
    from core.models.training import retrain_on_all_completed_matches
    from core.prediction.predictor import predict_match
    from core.prediction.team_state import build_team_latest_state_index

    model, scaler = retrain_on_all_completed_matches(
        model_type="decision_tree",
        model_factory=make_decision_tree,
        model_data=pipeline_result.model_data,
        feature_columns=pipeline_result.feature_columns,
    )
    team_state_index = build_team_latest_state_index(pipeline_result.featured_data)

    result_a = predict_match(
        home_team="England",
        away_team="Argentina",
        host_country="United States",
        tournament="FIFA World Cup",
        model=model,
        scaler=scaler,
        team_state_index=team_state_index,
        cold_start_fill_values=pipeline_result.cold_start_fill_values,
        tournament_dummy_columns=pipeline_result.tournament_dummy_columns,
        feature_columns=pipeline_result.feature_columns,
    )
    result_b = predict_match(
        home_team="England",
        away_team="Argentina",
        host_country="United States",
        tournament="FIFA World Cup",
        model=model,
        scaler=scaler,
        team_state_index=team_state_index,
        cold_start_fill_values=pipeline_result.cold_start_fill_values,
        tournament_dummy_columns=pipeline_result.tournament_dummy_columns,
        feature_columns=pipeline_result.feature_columns,
    )

    assert result_a.predicted_outcome == result_b.predicted_outcome
    assert result_a.probabilities == result_b.probabilities


def test_cold_start_team_falls_back_gracefully(pipeline_result):
    from core.models.definitions import make_decision_tree
    from core.models.training import retrain_on_all_completed_matches
    from core.prediction.predictor import predict_match
    from core.prediction.team_state import build_team_latest_state_index

    model, scaler = retrain_on_all_completed_matches(
        model_type="decision_tree",
        model_factory=make_decision_tree,
        model_data=pipeline_result.model_data,
        feature_columns=pipeline_result.feature_columns,
    )
    team_state_index = build_team_latest_state_index(pipeline_result.featured_data)

    result = predict_match(
        home_team="A Brand New Nation FC",
        away_team="Another New Nation FC",
        host_country="A Brand New Nation FC",
        tournament="Friendly",
        model=model,
        scaler=scaler,
        team_state_index=team_state_index,
        cold_start_fill_values=pipeline_result.cold_start_fill_values,
        tournament_dummy_columns=pipeline_result.tournament_dummy_columns,
        feature_columns=pipeline_result.feature_columns,
    )

    assert sum(result.probabilities.values()) == pytest.approx(1.0)
    assert result.predicted_outcome in {"Home Win", "Draw", "Home Loss"}
