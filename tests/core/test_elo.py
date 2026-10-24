from __future__ import annotations

import pandas as pd
import pytest

from core.config import ELO_FEATURE_VERSION, ORIGINAL_FEATURE_VERSION
from core.feature_engineering.elo import (
    ELO_FEATURES,
    ELO_INITIAL_RATING,
    add_elo_ratings,
    tournament_k_factor,
)
from core.schemas.feature_schema import build_feature_columns


def _matches(rows):
    return pd.DataFrame(
        rows, columns=["date", "home_team", "away_team", "home_score", "away_score", "tournament", "neutral"]
    ).assign(date=lambda d: pd.to_datetime(d["date"]))


@pytest.mark.parametrize(
    "tournament, k",
    [
        ("FIFA World Cup", 60),
        ("FIFA World Cup qualification", 40),
        ("UEFA Euro", 50),
        ("Copa Am\x8a\x9drica", 50),
        ("UEFA Nations League", 40),
        ("Friendly", 20),
        ("Merdeka Tournament", 30),
    ],
)
def test_tournament_k_factor(tournament, k):
    assert tournament_k_factor(tournament) == k


def test_home_win_updates_ratings_by_hand_computed_amount():
    data, ratings = add_elo_ratings(_matches([("2020-01-01", "A", "B", 1, 0, "Friendly", False)]))

    assert data.loc[0, "elo_home"] == ELO_INITIAL_RATING
    assert data.loc[0, "elo_away"] == ELO_INITIAL_RATING
    expected_home = 1 / (1 + 10 ** (-100 / 400))  # +100 home advantage
    delta = 20 * 1.0 * (1 - expected_home)
    assert ratings["A"] == pytest.approx(ELO_INITIAL_RATING + delta)
    assert ratings["B"] == pytest.approx(ELO_INITIAL_RATING - delta)


def test_same_day_matches_read_pre_day_ratings_and_fixtures_never_update():
    data, ratings = add_elo_ratings(
        _matches(
            [
                ("2020-01-01", "A", "B", 3, 0, "FIFA World Cup", True),
                ("2020-01-01", "C", "A", 0, 0, "Friendly", True),  # same day: A still at 1500
                ("2020-02-01", "A", "D", None, None, "Friendly", True),  # unscored fixture
            ]
        )
    )

    assert data.loc[1, "elo_away"] == ELO_INITIAL_RATING
    assert data.loc[2, "elo_home"] == ratings["A"]  # fixture sees post-January rating
    assert ratings["D"] == ELO_INITIAL_RATING  # fixture did not move D
    assert sum(ratings.values()) == pytest.approx(4 * ELO_INITIAL_RATING)  # zero-sum


def test_feature_v1_columns_unchanged_and_v2_adds_elo():
    dummies = ["tournament_Friendly", "tournament_World Cup"]
    v1 = build_feature_columns(dummies, ORIGINAL_FEATURE_VERSION)
    v2 = build_feature_columns(dummies, ELO_FEATURE_VERSION)

    assert not set(ELO_FEATURES) & set(v1)
    assert [c for c in v2 if c not in ELO_FEATURES] == v1
    assert v2.index("elo_home") < v2.index("neutral")
