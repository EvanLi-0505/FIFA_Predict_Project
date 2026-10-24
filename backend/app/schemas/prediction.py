from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, computed_field

from core.analytics.upset import assess_upset_risk


class PredictionRequest(BaseModel):
    home_team: str = Field(..., min_length=1, max_length=128)
    away_team: str = Field(..., min_length=1, max_length=128)
    host_country: str = Field(..., min_length=1, max_length=128)
    tournament: str = Field(..., min_length=1, max_length=128)
    """Raw tournament name/label from the UI. Mapped internally to one of
    Friendly / Other Competitive / World Cup / World Cup Qualification via
    core.feature_engineering.tournament.categorize_tournament — any value
    not recognised falls into 'Other Competitive', matching notebook
    behaviour exactly."""


class _WithUpsetRisk(BaseModel):
    """Upset risk derived from `probabilities` (core.analytics.upset) — also
    works for history records saved before upset risk existed."""

    probabilities: dict[str, float]

    @computed_field
    @property
    def upset_probability(self) -> float:
        return assess_upset_risk(self.probabilities).probability

    @computed_field
    @property
    def upset_risk_level(self) -> str:
        return assess_upset_risk(self.probabilities).level

    @computed_field
    @property
    def upset_favorite_outcome(self) -> str:
        return assess_upset_risk(self.probabilities).favorite_outcome


class PredictionResponse(_WithUpsetRisk):
    prediction_id: int
    home_team: str
    away_team: str
    host_country: str
    tournament: str
    tournament_category: str
    neutral: int
    predicted_outcome: str
    confidence: float
    model_version: str
    dataset_version: str


class UpsetRiskResponse(_WithUpsetRisk):
    home_team: str
    away_team: str
    host_country: str
    tournament: str
    tournament_category: str
    neutral: int
    predicted_outcome: str
    model_version: str
    dataset_version: str


class PredictionHistoryItem(_WithUpsetRisk):
    id: int
    home_team: str
    away_team: str
    host_country: str
    tournament: str
    neutral: int
    predicted_outcome: str
    confidence: float
    model_version_id: int
    dataset_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class TeamUpsetMatch(BaseModel):
    date: str
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    tournament: str
    winner: str
    loser: str
    upset_probability: float
    role: str
    """"caused" (the team won as the underdog) or "suffered" (lost as the favorite)."""


class TeamUpsetSummary(BaseModel):
    matches: int
    upsets_caused: int
    upsets_suffered: int


class TeamUpsetsResponse(BaseModel):
    team: str
    max_probability: float
    summary: TeamUpsetSummary
    matches: list[TeamUpsetMatch]


class ConfidenceBucketResponse(BaseModel):
    range_label: str
    count: int


class HistoryStatsResponse(BaseModel):
    total: int
    by_outcome: dict[str, int]
    confidence_buckets: list[ConfidenceBucketResponse]
