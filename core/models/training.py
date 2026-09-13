"""Model training and evaluation.

Ported verbatim from the source notebook, Phases 8-11 (training +
overall/World-Cup evaluation) and PHASE 13.1 (final retraining on all
completed matches for production inference).
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sklearn.base import ClassifierMixin
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.preprocessing import StandardScaler

from core.models.definitions import MODELS_REQUIRING_SCALING


@dataclass
class EvaluationMetrics:
    accuracy: float
    macro_precision: float
    macro_recall: float
    macro_f1: float

    def to_dict(self) -> dict[str, float]:
        return {
            "accuracy": self.accuracy,
            "macro_precision": self.macro_precision,
            "macro_recall": self.macro_recall,
            "macro_f1": self.macro_f1,
        }


def evaluate_predictions(y_true: pd.Series, y_pred) -> EvaluationMetrics:
    """Compute the exact metric set used throughout Phases 8-11."""

    return EvaluationMetrics(
        accuracy=accuracy_score(y_true, y_pred),
        macro_precision=precision_score(
            y_true, y_pred, average="macro", zero_division=0
        ),
        macro_recall=recall_score(y_true, y_pred, average="macro", zero_division=0),
        macro_f1=f1_score(y_true, y_pred, average="macro", zero_division=0),
    )


def fit_model(
    model_type: str,
    model: ClassifierMixin,
    X_train: pd.DataFrame,
    y_train: pd.Series,
) -> tuple[ClassifierMixin, StandardScaler | None]:
    """Fit a model, applying StandardScaler only for model types that need it
    (Logistic Regression — PHASE 8.1). Decision Tree / Random Forest train on
    raw features, matching Phases 9.2 and 10.1.

    Returns
    -------
    (fitted_model, scaler_or_none)
        `scaler_or_none` must be reused (via `.transform`, never re-fit) on
        any data evaluated or predicted with this model.
    """

    if model_type in MODELS_REQUIRING_SCALING:
        scaler = StandardScaler()
        X_train_transformed = scaler.fit_transform(X_train)
        model.fit(X_train_transformed, y_train)
        return model, scaler

    model.fit(X_train, y_train)
    return model, None


def predict_with_model(
    model: ClassifierMixin, scaler: StandardScaler | None, X: pd.DataFrame
):
    """Predict classes and probabilities, applying `scaler.transform` first
    if the model requires scaling."""

    X_input = scaler.transform(X) if scaler is not None else X
    predictions = model.predict(X_input)
    probabilities = model.predict_proba(X_input)
    return predictions, probabilities


def retrain_on_all_completed_matches(
    model_type: str,
    model_factory,
    model_data: pd.DataFrame,
    feature_columns: list[str],
) -> tuple[ClassifierMixin, StandardScaler | None]:
    """PHASE 13.1 — retrain the selected model on every completed match.

    This is the model that serves live/dynamic predictions in production,
    not the train-split-only model used for offline evaluation.
    """

    X_final_train = model_data[feature_columns].copy()
    y_final_train = model_data["result"].copy()

    model = model_factory()
    return fit_model(model_type, model, X_final_train, y_final_train)
