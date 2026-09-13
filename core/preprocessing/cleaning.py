"""Data cleaning and target construction.

Ported verbatim from the source notebook, Phases 3 and 4:
- PHASE 3.1: convert date dtype
- PHASE 3.2: sort chronologically
- PHASE 3.3: separate completed matches from unscored fixtures
- PHASE 3.4: drop exact duplicates from completed matches
- PHASE 4.1: construct the match outcome target
- PHASE 4.2: validate target labels

No modelling logic lives here — only cleaning and the target label itself.
"""

from __future__ import annotations

import pandas as pd

from core.dataset.io import parse_date_column


def convert_date_column(df: pd.DataFrame) -> pd.DataFrame:
    """PHASE 3.1 — convert `date` to datetime64, invalid strings -> NaT.

    Delegates to `core.dataset.io.parse_date_column` (mixed-format safe)
    rather than the notebook's plain `pd.to_datetime(errors="coerce")` —
    see that module's docstring for why the naive call silently turns most
    rows' dates into NaT on the built-in (mixed ISO/slash format) dataset.
    """

    df = df.copy()
    df["date"] = parse_date_column(df["date"])
    return df


def sort_chronologically(df: pd.DataFrame) -> pd.DataFrame:
    """PHASE 3.2 — sort all matches earliest to latest."""

    return df.sort_values("date").reset_index(drop=True)


def split_completed_and_fixtures(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """PHASE 3.3 — separate completed matches from unscored fixtures.

    Returns
    -------
    (completed_matches, prediction_fixtures)
    """

    completed_matches = df[
        df["home_score"].notna() & df["away_score"].notna()
    ].copy()

    prediction_fixtures = df[
        df["home_score"].isna() | df["away_score"].isna()
    ].copy()

    return completed_matches, prediction_fixtures


def drop_exact_duplicates(completed_matches: pd.DataFrame) -> pd.DataFrame:
    """PHASE 3.4 — remove exact duplicate rows from completed matches."""

    return completed_matches.drop_duplicates().reset_index(drop=True)


def create_match_result(row: pd.Series) -> str:
    """PHASE 4.1 — construct the 3-class target from the recorded score.

    Home Win  : home_score > away_score
    Draw      : home_score == away_score
    Home Loss : home_score < away_score
    """

    if row["home_score"] > row["away_score"]:
        return "Home Win"
    elif row["home_score"] == row["away_score"]:
        return "Draw"
    else:
        return "Home Loss"


def add_match_result_target(completed_matches: pd.DataFrame) -> pd.DataFrame:
    """Apply create_match_result() to every completed match."""

    completed_matches = completed_matches.copy()
    completed_matches["result"] = completed_matches.apply(
        create_match_result, axis=1
    )
    return completed_matches


def validate_match_result_target(completed_matches: pd.DataFrame) -> bool:
    """PHASE 4.2 — verify every `result` label matches its recorded score.

    Returns True only if every single row is labelled correctly.
    """

    correct = (
        (
            (completed_matches["home_score"] > completed_matches["away_score"])
            & (completed_matches["result"] == "Home Win")
        )
        | (
            (completed_matches["home_score"] == completed_matches["away_score"])
            & (completed_matches["result"] == "Draw")
        )
        | (
            (completed_matches["home_score"] < completed_matches["away_score"])
            & (completed_matches["result"] == "Home Loss")
        )
    )

    return bool(correct.all())
