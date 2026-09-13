"""Dataset loading and date-format standardisation.

The source notebook loaded `results.csv` directly with
`pd.read_csv("results.csv")` inside Google Colab (Phase 1.2), then converted
the `date` column with `pd.to_datetime(df["date"], errors="coerce")`
(Phase 3.1). This module reproduces that loading behaviour but removes the
Colab-specific `google.colab.files.upload()` call and fixes a real parsing
defect uncovered while validating Stage 1 (Conflict B from the Stage 0
audit, resolved per the user's explicit approval to handle it at our
discretion):

The built-in dataset mixes ISO (`YYYY-MM-DD`) and slash (`YYYY/M/D`) date
strings — the first 127 rows (1872-1899) are ISO, the remaining ~49,393 rows
are slash-formatted. Both forms are individually unambiguous (year always
comes first), but `pd.to_datetime(series, errors="coerce")` with no
explicit `format` infers a SINGLE format from the first non-null value and
applies it to the whole column for performance. Since the first row is ISO,
every slash-formatted row then fails to parse and silently becomes `NaT` —
confirmed empirically: this turns 49,393 of 49,520 rows' dates into missing
values, which cascades into massive, silent data loss during deduplication
and historical feature engineering. Using `format="mixed"` parses each
value independently and fixes this without changing a single non-date
value or any modelling number.

`load_raw_dataset` does NOT convert the date column — that stays in
`core.preprocessing.cleaning.convert_date_column` to keep this module a
thin I/O layer. It routes through `parse_dates_safely` below.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from core.config import REQUIRED_RAW_COLUMNS

# Any row whose date does not match one of these patterns is flagged rather
# than silently passed to dateutil's ambiguous free-form parser.
_ACCEPTED_DATE_REGEX = r"^\d{4}-\d{1,2}-\d{1,2}$|^\d{4}/\d{1,2}/\d{1,2}$"

# Encodings tried in order. UTF-8 is the expected encoding; the built-in
# dataset (`datasets/builtin/results.csv`) has a number of `city`/`country`
# values (mostly early-1900s European/South American match venues, e.g.
# "Krak?w", "Asunci?n") that were already corrupted to a literal "?" at some
# earlier stage of the source data's history, before it ever reached this
# project — that is lossy by construction (a literal "?" byte cannot be
# decoded back to the original character) and is NOT fixed here. Those
# columns are not used by any model feature or displayed anywhere in the
# app, so this has no functional impact. A tolerant fallback is still
# required so the file loads at all instead of hard-crashing on those
# pre-existing bad bytes. latin-1 is listed last because it can decode any
# byte sequence and must never mask a genuine problem with an otherwise
# clean UTF-8 file.
_ENCODING_FALLBACK_CHAIN = ["utf-8", "cp1252", "latin-1"]

# A handful of `home_team`/`away_team`/`tournament` values ARE recoverable:
# they decode via cp1252 (the fallback this file actually uses, since other
# bytes elsewhere in the file are not valid UTF-8) into a consistent,
# identifiable mojibake pattern rather than a lossy "?". Specifically, the
# two-byte sequence 0x8A 0x9D decodes via cp1252 to "\x8a\x9d", and in every
# one of the five places it appears below it sits exactly where a well-known
# place name has an "é" — a well-documented, extremely low-risk correction
# (Curaçao, São Tomé and Príncipe are current FIFA members; Réunion, Saint
# Barthélemy, Székely Land are common unofficial-team entries in this
# dataset family). The tournament name is restored to the plain-ASCII form
# used elsewhere in football databases ("Evence Coppee Trophy", no accents)
# rather than a guessed accented form. One further mangled team name
# ("Ry\x93zky\x93z") was found during the same audit but could NOT be
# confidently identified — inventing a spelling would be worse than leaving
# it recognisably broken, so it is deliberately left uncorrected.
_KNOWN_MOJIBAKE_CORRECTIONS = {
    "CuraäÍao": "Curaçao",
    "D\x8a\x9dlvid\x8a\x9dk": "Délvidék",
    "Felvid\x8a\x9dk": "Felvidék",
    "R\x8a\x9dunion": "Réunion",
    "Saint Barth\x8a\x9dlemy": "Saint Barthélemy",
    "Sz\x8a\x9dkely Land": "Székely Land",
    "S\xe4\xa9o Tom\x8a\x9d and Pr?ncipe": "São Tomé and Príncipe",
    "?vence Copp\x8a\x9de Trophy": "Evence Coppee Trophy",
}

_MOJIBAKE_COLUMNS = ("home_team", "away_team", "tournament")


def load_raw_dataset(csv_path: str | Path) -> pd.DataFrame:
    """Load a results.csv file exactly as the notebook's df_raw.

    Parameters
    ----------
    csv_path : str or Path
        Path to a CSV file following the `REQUIRED_RAW_COLUMNS` schema.

    Returns
    -------
    pd.DataFrame
        The raw dataframe, unmodified column-wise, matching
        `pd.read_csv("results.csv")` from Phase 1.2 of the source notebook.
        The `date` column is left as raw strings; call
        `core.preprocessing.cleaning.convert_date_column` next.
    """

    csv_path = Path(csv_path)

    if not csv_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {csv_path}")

    df_raw = _read_csv_with_encoding_fallback(csv_path)
    df_raw = _fix_known_mojibake(df_raw)

    missing_columns = [
        column
        for column in REQUIRED_RAW_COLUMNS
        if column not in df_raw.columns
    ]

    if missing_columns:
        raise ValueError(
            "Dataset is missing required column(s): "
            + ", ".join(missing_columns)
        )

    return df_raw


def _read_csv_with_encoding_fallback(csv_path: Path) -> pd.DataFrame:
    """Read a CSV trying each encoding in `_ENCODING_FALLBACK_CHAIN`.

    Only affects text decoding of the raw bytes — it never alters cell
    values, column order, or row order. Falls back only on a genuine decode
    failure, so a clean UTF-8 file is always read as plain UTF-8.
    """

    last_error: UnicodeDecodeError | None = None

    for encoding in _ENCODING_FALLBACK_CHAIN:
        try:
            return pd.read_csv(csv_path, encoding=encoding)
        except UnicodeDecodeError as error:
            last_error = error
            continue

    raise last_error  # pragma: no cover - latin-1 never raises in practice


def _fix_known_mojibake(df: pd.DataFrame) -> pd.DataFrame:
    """Repair the specific, identifiable mojibake listed in
    `_KNOWN_MOJIBAKE_CORRECTIONS` (see that dict's comment for why these —
    and only these — are safe to correct). A no-op on any dataset that
    doesn't contain these exact strings, so it is harmless to run
    unconditionally on every upload, not just the built-in dataset.
    """

    df = df.copy()
    for column in _MOJIBAKE_COLUMNS:
        if column in df.columns:
            df[column] = df[column].replace(_KNOWN_MOJIBAKE_CORRECTIONS)
    return df


def parse_date_column(date_series: pd.Series) -> pd.Series:
    """Parse a `date` column, robust to mixed ISO/slash formats.

    Uses `format="mixed"` so each value is parsed independently instead of
    a single inferred format being applied to the whole column (see module
    docstring for why the naive `pd.to_datetime(series, errors="coerce")`
    call silently destroys ~99.7% of dates on the built-in dataset).
    Genuinely invalid date strings still become `NaT`, exactly as
    `errors="coerce"` intends.
    """

    return pd.to_datetime(date_series, format="mixed", errors="coerce")


def parse_dates_safely(date_series: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Parse a date column and flag rows in an unrecognised format.

    Returns
    -------
    (parsed_dates, unrecognised_format_mask)
        `parsed_dates` comes from `parse_date_column` (mixed-format safe).
        `unrecognised_format_mask` flags rows whose raw string does not match
        either known-unambiguous format (`YYYY-M-D` / `YYYY/M/D`), so a
        future dataset upload with a genuinely ambiguous format like
        `MM/DD/YYYY` is surfaced during validation instead of being
        silently misinterpreted.
    """

    raw_strings = date_series.astype(str)

    unrecognised_format_mask = ~raw_strings.str.match(_ACCEPTED_DATE_REGEX)

    parsed_dates = parse_date_column(date_series)

    return parsed_dates, unrecognised_format_mask
