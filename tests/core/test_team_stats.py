"""Unit tests for core.analytics.team_stats — pure math, no dataset I/O."""

from __future__ import annotations

import pandas as pd
import pytest

from core.analytics.team_stats import (
    compare_teams,
    compute_rating,
    compute_team_stats,
    get_team_matches,
    list_all_team_names,
)


@pytest.fixture
def completed_matches() -> pd.DataFrame:
    # Team "Alpha": 2 wins, 1 draw, 1 loss over 4 matches.
    # Team "Beta": loses to Alpha twice, draws once, beats Gamma once.
    rows = [
        {"date": "2020-01-01", "home_team": "Alpha", "away_team": "Beta",
         "home_score": 2, "away_score": 0, "tournament": "Friendly",
         "neutral": False, "result": "Home Win"},
        {"date": "2020-02-01", "home_team": "Beta", "away_team": "Alpha",
         "home_score": 1, "away_score": 1, "tournament": "Friendly",
         "neutral": False, "result": "Draw"},
        {"date": "2020-03-01", "home_team": "Alpha", "away_team": "Beta",
         "home_score": 0, "away_score": 3, "tournament": "Friendly",
         "neutral": False, "result": "Home Loss"},
        {"date": "2020-04-01", "home_team": "Alpha", "away_team": "Gamma",
         "home_score": 4, "away_score": 1, "tournament": "Friendly",
         "neutral": True, "result": "Home Win"},
        {"date": "2020-05-01", "home_team": "Beta", "away_team": "Gamma",
         "home_score": 2, "away_score": 1, "tournament": "Friendly",
         "neutral": False, "result": "Home Win"},
    ]
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    return df


def test_list_all_team_names(completed_matches):
    assert list_all_team_names(completed_matches) == ["Alpha", "Beta", "Gamma"]


def test_get_team_matches_most_recent_first(completed_matches):
    matches = get_team_matches(completed_matches, "Alpha")
    dates = [m.date for m in matches]
    assert dates == sorted(dates, reverse=True)
    assert len(matches) == 4


def test_get_team_matches_outcome_from_teams_perspective(completed_matches):
    matches = get_team_matches(completed_matches, "Alpha")
    by_date = {m.date: m for m in matches}

    # Alpha 2-0 Beta at home -> Win for Alpha
    assert by_date["2020-01-01"].outcome == "Win"
    assert by_date["2020-01-01"].is_home is True
    assert by_date["2020-01-01"].team_score == 2
    assert by_date["2020-01-01"].opponent == "Beta"

    # Beta 1-1 Alpha, Alpha is away -> Draw for Alpha
    assert by_date["2020-02-01"].outcome == "Draw"
    assert by_date["2020-02-01"].is_home is False

    # Alpha 0-3 Beta at home -> Loss for Alpha
    assert by_date["2020-03-01"].outcome == "Loss"


def test_compute_team_stats_alpha(completed_matches):
    stats = compute_team_stats(completed_matches, "Alpha")

    assert stats.matches_played == 4
    assert stats.wins == 2
    assert stats.draws == 1
    assert stats.losses == 1
    assert stats.goals_for == 2 + 1 + 0 + 4  # 7
    assert stats.goals_against == 0 + 1 + 3 + 1  # 5
    assert stats.points_per_game == pytest.approx((3 * 2 + 1) / 4)
    assert stats.small_sample is True  # fewer than 5 matches
    assert 0 <= stats.rating <= 100


def test_compute_team_stats_unknown_team_returns_none(completed_matches):
    assert compute_team_stats(completed_matches, "Nonexistent FC") is None


def test_compute_rating_monotonic_in_points_per_game():
    low = compute_rating(points_per_game=0.5, recent_points_per_game=0.5, goal_diff_avg=0.0)
    high = compute_rating(points_per_game=2.5, recent_points_per_game=2.5, goal_diff_avg=0.0)
    assert high > low


def test_compute_rating_bounded_0_to_100():
    assert compute_rating(3.0, 3.0, 10.0) <= 100.0
    assert compute_rating(0.0, 0.0, -10.0) >= 0.0


def test_compare_teams_sorted_by_rating_desc(completed_matches):
    results = compare_teams(completed_matches, ["Alpha", "Beta", "Gamma"])
    ratings = [r.rating for r in results]
    assert ratings == sorted(ratings, reverse=True)
    assert {r.team_name for r in results} == {"Alpha", "Beta", "Gamma"}


def test_compare_teams_skips_unknown_names(completed_matches):
    results = compare_teams(completed_matches, ["Alpha", "Nonexistent FC"])
    assert [r.team_name for r in results] == ["Alpha"]
