"""Tournament categorisation, one-hot encoding, and neutral-venue encoding.

Ported verbatim from the source notebook, PHASE 6.4 (`categorize_tournament`),
PHASE 6.5 (one-hot encoding), and PHASE 6.6 (neutral encoding).
"""

from __future__ import annotations

import pandas as pd


def categorize_tournament(tournament: str) -> str:
    """Group a raw tournament name into one of four broad categories."""

    if tournament == "FIFA World Cup":
        return "World Cup"
    elif tournament == "FIFA World Cup qualification":
        return "World Cup Qualification"
    elif tournament == "Friendly":
        return "Friendly"
    else:
        return "Other Competitive"


def encode_tournament_categories(
    model_data: pd.DataFrame, final_prediction_data: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    """One-hot encode tournament categories on both modelling frames.

    `final_prediction_data` is aligned to contain every dummy column that
    appears in `model_data`, filled with 0 for any category absent from the
    prediction fixtures (matches PHASE 6.5's alignment step exactly).

    Returns
    -------
    (model_data, final_prediction_data, tournament_dummy_columns)
    """

    model_data = model_data.copy()
    final_prediction_data = final_prediction_data.copy()

    model_data["tournament_category"] = model_data["tournament"].apply(
        categorize_tournament
    )
    final_prediction_data["tournament_category"] = final_prediction_data[
        "tournament"
    ].apply(categorize_tournament)

    model_data = pd.get_dummies(
        model_data, columns=["tournament_category"], prefix="tournament", dtype=int
    )
    final_prediction_data = pd.get_dummies(
        final_prediction_data,
        columns=["tournament_category"],
        prefix="tournament",
        dtype=int,
    )

    tournament_dummy_columns = [
        column
        for column in model_data.columns
        if column.startswith("tournament_") and column != "tournament"
    ]

    for column in tournament_dummy_columns:
        if column not in final_prediction_data.columns:
            final_prediction_data[column] = 0

    return model_data, final_prediction_data, tournament_dummy_columns


def encode_neutral(data: pd.DataFrame) -> pd.DataFrame:
    """Convert the boolean `neutral` column to binary 0/1 (int)."""

    data = data.copy()
    data["neutral"] = data["neutral"].astype(int)
    return data
