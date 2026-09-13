from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.db.session import get_session
from backend.app.schemas.prediction import PredictionRequest, PredictionResponse
from backend.app.services import prediction_service
from backend.app.services.feature_service import NoActiveConfigurationError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/predictions", tags=["predictions"])


@router.post("", response_model=PredictionResponse)
def create_prediction(
    request: PredictionRequest, session: Session = Depends(get_session)
) -> PredictionResponse:
    try:
        outcome = prediction_service.predict(
            session,
            home_team=request.home_team,
            away_team=request.away_team,
            host_country=request.host_country,
            tournament=request.tournament,
        )
    except NoActiveConfigurationError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error

    logger.info(
        "prediction id=%s %s vs %s -> %s (model=%s dataset=%s)",
        outcome.prediction_id,
        outcome.home_team,
        outcome.away_team,
        outcome.predicted_outcome,
        outcome.model_version,
        outcome.dataset_version,
    )

    return PredictionResponse(
        prediction_id=outcome.prediction_id,
        home_team=outcome.home_team,
        away_team=outcome.away_team,
        host_country=outcome.host_country,
        tournament=outcome.tournament,
        tournament_category=outcome.tournament_category,
        neutral=outcome.neutral,
        probabilities=outcome.probabilities,
        predicted_outcome=outcome.predicted_outcome,
        confidence=outcome.confidence,
        model_version=outcome.model_version,
        dataset_version=outcome.dataset_version,
    )
