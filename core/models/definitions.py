"""Model factory functions with hyperparameters ported verbatim from the
source notebook (Phases 8.2, 9.1, 10.1).

`PRODUCTION_MODEL_TYPE` records which model type is the validated default
(Development Prompt.md Section 17). Do not change hyperparameters here
without explicit approval — they are part of the validated methodology.
"""

from __future__ import annotations

from sklearn.ensemble import (
    AdaBoostClassifier,
    GradientBoostingClassifier,
    RandomForestClassifier,
)
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier

from core.config import RANDOM_STATE

PRODUCTION_MODEL_TYPE = "decision_tree"


def make_logistic_regression() -> LogisticRegression:
    """PHASE 8.2 configuration. Requires StandardScaler-transformed input."""

    return LogisticRegression(max_iter=2000, random_state=RANDOM_STATE)


def make_decision_tree() -> DecisionTreeClassifier:
    """PHASE 9.1 configuration — the validated production model.

    Takes raw (unscaled) feature input; do not apply StandardScaler.
    """

    return DecisionTreeClassifier(
        max_depth=10,
        min_samples_split=20,
        min_samples_leaf=10,
        random_state=RANDOM_STATE,
    )


def make_random_forest() -> RandomForestClassifier:
    """PHASE 10.1 configuration — kept for comparison/feature-importance only.

    Takes raw (unscaled) feature input; do not apply StandardScaler.
    """

    return RandomForestClassifier(
        n_estimators=300,
        max_depth=15,
        min_samples_split=10,
        min_samples_leaf=5,
        max_features="sqrt",
        n_jobs=-1,
        random_state=RANDOM_STATE,
    )


def make_gradient_boosting() -> GradientBoostingClassifier:
    """Added by user request after Stage 4 review, not part of the original
    notebook methodology — comparison/experimentation only (Development
    Prompt.md Section 17). Takes raw (unscaled) feature input.
    """

    return GradientBoostingClassifier(
        n_estimators=100,
        max_depth=3,
        learning_rate=0.1,
        random_state=RANDOM_STATE,
    )


def make_knn() -> KNeighborsClassifier:
    """Added by user request after Stage 4 review — comparison only.
    Requires StandardScaler-transformed input (distance-based model).
    """

    return KNeighborsClassifier(n_neighbors=15)


def make_naive_bayes() -> GaussianNB:
    """Added by user request after Stage 4 review — comparison only.
    Takes raw (unscaled) feature input.
    """

    return GaussianNB()


def make_adaboost() -> AdaBoostClassifier:
    """Added by user request after Stage 4 review — comparison only.
    Takes raw (unscaled) feature input.
    """

    return AdaBoostClassifier(n_estimators=100, random_state=RANDOM_STATE)


MODEL_FACTORIES = {
    "logistic_regression": make_logistic_regression,
    "decision_tree": make_decision_tree,
    "random_forest": make_random_forest,
    "gradient_boosting": make_gradient_boosting,
    "knn": make_knn,
    "naive_bayes": make_naive_bayes,
    "adaboost": make_adaboost,
}

# Model types that require StandardScaler-transformed input (fit on train only)
MODELS_REQUIRING_SCALING = {"logistic_regression", "knn"}
