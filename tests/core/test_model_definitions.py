"""Every registered model factory must actually train and predict through
the shared `fit_model` / `predict_with_model` plumbing (Stage 4 follow-up:
the user asked for more model choices in the Model Management UI).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from core.models.definitions import MODEL_FACTORIES
from core.models.training import fit_model, predict_with_model


@pytest.fixture
def synthetic_data():
    rng = np.random.default_rng(42)
    n_rows = 300
    X = pd.DataFrame(
        rng.normal(size=(n_rows, 8)),
        columns=[f"feature_{i}" for i in range(8)],
    )
    # Make the label loosely a function of the features so models have
    # something real to learn, rather than pure noise.
    score = X["feature_0"] + X["feature_1"] - X["feature_2"]
    y = pd.Series(
        np.select(
            [score > 0.5, score < -0.5],
            ["Home Win", "Home Loss"],
            default="Draw",
        )
    )
    return X, y


@pytest.mark.parametrize("model_type", sorted(MODEL_FACTORIES))
def test_every_model_factory_trains_and_predicts(model_type, synthetic_data):
    X, y = synthetic_data
    model_factory = MODEL_FACTORIES[model_type]

    model, scaler = fit_model(model_type, model_factory(), X, y)
    predictions, probabilities = predict_with_model(model, scaler, X)

    assert len(predictions) == len(X)
    assert probabilities.shape == (len(X), 3)
    assert np.allclose(probabilities.sum(axis=1), 1.0, atol=1e-6)
    assert set(predictions).issubset({"Home Win", "Draw", "Home Loss"})
