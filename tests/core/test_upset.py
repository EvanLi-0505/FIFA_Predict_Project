from __future__ import annotations

import pandas as pd
import pytest

from core.analytics.upset import (
    assess_upset_risk,
    build_upset_history,
    team_upset_history,
    upset_risk_level,
)


@pytest.mark.parametrize(
    "probability, level",
    [(0.0, "low"), (0.149, "low"), (0.15, "medium"), (0.30, "medium"), (0.301, "high"), (0.45, "high")],
)
def test_risk_tiers(probability, level):
    assert upset_risk_level(probability) == level


def test_underdog_is_the_side_with_lower_win_probability_and_draws_are_ignored():
    away_favored = assess_upset_risk({"Home Win": 0.32, "Draw": 0.30, "Home Loss": 0.38})
    assert away_favored.favorite_outcome == "Home Loss"
    assert away_favored.underdog_outcome == "Home Win"
    assert away_favored.probability == pytest.approx(0.32)
    assert away_favored.level == "high"

    home_favored = assess_upset_risk({"Home Win": 0.7, "Draw": 0.2, "Home Loss": 0.1})
    assert home_favored.favorite_outcome == "Home Win"
    assert home_favored.probability == pytest.approx(0.1)
    assert home_favored.level == "low"


def test_missing_outcome_class_counts_as_zero():
    # e.g. a model trained on a tiny upload that never had a home loss
    risk = assess_upset_risk({"Home Win": 0.6, "Draw": 0.4})
    assert risk.favorite_outcome == "Home Win"
    assert risk.probability == 0.0


def test_historical_upsets_need_an_underdog_win_below_twenty_percent():
    model_data = pd.DataFrame(
        {
            "date": pd.to_datetime(["2020-01-01", "2021-01-01", "2022-01-01", "2023-01-01"]),
            "home_team": ["A", "A", "A", "B"],
            "away_team": ["B", "B", "B", "A"],
            "home_score": [0, 0, 1, 2],
            "away_score": [1, 1, 1, 0],
            "tournament": ["Friendly"] * 4,
            "result": ["Home Loss", "Home Loss", "Draw", "Home Win"],
        }
    )
    probabilities = pd.DataFrame(
        {
            # 1: away underdog (10%) wins -> upset. 2: away underdog at 25% wins -> too likely.
            # 3: draw -> never an upset. 4: home underdog (5%) wins -> upset.
            "Home Win": [0.70, 0.55, 0.80, 0.05],
            "Draw": [0.20, 0.20, 0.15, 0.20],
            "Home Loss": [0.10, 0.25, 0.05, 0.75],
        }
    )

    history = build_upset_history(model_data, probabilities)

    assert [u["date"] for u in history["upsets"]] == ["2023-01-01", "2020-01-01"]  # newest first
    assert history["teams"]["B"] == {"matches": 4, "upsets_caused": 2, "upsets_suffered": 0}
    assert history["teams"]["A"] == {"matches": 4, "upsets_caused": 0, "upsets_suffered": 2}

    team_a = team_upset_history(history, "A", limit=1)
    assert len(team_a["matches"]) == 1
    assert team_a["matches"][0]["role"] == "suffered"
    assert team_a["matches"][0]["upset_probability"] == pytest.approx(0.05)

    unknown = team_upset_history(history, "Nowhere", limit=5)
    assert unknown["summary"]["matches"] == 0 and unknown["matches"] == []
