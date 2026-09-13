"""Train the production Decision Tree on the built-in dataset and export it
as a versioned model artifact under `models/`.

This mirrors PHASE 13.1 of the source notebook (retrain the selected model
on every completed match) using the shared `core/` package exclusively —
nothing here reimplements feature engineering or training logic.

Usage:
    .venv/Scripts/python.exe scripts/train_and_export_model.py
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.config import CLASS_LABELS, FEATURE_VERSION  # noqa: E402
from core.dataset.io import load_raw_dataset  # noqa: E402
from core.models.definitions import PRODUCTION_MODEL_TYPE, make_decision_tree  # noqa: E402
from core.models.registry import ModelMetadata, save_model_artifact  # noqa: E402
from core.models.split import chronological_train_test_split  # noqa: E402
from core.models.training import (  # noqa: E402
    evaluate_predictions,
    predict_with_model,
    retrain_on_all_completed_matches,
)
from core.pipeline import run_feature_pipeline  # noqa: E402
from core.config import TRAIN_RATIO  # noqa: E402

BUILTIN_DATASET_PATH = PROJECT_ROOT / "datasets" / "builtin" / "results.csv"
DATASET_VERSION = "builtin_v1"
MODEL_ID = "decision_tree_v1"
OUTPUT_DIR = PROJECT_ROOT / "models" / "decision_tree" / "v1"


def main() -> int:
    print(f"Loading built-in dataset ({DATASET_VERSION}) from {BUILTIN_DATASET_PATH}")
    df_raw = load_raw_dataset(BUILTIN_DATASET_PATH)
    print(f"  {len(df_raw):,} rows")

    print("\nRunning feature engineering pipeline...")
    pipeline_result = run_feature_pipeline(df_raw)
    print(f"  featured_data : {len(pipeline_result.featured_data):,} rows")
    print(f"  model_data    : {len(pipeline_result.model_data):,} completed matches")
    print(f"  feature_columns ({len(pipeline_result.feature_columns)}): "
          f"{pipeline_result.feature_columns}")

    # --- offline evaluation on a held-out chronological split, for the
    # model_versions.metrics record (mirrors Phases 7-9 of the notebook) ---
    print("\nEvaluating on a held-out chronological split (for metrics only; "
          "the deployed model below is retrained on ALL completed matches)...")

    X = pipeline_result.model_data[pipeline_result.feature_columns].copy()
    y = pipeline_result.model_data["result"].copy()

    split = chronological_train_test_split(
        pipeline_result.model_data, X, y, TRAIN_RATIO
    )
    print(f"  split date        : {split.split_date.date()}")
    print(f"  training records  : {len(split.X_train):,}")
    print(f"  testing records   : {len(split.X_test):,}")
    print(f"  World Cup test set: {len(split.X_test_world_cup):,}")

    eval_model = make_decision_tree()
    eval_model.fit(split.X_train, split.y_train)

    overall_predictions, _ = predict_with_model(eval_model, None, split.X_test)
    overall_metrics = evaluate_predictions(split.y_test, overall_predictions)

    world_cup_predictions, _ = predict_with_model(
        eval_model, None, split.X_test_world_cup
    )
    world_cup_metrics = evaluate_predictions(
        split.y_test_world_cup, world_cup_predictions
    )

    print(f"  overall test    : {overall_metrics.to_dict()}")
    print(f"  world cup test  : {world_cup_metrics.to_dict()}")

    # --- retrain on ALL completed matches for production deployment
    # (PHASE 13.1) ---
    print("\nRetraining final model on all completed matches (deployment model)...")
    model, scaler = retrain_on_all_completed_matches(
        model_type=PRODUCTION_MODEL_TYPE,
        model_factory=make_decision_tree,
        model_data=pipeline_result.model_data,
        feature_columns=pipeline_result.feature_columns,
    )
    print(f"  trained on {len(pipeline_result.model_data):,} matches")

    metadata = ModelMetadata(
        model_id=MODEL_ID,
        model_type=PRODUCTION_MODEL_TYPE,
        dataset_version=DATASET_VERSION,
        feature_version=FEATURE_VERSION,
        feature_columns=pipeline_result.feature_columns,
        tournament_dummy_columns=pipeline_result.tournament_dummy_columns,
        cold_start_fill_values=pipeline_result.cold_start_fill_values,
        class_labels=CLASS_LABELS,
        training_timestamp=datetime.now(timezone.utc).isoformat(),
        metrics={
            "held_out_split_date": str(split.split_date.date()),
            "overall_test": overall_metrics.to_dict(),
            "world_cup_test": world_cup_metrics.to_dict(),
            "trained_on_records": len(pipeline_result.model_data),
        },
    )

    save_model_artifact(OUTPUT_DIR, model, metadata, scaler)
    print(f"\nModel artifact saved to: {OUTPUT_DIR}")
    print("  - model.joblib")
    print("  - metadata.json")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
