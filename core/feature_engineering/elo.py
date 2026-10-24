"""Pre-match Elo team ratings (feature_v2 only — not part of the notebook).

World Football Elo rules (eloratings.net) with their published constants,
deliberately not tuned on this dataset:

    new = old + K * G * (W - We)
    We  = 1 / (1 + 10 ** (-(dr) / 400)),  dr = home - away (+100 if not neutral)
    K   = 60 World Cup finals, 50 continental finals / Confederations Cup,
          40 qualifiers and Nations Leagues, 20 friendlies, 30 anything else
    G   = 1 for a 0-1 goal margin, 1.5 for 2, (11 + N) / 8 for N >= 3

Leakage rules match `team_history.generate_historical_features`: every
match on a date reads its ratings BEFORE any result from that date is
applied, and unscored fixtures never update a rating.
"""

from __future__ import annotations

from collections import defaultdict

import numpy as np
import pandas as pd

ELO_INITIAL_RATING = 1500.0
ELO_HOME_ADVANTAGE = 100.0

ELO_FEATURES = ["elo_home", "elo_away", "elo_diff"]

_CONTINENTAL_FINALS = {
    "uefa euro",
    "african cup of nations",
    "afc asian cup",
    "gold cup",
    "concacaf championship",
    "oceania nations cup",
    "confederations cup",
}
_NATIONS_LEAGUES = {"uefa nations league", "concacaf nations league"}


def tournament_k_factor(tournament: str) -> float:
    name = str(tournament).strip().lower()
    if name == "fifa world cup":
        return 60.0
    # "copa am": the built-in dataset spells Copa América with a mangled "é".
    if name in _CONTINENTAL_FINALS or name.startswith("copa am"):
        return 50.0
    if "qualification" in name or name in _NATIONS_LEAGUES:
        return 40.0
    if name == "friendly":
        return 20.0
    return 30.0


def _goal_margin_multiplier(goal_difference: float) -> float:
    margin = abs(goal_difference)
    if margin <= 1:
        return 1.0
    if margin == 2:
        return 1.5
    return (11.0 + margin) / 8.0


def add_elo_ratings(featured_data: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, float]]:
    """Attach pre-match `elo_home` / `elo_away` columns.

    `featured_data` must be in ascending date order (as returned by
    `generate_historical_features`). Returns the augmented copy plus every
    team's rating after the last completed match — the value to use when
    predicting a future match.
    """

    ratings: defaultdict[str, float] = defaultdict(lambda: ELO_INITIAL_RATING)
    n = len(featured_data)
    elo_home = np.empty(n)
    elo_away = np.empty(n)

    pending: list[tuple] = []
    current_date = None

    def apply_pending() -> None:
        deltas: defaultdict[str, float] = defaultdict(float)
        for row, home_rating, away_rating in pending:
            advantage = 0.0 if row.neutral else ELO_HOME_ADVANTAGE
            expected_home = 1.0 / (1.0 + 10 ** (-(home_rating + advantage - away_rating) / 400.0))
            goal_difference = row.home_score - row.away_score
            actual_home = 1.0 if goal_difference > 0 else 0.5 if goal_difference == 0 else 0.0
            delta = (
                tournament_k_factor(row.tournament)
                * _goal_margin_multiplier(goal_difference)
                * (actual_home - expected_home)
            )
            deltas[row.home_team] += delta
            deltas[row.away_team] -= delta
        for team, delta in deltas.items():
            ratings[team] += delta
        pending.clear()

    columns = ["date", "home_team", "away_team", "home_score", "away_score", "tournament", "neutral"]
    for position, row in enumerate(featured_data[columns].itertuples(index=False)):
        if row.date != current_date:
            apply_pending()
            current_date = row.date
        home_rating = ratings[row.home_team]
        away_rating = ratings[row.away_team]
        elo_home[position] = home_rating
        elo_away[position] = away_rating
        if pd.notna(row.home_score) and pd.notna(row.away_score):
            pending.append((row, home_rating, away_rating))
    apply_pending()

    result = featured_data.copy()
    result["elo_home"] = elo_home
    result["elo_away"] = elo_away
    return result, dict(ratings)


def add_elo_difference(data: pd.DataFrame) -> pd.DataFrame:
    """Pure rating gap; home advantage is left to the separate `neutral`
    feature so the model can learn its own weight for it."""

    data = data.copy()
    data["elo_diff"] = data["elo_home"] - data["elo_away"]
    return data
