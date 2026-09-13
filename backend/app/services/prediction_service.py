"""Prediction service: the only place that calls `core.prediction.predictor`.

Wraps a prediction with dataset/model version stamping and persists it to
prediction history (Development Prompt.md Sections 19-20).
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from backend.app.services.feature_service import get_inference_context
from core.prediction.predictor import predict_match
from database.repositories.sqlalchemy_repositories import PredictionRepositoryImpl

_prediction_repo = PredictionRepositoryImpl()


@dataclass
class PredictionOutcome:
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


def predict(
    session: Session,
    *,
    home_team: str,
    away_team: str,
    host_country: str,
    tournament: str,
) -> PredictionOutcome:
    context = get_inference_context(session)

    result = predict_match(
        home_team=home_team,
        away_team=away_team,
        host_country=host_country,
        tournament=tournament,
        model=context.model,
        scaler=context.scaler,
        team_state_index=context.team_state_index,
        cold_start_fill_values=context.cold_start_fill_values,
        tournament_dummy_columns=context.tournament_dummy_columns,
        feature_columns=context.feature_columns,
    )

    record = _prediction_repo.create(
        session,
        model_version_id=context.model_version_id,
        dataset_id=context.dataset_id,
        home_team=result.home_team,
        away_team=result.away_team,
        host_country=result.host_country,
        tournament=result.tournament,
        neutral=result.neutral,
        probabilities=result.probabilities,
        predicted_outcome=result.predicted_outcome,
        confidence=result.confidence,
    )
    session.commit()

    return PredictionOutcome(
        prediction_id=record.id,
        home_team=result.home_team,
        away_team=result.away_team,
        host_country=result.host_country,
        tournament=result.tournament,
        tournament_category=result.tournament_category,
        neutral=result.neutral,
        probabilities=result.probabilities,
        predicted_outcome=result.predicted_outcome,
        confidence=result.confidence,
        model_version=context.model_id,
        dataset_version=context.dataset_version_label,
    )


def list_known_teams(session: Session) -> list[str]:
    context = get_inference_context(session)
    return context.known_teams
