"""Strict chronological train/test split and FIFA World Cup test subset.

Ported verbatim from the source notebook, PHASE 7.1, 7.2, and 7.4.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class ChronologicalSplit:
    X_train: pd.DataFrame
    X_test: pd.DataFrame
    y_train: pd.Series
    y_test: pd.Series
    train_metadata: pd.DataFrame
    test_metadata: pd.DataFrame
    split_date: pd.Timestamp

    X_test_world_cup: pd.DataFrame
    y_test_world_cup: pd.Series
    world_cup_test_metadata: pd.DataFrame


def chronological_train_test_split(
    model_data: pd.DataFrame,
    X: pd.DataFrame,
    y: pd.Series,
    train_ratio: float,
) -> ChronologicalSplit:
    """PHASE 7.1 — split by an approximate percentile date boundary.

    Every match strictly before `split_date` is training; every match on or
    after `split_date` is testing. This is a date-boundary split, not an
    exact-count split, so the resulting ratio is only approximately
    `train_ratio`.
    """

    approximate_split_index = int(len(model_data) * train_ratio)
    split_date = model_data.iloc[approximate_split_index]["date"]

    train_mask = model_data["date"] < split_date
    test_mask = model_data["date"] >= split_date

    X_train = X.loc[train_mask].copy()
    X_test = X.loc[test_mask].copy()
    y_train = y.loc[train_mask].copy()
    y_test = y.loc[test_mask].copy()

    train_metadata = model_data.loc[train_mask].copy()
    test_metadata = model_data.loc[test_mask].copy()

    # PHASE 7.2 — validate strict temporal separation
    latest_training_date = train_metadata["date"].max()
    earliest_testing_date = test_metadata["date"].min()
    if not (latest_training_date < earliest_testing_date):
        raise ValueError(
            "Temporal overlap detected between training and testing sets: "
            f"latest_training_date={latest_training_date}, "
            f"earliest_testing_date={earliest_testing_date}"
        )

    # PHASE 7.4 — FIFA World Cup test subset
    world_cup_test_mask = test_metadata["tournament"] == "FIFA World Cup"
    X_test_world_cup = X_test.loc[world_cup_test_mask].copy()
    y_test_world_cup = y_test.loc[world_cup_test_mask].copy()
    world_cup_test_metadata = test_metadata.loc[world_cup_test_mask].copy()

    return ChronologicalSplit(
        X_train=X_train,
        X_test=X_test,
        y_train=y_train,
        y_test=y_test,
        train_metadata=train_metadata,
        test_metadata=test_metadata,
        split_date=split_date,
        X_test_world_cup=X_test_world_cup,
        y_test_world_cup=y_test_world_cup,
        world_cup_test_metadata=world_cup_test_metadata,
    )
