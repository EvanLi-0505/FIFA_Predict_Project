"""Upset ("black swan") risk: the probability that the underdog wins outright.

The underdog is whichever side the model gives the lower win probability
(Home Win vs Home Loss); draws are excluded. With the Elo model this
probability is well calibrated — on the 2016+ held-out matches, predicted
20-30% buckets upset 24.4% of the time and 30-40% buckets 33.5%.

A historical upset is a completed match the underdog won although the model
gave it less than HISTORICAL_UPSET_MAX_PROBABILITY beforehand.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from core.config import CLASS_LABELS
from core.models.training import predict_with_model

UPSET_MEDIUM_THRESHOLD = 0.15
UPSET_HIGH_THRESHOLD = 0.30
HISTORICAL_UPSET_MAX_PROBABILITY = 0.20

UPSET_HISTORY_CACHE_FILENAME = "upset_history_cache.json"


@dataclass
class UpsetRisk:
    favorite_outcome: str
    underdog_outcome: str
    probability: float
    level: str


def upset_risk_level(probability: float) -> str:
    if probability > UPSET_HIGH_THRESHOLD:
        return "high"
    if probability >= UPSET_MEDIUM_THRESHOLD:
        return "medium"
    return "low"


def assess_upset_risk(probabilities: dict[str, float]) -> UpsetRisk:
    # A model trained on a dataset that never contains an outcome has no
    # probability entry for it at all.
    home_win = probabilities.get("Home Win", 0.0)
    home_loss = probabilities.get("Home Loss", 0.0)
    if home_win >= home_loss:
        favorite, underdog, probability = "Home Win", "Home Loss", home_loss
    else:
        favorite, underdog, probability = "Home Loss", "Home Win", home_win
    return UpsetRisk(favorite, underdog, float(probability), upset_risk_level(probability))


def build_upset_history(model_data: pd.DataFrame, probabilities: pd.DataFrame) -> dict:
    """Find every historical upset and count, per team, matches played and
    upsets caused (won as underdog) / suffered (lost as favorite).

    `probabilities` must be row-aligned with `model_data` and have the
    model's class labels as columns (the model's pre-match view of each
    match).
    """

    home_win = probabilities["Home Win"].to_numpy()
    home_loss = probabilities["Home Loss"].to_numpy()

    teams: dict[str, dict[str, int]] = {}
    upsets: list[dict] = []

    def team_entry(name: str) -> dict[str, int]:
        return teams.setdefault(name, {"matches": 0, "upsets_caused": 0, "upsets_suffered": 0})

    columns = ["date", "home_team", "away_team", "home_score", "away_score", "tournament", "result"]
    for position, row in enumerate(model_data[columns].itertuples(index=False)):
        team_entry(row.home_team)["matches"] += 1
        team_entry(row.away_team)["matches"] += 1

        home_is_underdog = home_win[position] < home_loss[position]
        underdog_probability = home_win[position] if home_is_underdog else home_loss[position]
        underdog_won = row.result == ("Home Win" if home_is_underdog else "Home Loss")
        if not underdog_won or underdog_probability >= HISTORICAL_UPSET_MAX_PROBABILITY:
            continue

        winner, loser = (
            (row.home_team, row.away_team) if home_is_underdog else (row.away_team, row.home_team)
        )
        team_entry(winner)["upsets_caused"] += 1
        team_entry(loser)["upsets_suffered"] += 1
        upsets.append(
            {
                "date": pd.Timestamp(row.date).date().isoformat(),
                "home_team": row.home_team,
                "away_team": row.away_team,
                "home_score": int(row.home_score),
                "away_score": int(row.away_score),
                "tournament": row.tournament,
                "winner": winner,
                "loser": loser,
                "upset_probability": float(underdog_probability),
            }
        )

    upsets.sort(key=lambda upset: upset["date"], reverse=True)
    return {
        "max_probability": HISTORICAL_UPSET_MAX_PROBABILITY,
        "teams": teams,
        "upsets": upsets,
    }


def compute_upset_history(model, scaler, model_data: pd.DataFrame, feature_columns: list[str]) -> dict:
    """`build_upset_history` using a trained model's own probabilities for
    every completed match in the dataset it was trained on."""

    _, probabilities = predict_with_model(model, scaler, model_data[feature_columns])
    frame = pd.DataFrame(probabilities, columns=model.classes_, index=model_data.index)
    return build_upset_history(model_data, frame.reindex(columns=CLASS_LABELS, fill_value=0.0))


def team_upset_history(history: dict, team: str, limit: int) -> dict:
    summary = history["teams"].get(team, {"matches": 0, "upsets_caused": 0, "upsets_suffered": 0})
    matches = [
        {**upset, "role": "caused" if upset["winner"] == team else "suffered"}
        for upset in history["upsets"]
        if team in (upset["home_team"], upset["away_team"])
    ]
    return {
        "team": team,
        "max_probability": history["max_probability"],
        "summary": summary,
        "matches": matches[:limit],
    }


def save_upset_history_cache(cache_path: str | Path, history: dict) -> None:
    cache_path = Path(cache_path)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(history), encoding="utf-8")


def load_upset_history_cache(cache_path: str | Path) -> dict | None:
    cache_path = Path(cache_path)
    if not cache_path.exists():
        return None
    try:
        return json.loads(cache_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
