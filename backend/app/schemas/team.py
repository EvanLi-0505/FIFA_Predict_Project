from __future__ import annotations

from pydantic import BaseModel, Field


class TeamMatchResponse(BaseModel):
    date: str
    opponent: str
    is_home: bool
    tournament: str
    neutral: bool
    team_score: int
    opponent_score: int
    outcome: str


class TeamStatsResponse(BaseModel):
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
    recent_form: list[str]
    recent_points_per_game: float
    rating: float
    small_sample: bool


class TeamCompareRequest(BaseModel):
    team_names: list[str] = Field(..., min_length=1, max_length=5)
