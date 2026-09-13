from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


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


class PredictionResponse(BaseModel):
    prediction_id: int
    home_team: str
    away_team: str
    host_country: str
    tournament: str
    tournament_category: str
    neutral: int
    probabilities: dict[str, float]
    predicted_outcome: str
    confidence: float
    model_version: str
    dataset_version: str


class PredictionHistoryItem(BaseModel):
    id: int
    home_team: str
    away_team: str
    host_country: str
    tournament: str
    neutral: int
    probabilities: dict[str, float]
    predicted_outcome: str
    confidence: float
    model_version_id: int
    dataset_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ConfidenceBucketResponse(BaseModel):
    range_label: str
    count: int


class HistoryStatsResponse(BaseModel):
    total: int
    by_outcome: dict[str, int]
    confidence_buckets: list[ConfidenceBucketResponse]
