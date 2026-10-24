"""Train a built-in model on the built-in dataset and export it as a
versioned model artifact under `models/` (model + metadata + pre-computed
team-state cache, so the first launch needs no feature-engineering pass).

This mirrors PHASE 13.1 of the source notebook (retrain the selected model
on every completed match) using the shared `core/` package exclusively —
nothing here reimplements feature engineering or training logic.

Usage:
    .venv/Scripts/python.exe scripts/train_and_export_model.py [built-in id] [--cache-only]

--cache-only regenerates the upset-history cache for an existing artifact
without retraining it (the shipped model files stay byte-identical).

Built-in ids (default: logistic_regression_elo_v1):
    decision_tree_v1            original notebook model, feature_v1
    logistic_regression_elo_v1  Elo-feature model, feature_v2
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.services.feature_service import TEAM_STATE_CACHE_FILENAME  # noqa: E402
from core.analytics.upset import (  # noqa: E402
    UPSET_HISTORY_CACHE_FILENAME,
    compute_upset_history,
    save_upset_history_cache,
)
from core.models.registry import load_model_artifact  # noqa: E402
from core.config import (  # noqa: E402
    CLASS_LABELS,
    ELO_FEATURE_VERSION,
    ORIGINAL_FEATURE_VERSION,
    TRAIN_RATIO,
)
from core.dataset.io import load_raw_dataset  # noqa: E402
from core.models.definitions import MODEL_FACTORIES  # noqa: E402
from core.models.registry import ModelMetadata, save_model_artifact  # noqa: E402
from core.models.split import chronological_train_test_split  # noqa: E402
from core.models.training import (  # noqa: E402
    evaluate_predictions,
    fit_model,
    predict_with_model,
    retrain_on_all_completed_matches,
)
from core.pipeline import run_feature_pipeline  # noqa: E402
from core.prediction.team_state import (  # noqa: E402
    build_team_latest_state_index,
    save_team_state_index_cache,
)

BUILTIN_DATASET_PATH = PROJECT_ROOT / "datasets" / "builtin" / "results.csv"
DATASET_VERSION = "builtin_v1"

# model_id -> (model_type, feature_version, output dir)
BUILTIN_MODELS = {
    "decision_tree_v1": (
        "decision_tree",
        ORIGINAL_FEATURE_VERSION,
        PROJECT_ROOT / "models" / "decision_tree" / "v1",
    ),
    "logistic_regression_elo_v1": (
        "logistic_regression",
        ELO_FEATURE_VERSION,
        PROJECT_ROOT / "models" / "logistic_regression" / "elo_v1",
    ),
}
DEFAULT_MODEL_ID = "logistic_regression_elo_v1"


def main(argv: list[str]) -> int:
    cache_only = "--cache-only" in argv
    positional = [arg for arg in argv[1:] if not arg.startswith("--")]
    model_id = positional[0] if positional else DEFAULT_MODEL_ID
    if model_id not in BUILTIN_MODELS:
        print(f"Unknown built-in id {model_id!r}. Choose one of {sorted(BUILTIN_MODELS)}.")
        return 2
    model_type, feature_version, output_dir = BUILTIN_MODELS[model_id]

    if cache_only:
        loaded = load_model_artifact(output_dir)
        pipeline_result = run_feature_pipeline(load_raw_dataset(BUILTIN_DATASET_PATH), feature_version)
        save_upset_history_cache(
            output_dir / UPSET_HISTORY_CACHE_FILENAME,
            compute_upset_history(
                loaded.model, loaded.scaler, pipeline_result.model_data, loaded.metadata.feature_columns
            ),
        )
        print(f"Upset-history cache written to {output_dir / UPSET_HISTORY_CACHE_FILENAME}")
        return 0

    print(f"Exporting {model_id} ({model_type}, {feature_version}) -> {output_dir}")
    print(f"Loading built-in dataset ({DATASET_VERSION}) from {BUILTIN_DATASET_PATH}")
    df_raw = load_raw_dataset(BUILTIN_DATASET_PATH)
    print(f"  {len(df_raw):,} rows")

    print("\nRunning feature engineering pipeline...")
    pipeline_result = run_feature_pipeline(df_raw, feature_version)
    print(f"  model_data    : {len(pipeline_result.model_data):,} completed matches")
    print(f"  feature_columns ({len(pipeline_result.feature_columns)}): "
          f"{pipeline_result.feature_columns}")

    # --- offline evaluation on a held-out chronological split, for the
    # model_versions.metrics record (mirrors Phases 7-9 of the notebook) ---
    print("\nEvaluating on a held-out chronological split (for metrics only; "
          "the deployed model below is retrained on ALL completed matches)...")

    X = pipeline_result.model_data[pipeline_result.feature_columns].copy()
    y = pipeline_result.model_data["result"].copy()
    split = chronological_train_test_split(pipeline_result.model_data, X, y, TRAIN_RATIO)
    print(f"  split date        : {split.split_date.date()}")

    model_factory = MODEL_FACTORIES[model_type]
    eval_model, eval_scaler = fit_model(model_type, model_factory(), split.X_train, split.y_train)
    overall_predictions, _ = predict_with_model(eval_model, eval_scaler, split.X_test)
    overall_metrics = evaluate_predictions(split.y_test, overall_predictions)
    world_cup_predictions, _ = predict_with_model(eval_model, eval_scaler, split.X_test_world_cup)
    world_cup_metrics = evaluate_predictions(split.y_test_world_cup, world_cup_predictions)
    print(f"  overall test    : {overall_metrics.to_dict()}")
    print(f"  world cup test  : {world_cup_metrics.to_dict()}")

    print("\nRetraining final model on all completed matches (deployment model)...")
    model, scaler = retrain_on_all_completed_matches(
        model_type=model_type,
        model_factory=model_factory,
        model_data=pipeline_result.model_data,
        feature_columns=pipeline_result.feature_columns,
    )

    metadata = ModelMetadata(
        model_id=model_id,
        model_type=model_type,
        dataset_version=DATASET_VERSION,
        feature_version=feature_version,
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

    save_model_artifact(output_dir, model, metadata, scaler)
    save_team_state_index_cache(
        output_dir / TEAM_STATE_CACHE_FILENAME,
        build_team_latest_state_index(pipeline_result.featured_data, pipeline_result.elo_ratings),
    )
    save_upset_history_cache(
        output_dir / UPSET_HISTORY_CACHE_FILENAME,
        compute_upset_history(model, scaler, pipeline_result.model_data, pipeline_result.feature_columns),
    )
    print(f"\nModel artifact saved to: {output_dir}")
    for path in sorted(output_dir.iterdir()):
        print(f"  - {path.name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
