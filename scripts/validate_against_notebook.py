"""Stage 1 validation: Shared ML Core must reproduce the source notebook.

This script contains two independent implementations of the same pipeline:

1. `reference_*` functions: a self-contained, minimally-refactored transcription
   of `IPYNB_colab_code/fifa_world_cup_match_prediction.py`, written directly
   against pandas/numpy/sklearn WITHOUT importing anything from `core/`.
2. The actual `core/` package (the shared ML core being built for the Web and
   Desktop applications).

Both are run on the same built-in dataset, train the same Decision Tree
configuration, and predict the same set of hypothetical matches using the
dynamic interactive prediction workflow (Phase 13.2-13.4). If `core/` is a
faithful extraction of the notebook, every predicted probability must match
the reference implementation within floating-point tolerance.

Usage:
    .venv/Scripts/python.exe scripts/validate_against_notebook.py
"""

from __future__ import annotations

import sys
from collections import defaultdict, deque
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

RANDOM_STATE = 42
RECENT_MATCH_WINDOW = 5
BUILTIN_DATASET_PATH = PROJECT_ROOT / "datasets" / "builtin" / "results.csv"

TEST_MATCHUPS = [
    ("England", "Argentina", "United States", "FIFA World Cup"),
    ("Brazil", "Germany", "Brazil", "Friendly"),
    ("France", "Spain", "United States", "FIFA World Cup"),
    ("Atlantis FC", "France", "France", "FIFA World Cup qualification"),
]


# ============================================================
# REFERENCE IMPLEMENTATION (transcribed directly from the .py notebook,
# not importing core/, to serve as an independent ground truth)
# ============================================================


def reference_calculate_team_features(history, window_size=RECENT_MATCH_WINDOW):
    recent_matches = list(history)[-window_size:]
    matches_available = len(recent_matches)

    if matches_available == 0:
        return {
            "recent_win_rate": np.nan,
            "recent_draw_rate": np.nan,
            "avg_goals_scored": np.nan,
            "avg_goals_conceded": np.nan,
            "recent_goal_difference": np.nan,
            "matches_available": 0,
        }

    wins = sum(match["result"] == "Win" for match in recent_matches)
    draws = sum(match["result"] == "Draw" for match in recent_matches)
    goals_scored = [match["goals_scored"] for match in recent_matches]
    goals_conceded = [match["goals_conceded"] for match in recent_matches]

    return {
        "recent_win_rate": wins / matches_available,
        "recent_draw_rate": draws / matches_available,
        "avg_goals_scored": np.mean(goals_scored),
        "avg_goals_conceded": np.mean(goals_conceded),
        "recent_goal_difference": np.mean(goals_scored) - np.mean(goals_conceded),
        "matches_available": matches_available,
    }


def reference_generate_historical_features(match_data, window_size=RECENT_MATCH_WINDOW):
    data = match_data.sort_values("date").reset_index(drop=True).copy()
    team_history = defaultdict(lambda: deque(maxlen=window_size))
    feature_rows = []

    for current_date, daily_matches in data.groupby("date", sort=True):
        daily_updates = []
        for index, row in daily_matches.iterrows():
            home_team = row["home_team"]
            away_team = row["away_team"]
            home_features = reference_calculate_team_features(team_history[home_team], window_size)
            away_features = reference_calculate_team_features(team_history[away_team], window_size)

            feature_rows.append({
                "index": index,
                "home_recent_win_rate": home_features["recent_win_rate"],
                "away_recent_win_rate": away_features["recent_win_rate"],
                "home_recent_draw_rate": home_features["recent_draw_rate"],
                "away_recent_draw_rate": away_features["recent_draw_rate"],
                "home_avg_goals_scored": home_features["avg_goals_scored"],
                "away_avg_goals_scored": away_features["avg_goals_scored"],
                "home_avg_goals_conceded": home_features["avg_goals_conceded"],
                "away_avg_goals_conceded": away_features["avg_goals_conceded"],
                "home_recent_goal_difference": home_features["recent_goal_difference"],
                "away_recent_goal_difference": away_features["recent_goal_difference"],
                "home_matches_available": home_features["matches_available"],
                "away_matches_available": away_features["matches_available"],
            })

            if pd.notna(row["home_score"]) and pd.notna(row["away_score"]):
                daily_updates.append(row)

        for row in daily_updates:
            home_team = row["home_team"]
            away_team = row["away_team"]
            home_score = row["home_score"]
            away_score = row["away_score"]

            if home_score > away_score:
                home_result, away_result = "Win", "Loss"
            elif home_score < away_score:
                home_result, away_result = "Loss", "Win"
            else:
                home_result, away_result = "Draw", "Draw"

            team_history[home_team].append({"result": home_result, "goals_scored": home_score, "goals_conceded": away_score})
            team_history[away_team].append({"result": away_result, "goals_scored": away_score, "goals_conceded": home_score})

    feature_df = pd.DataFrame(feature_rows).set_index("index").sort_index()
    return pd.concat([data, feature_df], axis=1)


def reference_add_difference_features(data):
    data = data.copy()
    data["win_rate_difference"] = data["home_recent_win_rate"] - data["away_recent_win_rate"]
    data["draw_rate_difference"] = data["home_recent_draw_rate"] - data["away_recent_draw_rate"]
    data["goals_scored_difference"] = data["home_avg_goals_scored"] - data["away_avg_goals_scored"]
    data["goals_conceded_difference"] = data["home_avg_goals_conceded"] - data["away_avg_goals_conceded"]
    data["goal_difference_difference"] = data["home_recent_goal_difference"] - data["away_recent_goal_difference"]
    data["experience_difference"] = data["home_matches_available"] - data["away_matches_available"]
    return data


def reference_categorize_tournament(tournament):
    if tournament == "FIFA World Cup":
        return "World Cup"
    elif tournament == "FIFA World Cup qualification":
        return "World Cup Qualification"
    elif tournament == "Friendly":
        return "Friendly"
    else:
        return "Other Competitive"


def run_reference_pipeline(df_raw: pd.DataFrame):
    df = df_raw.copy()
    # NOTE: the notebook's original one-liner `pd.to_datetime(df["date"],
    # errors="coerce")` (no explicit format) infers a single date format
    # from the first row and silently turns ~99.7% of this dataset's dates
    # into NaT, because the built-in dataset mixes ISO and slash date
    # formats. This is the approved fix for Conflict B (Stage 0 audit) —
    # applied here too so this reference reflects the notebook's INTENDED
    # behaviour, not its accidental breakage on this specific dataset.
    df["date"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")
    df = df.sort_values("date").reset_index(drop=True)

    completed_matches = df[df["home_score"].notna() & df["away_score"].notna()].copy()
    prediction_fixtures = df[df["home_score"].isna() | df["away_score"].isna()].copy()
    completed_matches = completed_matches.drop_duplicates().reset_index(drop=True)

    def create_match_result(row):
        if row["home_score"] > row["away_score"]:
            return "Home Win"
        elif row["home_score"] == row["away_score"]:
            return "Draw"
        else:
            return "Home Loss"

    completed_matches["result"] = completed_matches.apply(create_match_result, axis=1)

    timeline = pd.concat([completed_matches, prediction_fixtures], ignore_index=True)
    timeline = timeline.sort_values("date").reset_index(drop=True)

    featured_data = reference_generate_historical_features(timeline)

    model_data = featured_data[featured_data["home_score"].notna() & featured_data["away_score"].notna()].copy()
    final_prediction_data = featured_data[featured_data["home_score"].isna() | featured_data["away_score"].isna()].copy()

    total_team_appearances = len(model_data) * 2
    overall_win_rate = (model_data["result"] != "Draw").sum() / total_team_appearances
    overall_draw_rate = (model_data["result"] == "Draw").sum() * 2 / total_team_appearances
    overall_avg_goals = (model_data["home_score"].sum() + model_data["away_score"].sum()) / total_team_appearances

    cold_start_fill_values = {
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

    model_data = model_data.fillna(value=cold_start_fill_values)
    final_prediction_data = final_prediction_data.fillna(value=cold_start_fill_values)

    model_data = reference_add_difference_features(model_data)
    final_prediction_data = reference_add_difference_features(final_prediction_data)

    model_data["tournament_category"] = model_data["tournament"].apply(reference_categorize_tournament)
    final_prediction_data["tournament_category"] = final_prediction_data["tournament"].apply(reference_categorize_tournament)

    model_data = pd.get_dummies(model_data, columns=["tournament_category"], prefix="tournament", dtype=int)
    final_prediction_data = pd.get_dummies(final_prediction_data, columns=["tournament_category"], prefix="tournament", dtype=int)

    tournament_dummy_columns = [c for c in model_data.columns if c.startswith("tournament_") and c != "tournament"]
    for column in tournament_dummy_columns:
        if column not in final_prediction_data.columns:
            final_prediction_data[column] = 0

    model_data["neutral"] = model_data["neutral"].astype(int)
    final_prediction_data["neutral"] = final_prediction_data["neutral"].astype(int)

    base_features = [
        "home_recent_win_rate", "away_recent_win_rate",
        "home_recent_draw_rate", "away_recent_draw_rate",
        "home_avg_goals_scored", "away_avg_goals_scored",
        "home_avg_goals_conceded", "away_avg_goals_conceded",
        "home_recent_goal_difference", "away_recent_goal_difference",
        "home_matches_available", "away_matches_available",
    ]
    difference_features = [
        "win_rate_difference", "draw_rate_difference",
        "goals_scored_difference", "goals_conceded_difference",
        "goal_difference_difference", "experience_difference",
    ]
    context_features = ["neutral"] + tournament_dummy_columns
    feature_columns = base_features + difference_features + context_features

    X_final_train = model_data[feature_columns].copy()
    y_final_train = model_data["result"].copy()

    final_decision_tree_model = DecisionTreeClassifier(
        max_depth=10, min_samples_split=20, min_samples_leaf=10, random_state=RANDOM_STATE
    )
    final_decision_tree_model.fit(X_final_train, y_final_train)

    def get_team_latest_history(team_name, full_timeline):
        team_matches = full_timeline[
            (full_timeline["home_team"] == team_name) | (full_timeline["away_team"] == team_name)
        ]
        if len(team_matches) == 0:
            return None
        latest_match = team_matches.iloc[-1]
        if latest_match["home_team"] == team_name:
            return {
                "win_rate": latest_match["home_recent_win_rate"],
                "draw_rate": latest_match["home_recent_draw_rate"],
                "goals_scored": latest_match["home_avg_goals_scored"],
                "goals_conceded": latest_match["home_avg_goals_conceded"],
                "goal_diff": latest_match["home_recent_goal_difference"],
                "exp": latest_match["home_matches_available"],
            }
        else:
            return {
                "win_rate": latest_match["away_recent_win_rate"],
                "draw_rate": latest_match["away_recent_draw_rate"],
                "goals_scored": latest_match["away_avg_goals_scored"],
                "goals_conceded": latest_match["away_avg_goals_conceded"],
                "goal_diff": latest_match["away_recent_goal_difference"],
                "exp": latest_match["away_matches_available"],
            }

    def fallback_if_none(hist_dict):
        if hist_dict is None:
            return {
                "win_rate": cold_start_fill_values["home_recent_win_rate"],
                "draw_rate": cold_start_fill_values["home_recent_draw_rate"],
                "goals_scored": cold_start_fill_values["home_avg_goals_scored"],
                "goals_conceded": cold_start_fill_values["home_avg_goals_conceded"],
                "goal_diff": cold_start_fill_values["home_recent_goal_difference"],
                "exp": 0,
            }
        return hist_dict

    def predict(home_team, away_team, host_country, tournament):
        neutral = int(home_team != host_country)
        home_hist = fallback_if_none(get_team_latest_history(home_team, featured_data))
        away_hist = fallback_if_none(get_team_latest_history(away_team, featured_data))

        dynamic_row = pd.DataFrame([{
            "home_recent_win_rate": home_hist["win_rate"],
            "away_recent_win_rate": away_hist["win_rate"],
            "home_recent_draw_rate": home_hist["draw_rate"],
            "away_recent_draw_rate": away_hist["draw_rate"],
            "home_avg_goals_scored": home_hist["goals_scored"],
            "away_avg_goals_scored": away_hist["goals_scored"],
            "home_avg_goals_conceded": home_hist["goals_conceded"],
            "away_avg_goals_conceded": away_hist["goals_conceded"],
            "home_recent_goal_difference": home_hist["goal_diff"],
            "away_recent_goal_difference": away_hist["goal_diff"],
            "home_matches_available": home_hist["exp"],
            "away_matches_available": away_hist["exp"],
            "neutral": neutral,
        }])

        dynamic_row = reference_add_difference_features(dynamic_row)
        tourn_cat = reference_categorize_tournament(tournament)
        for col in tournament_dummy_columns:
            dynamic_row[col] = 1 if col == f"tournament_{tourn_cat}" else 0

        X_dynamic = dynamic_row[feature_columns].copy()
        pred = final_decision_tree_model.predict(X_dynamic)[0]
        proba = final_decision_tree_model.predict_proba(X_dynamic)[0]
        classes = final_decision_tree_model.classes_
        prob_dict = {classes[i]: float(proba[i]) for i in range(len(classes))}
        return pred, prob_dict

    return {
        "feature_columns": feature_columns,
        "tournament_dummy_columns": tournament_dummy_columns,
        "cold_start_fill_values": cold_start_fill_values,
        "model_data_len": len(model_data),
        "predict": predict,
    }


# ============================================================
# CORE PACKAGE IMPLEMENTATION
# ============================================================


def run_core_pipeline(df_raw: pd.DataFrame):
    from core.dataset.io import load_raw_dataset  # noqa: F401 (path already loaded by caller)
    from core.models.definitions import make_decision_tree
    from core.models.training import retrain_on_all_completed_matches
    from core.pipeline import run_feature_pipeline
    from core.prediction.predictor import predict_match
    from core.prediction.team_state import build_team_latest_state_index

    pipeline_result = run_feature_pipeline(df_raw)

    model, scaler = retrain_on_all_completed_matches(
        model_type="decision_tree",
        model_factory=make_decision_tree,
        model_data=pipeline_result.model_data,
        feature_columns=pipeline_result.feature_columns,
    )

    team_state_index = build_team_latest_state_index(pipeline_result.featured_data)

    def predict(home_team, away_team, host_country, tournament):
        result = predict_match(
            home_team=home_team,
            away_team=away_team,
            host_country=host_country,
            tournament=tournament,
            model=model,
            scaler=scaler,
            team_state_index=team_state_index,
            cold_start_fill_values=pipeline_result.cold_start_fill_values,
            tournament_dummy_columns=pipeline_result.tournament_dummy_columns,
            feature_columns=pipeline_result.feature_columns,
        )
        return result.predicted_outcome, result.probabilities

    return {
        "feature_columns": pipeline_result.feature_columns,
        "tournament_dummy_columns": pipeline_result.tournament_dummy_columns,
        "cold_start_fill_values": pipeline_result.cold_start_fill_values,
        "model_data_len": len(pipeline_result.model_data),
        "predict": predict,
    }


# ============================================================
# COMPARISON
# ============================================================


def main() -> int:
    if not BUILTIN_DATASET_PATH.exists():
        print(f"FAIL: built-in dataset not found at {BUILTIN_DATASET_PATH}")
        return 1

    from core.dataset.io import load_raw_dataset

    # Both the reference and core pipelines load through the same function
    # so this comparison validates feature-engineering/modelling parity,
    # not CSV I/O quirks (see core/dataset/io.py for the encoding-fallback
    # rationale).
    df_raw = load_raw_dataset(BUILTIN_DATASET_PATH)
    print(f"Loaded builtin dataset: {len(df_raw):,} rows from {BUILTIN_DATASET_PATH}")

    print("\nRunning reference (notebook-transcribed) pipeline...")
    reference = run_reference_pipeline(df_raw)

    print("Running core/ package pipeline...")
    core_result = run_core_pipeline(df_raw)

    all_passed = True

    print("\n" + "=" * 70)
    print("STRUCTURAL PARITY")
    print("=" * 70)

    checks = [
        ("feature_columns", reference["feature_columns"] == core_result["feature_columns"]),
        ("tournament_dummy_columns", reference["tournament_dummy_columns"] == core_result["tournament_dummy_columns"]),
        ("model_data row count", reference["model_data_len"] == core_result["model_data_len"]),
        (
            "cold_start_fill_values",
            all(
                abs(reference["cold_start_fill_values"][k] - core_result["cold_start_fill_values"][k]) < 1e-12
                for k in reference["cold_start_fill_values"]
            ),
        ),
    ]

    for name, passed in checks:
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {name}")
        all_passed = all_passed and passed

    print("\n" + "=" * 70)
    print("PREDICTION PARITY (reference notebook logic vs core/ package)")
    print("=" * 70)

    for home, away, host, tournament in TEST_MATCHUPS:
        ref_pred, ref_proba = reference["predict"](home, away, host, tournament)
        core_pred, core_proba = core_result["predict"](home, away, host, tournament)

        outcome_match = ref_pred == core_pred
        proba_match = all(
            abs(ref_proba[k] - core_proba[k]) < 1e-9 for k in ref_proba
        )
        passed = outcome_match and proba_match

        status = "PASS" if passed else "FAIL"
        print(f"\n[{status}] {home} vs {away} (host={host}, tournament={tournament})")
        print(f"  reference: {ref_pred}  {ref_proba}")
        print(f"  core     : {core_pred}  {core_proba}")

        all_passed = all_passed and passed

    print("\n" + "=" * 70)
    if all_passed:
        print("ALL CHECKS PASSED: core/ is a faithful extraction of the notebook.")
    else:
        print("SOME CHECKS FAILED: core/ diverges from the notebook. Investigate before proceeding.")
    print("=" * 70)

    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
