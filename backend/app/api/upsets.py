from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.db.session import get_session
from backend.app.schemas.prediction import (
    PredictionRequest,
    TeamUpsetsResponse,
    UpsetRiskResponse,
)
from backend.app.services import prediction_service, upset_service
from backend.app.services.feature_service import NoActiveConfigurationError

router = APIRouter(prefix="/api/upsets", tags=["upsets"])


@router.post("/risk", response_model=UpsetRiskResponse)
def assess_upset_risk(
    request: PredictionRequest, session: Session = Depends(get_session)
) -> UpsetRiskResponse:
    """Upset risk for a hypothetical match. Not recorded in prediction history."""

    try:
        outcome = prediction_service.predict(
            session,
            home_team=request.home_team,
            away_team=request.away_team,
            host_country=request.host_country,
            tournament=request.tournament,
            record_history=False,
        )
    except NoActiveConfigurationError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error

    return UpsetRiskResponse(
        home_team=outcome.home_team,
        away_team=outcome.away_team,
        host_country=outcome.host_country,
        tournament=outcome.tournament,
        tournament_category=outcome.tournament_category,
        neutral=outcome.neutral,
        probabilities=outcome.probabilities,
        predicted_outcome=outcome.predicted_outcome,
        model_version=outcome.model_version,
        dataset_version=outcome.dataset_version,
    )


@router.get("/teams/{team_name}", response_model=TeamUpsetsResponse)
def get_team_upsets(
    team_name: str,
    limit: int = Query(default=20, ge=1, le=200),
    session: Session = Depends(get_session),
) -> TeamUpsetsResponse:
    """Historical upsets the team caused or suffered, most recent first."""

    try:
        history = upset_service.get_team_upsets(session, team_name, limit=limit)
    except NoActiveConfigurationError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error

    return TeamUpsetsResponse.model_validate(history)
