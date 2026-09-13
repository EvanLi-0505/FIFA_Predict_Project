"""Team-centric browsing and comparison analytics.

Added after Stage 4 manual testing feedback (Team Explorer page): a team's
full match history timeline, lifetime aggregate stats, and a composite
"power rating" for comparing up to a handful of teams side by side.

This is intentionally separate from `core.feature_engineering` — those
modules compute *pre-match, leakage-free, rolling-window* features for
model training/prediction. This module computes *all-time, read-only*
descriptive statistics for human browsing, so it operates directly on
`core.pipeline.build_completed_matches()` output rather than the expensive
`generate_historical_features` pass.

RATING METHODOLOGY (transparent by design — this is NOT an official FIFA
ranking, it is a simple illustrative composite for comparing teams within
this app):

    points_per_game       = (3*wins + draws) / matches_played        (0-3)
    recent_points_per_game = same formula over at most the last 10
                             chronological matches                    (0-3)
    goal_diff_component    = 0.5 + 0.5*tanh(avg_goal_diff / 1.5)      (0-1)
                             (a smooth squashing curve centred on 0 so
                             extreme goal differences don't dominate)

    rating = 100 * clamp01(
        0.50 * (points_per_game / 3) +
        0.30 * (recent_points_per_game / 3) +
        0.20 * goal_diff_component
    )

Recent form is weighted second-highest (30%) because it is the more
predictive signal of current strength; lifetime record carries the most
weight (50%) as the most stable estimate; goal difference contributes the
remainder as a tie-breaker/margin-of-victory signal.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import pandas as pd

RECENT_FORM_WINDOW = 10


@dataclass
class TeamMatchRecord:
    date: str
    opponent: str
    is_home: bool
    tournament: str
    neutral: bool
    team_score: int
    opponent_score: int
    outcome: str  # "Win" | "Draw" | "Loss"


@dataclass
class TeamStats:
    team_name: str
    matches_played: int
    wins: int
    draws: int
    losses: int
    win_rate: float
    draw_rate: float
    loss_rate: float
    goals_for: int
    goals_against: int
    goals_for_avg: float
    goals_against_avg: float
    goal_diff_avg: float
    points_per_game: float
    recent_form: list[str] = field(default_factory=list)
    """Most recent results first, e.g. ['Win', 'Win', 'Draw', 'Loss']."""
    recent_points_per_game: float = 0.0
    rating: float = 0.0
    small_sample: bool = False
    """True when matches_played < 5 — stats/rating are still computed but
    should be flagged as low-confidence in the UI."""


def list_all_team_names(completed_matches: pd.DataFrame) -> list[str]:
    teams = set(completed_matches["home_team"]) | set(completed_matches["away_team"])
    return sorted(teams)


def _team_rows(completed_matches: pd.DataFrame, team_name: str) -> pd.DataFrame:
    mask = (completed_matches["home_team"] == team_name) | (
        completed_matches["away_team"] == team_name
    )
    return completed_matches.loc[mask].sort_values("date")


def get_team_matches(
    completed_matches: pd.DataFrame, team_name: str, limit: int | None = None
) -> list[TeamMatchRecord]:
    """Full match history for one team, most recent first."""

    rows = _team_rows(completed_matches, team_name).sort_values("date", ascending=False)
    if limit is not None:
        rows = rows.head(limit)

    records: list[TeamMatchRecord] = []
    for _, row in rows.iterrows():
        is_home = row["home_team"] == team_name
        team_score = row["home_score"] if is_home else row["away_score"]
        opponent_score = row["away_score"] if is_home else row["home_score"]
        opponent = row["away_team"] if is_home else row["home_team"]

        if team_score > opponent_score:
            outcome = "Win"
        elif team_score == opponent_score:
            outcome = "Draw"
        else:
            outcome = "Loss"

        records.append(
            TeamMatchRecord(
                date=row["date"].date().isoformat(),
                opponent=opponent,
                is_home=bool(is_home),
                tournament=row["tournament"],
                neutral=bool(row["neutral"]),
                team_score=int(team_score),
                opponent_score=int(opponent_score),
                outcome=outcome,
            )
        )

    return records


def _goal_diff_component(avg_goal_diff: float) -> float:
    return 0.5 + 0.5 * math.tanh(avg_goal_diff / 1.5)


def compute_rating(points_per_game: float, recent_points_per_game: float, goal_diff_avg: float) -> float:
    raw = (
        0.50 * (points_per_game / 3)
        + 0.30 * (recent_points_per_game / 3)
        + 0.20 * _goal_diff_component(goal_diff_avg)
    )
    return round(100 * max(0.0, min(1.0, raw)), 1)


def compute_team_stats(completed_matches: pd.DataFrame, team_name: str) -> TeamStats | None:
    matches = get_team_matches(completed_matches, team_name)
    matches_played = len(matches)

    if matches_played == 0:
        return None

    wins = sum(1 for m in matches if m.outcome == "Win")
    draws = sum(1 for m in matches if m.outcome == "Draw")
    losses = sum(1 for m in matches if m.outcome == "Loss")

    goals_for = sum(m.team_score for m in matches)
    goals_against = sum(m.opponent_score for m in matches)

    goals_for_avg = goals_for / matches_played
    goals_against_avg = goals_against / matches_played
    goal_diff_avg = goals_for_avg - goals_against_avg

    points_per_game = (3 * wins + draws) / matches_played

    recent = matches[:RECENT_FORM_WINDOW]  # matches is already most-recent-first
    recent_wins = sum(1 for m in recent if m.outcome == "Win")
    recent_draws = sum(1 for m in recent if m.outcome == "Draw")
    recent_points_per_game = (
        (3 * recent_wins + recent_draws) / len(recent) if recent else 0.0
    )

    rating = compute_rating(points_per_game, recent_points_per_game, goal_diff_avg)

    return TeamStats(
        team_name=team_name,
        matches_played=matches_played,
        wins=wins,
        draws=draws,
        losses=losses,
        win_rate=wins / matches_played,
        draw_rate=draws / matches_played,
        loss_rate=losses / matches_played,
        goals_for=goals_for,
        goals_against=goals_against,
        goals_for_avg=goals_for_avg,
        goals_against_avg=goals_against_avg,
        goal_diff_avg=goal_diff_avg,
        points_per_game=points_per_game,
        recent_form=[m.outcome for m in recent],
        recent_points_per_game=recent_points_per_game,
        rating=rating,
        small_sample=matches_played < 5,
    )


def compare_teams(completed_matches: pd.DataFrame, team_names: list[str]) -> list[TeamStats]:
    """Compute stats+rating for each team, sorted by rating descending.

    Teams with no matches in the dataset are silently skipped rather than
    raising, so a comparison of 5 teams still returns useful results if one
    name is misspelled or genuinely absent.
    """

    results = []
    for team_name in team_names:
        stats = compute_team_stats(completed_matches, team_name)
        if stats is not None:
            results.append(stats)

    return sorted(results, key=lambda s: s.rating, reverse=True)
