"""Dataset validation for uploaded (non-built-in) datasets.

Implements Development Prompt.md Section 14 ("DATASET VALIDATION"). A user
upload must pass all checks here before it may become the active dataset.
Nothing here mutates the uploaded file — validation only inspects it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from core.config import REQUIRED_RAW_COLUMNS
from core.dataset.io import parse_dates_safely


@dataclass
class ValidationIssue:
    field: str
    message: str


@dataclass
class ValidationReport:
    is_valid: bool
    row_count: int
    issues: list[ValidationIssue] = field(default_factory=list)

    def add_error(self, field_name: str, message: str) -> None:
        self.is_valid = False
        self.issues.append(ValidationIssue(field=field_name, message=message))


def validate_dataset(df: pd.DataFrame) -> ValidationReport:
    """Validate a raw results.csv-shaped dataframe.

    Checks performed (Development Prompt Section 14):
    - required columns present
    - column names match exactly
    - home_score / away_score are numeric or missing (future fixtures)
    - date column parses without ambiguity
    - no exact duplicate rows
    - neutral column only contains boolean-like values
    - at least one row remains after validation
    """

    report = ValidationReport(is_valid=True, row_count=len(df))

    missing_columns = [
        column for column in REQUIRED_RAW_COLUMNS if column not in df.columns
    ]
    for column in missing_columns:
        report.add_error("columns", f"Missing required column: {column}")

    if missing_columns:
        # Remaining checks assume the columns exist; stop here.
        return report

    if len(df) == 0:
        report.add_error("rows", "Dataset contains zero rows.")
        return report

    # --- date validity -------------------------------------------------
    parsed_dates, unrecognised_format_mask = parse_dates_safely(df["date"])

    unparseable_count = int(parsed_dates.isna().sum())
    if unparseable_count:
        report.add_error(
            "date",
            f"{unparseable_count} row(s) have a date that could not be parsed.",
        )

    ambiguous_count = int(unrecognised_format_mask.sum())
    if ambiguous_count:
        report.add_error(
            "date",
            f"{ambiguous_count} row(s) use an unrecognised or ambiguous date "
            "format. Expected YYYY-MM-DD or YYYY/M/D.",
        )

    # --- score validity --------------------------------------------------
    for score_column in ("home_score", "away_score"):
        numeric_scores = pd.to_numeric(df[score_column], errors="coerce")
        invalid_mask = numeric_scores.isna() & df[score_column].notna()
        invalid_count = int(invalid_mask.sum())
        if invalid_count:
            report.add_error(
                score_column,
                f"{invalid_count} row(s) have a non-numeric {score_column}.",
            )

        negative_mask = numeric_scores < 0
        negative_count = int(negative_mask.sum())
        if negative_count:
            report.add_error(
                score_column,
                f"{negative_count} row(s) have a negative {score_column}.",
            )

    # --- team name validity ---------------------------------------------
    for team_column in ("home_team", "away_team"):
        blank_count = int(
            df[team_column].isna().sum()
            + (df[team_column].astype(str).str.strip() == "").sum()
        )
        if blank_count:
            report.add_error(
                team_column, f"{blank_count} row(s) have a blank {team_column}."
            )

    same_team_count = int((df["home_team"] == df["away_team"]).sum())
    if same_team_count:
        report.add_error(
            "home_team/away_team",
            f"{same_team_count} row(s) have identical home_team and away_team.",
        )

    # --- neutral column validity ------------------------------------------
    valid_neutral_values = {True, False, "TRUE", "FALSE", "True", "False", 0, 1}
    invalid_neutral_mask = ~df["neutral"].isin(valid_neutral_values)
    invalid_neutral_count = int(invalid_neutral_mask.sum())
    if invalid_neutral_count:
        report.add_error(
            "neutral",
            f"{invalid_neutral_count} row(s) have a non-boolean neutral value.",
        )

    # --- duplicate rows ----------------------------------------------------
    duplicate_count = int(df.duplicated().sum())
    if duplicate_count:
        report.add_error(
            "duplicates", f"{duplicate_count} exact duplicate row(s) found."
        )

    return report
