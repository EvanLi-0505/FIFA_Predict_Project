from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.db.session import get_session
from backend.app.services import prediction_service
from backend.app.services.feature_service import NoActiveConfigurationError

router = APIRouter(prefix="/api/teams", tags=["teams"])


@router.get("", response_model=list[str])
def list_teams(session: Session = Depends(get_session)) -> list[str]:
    try:
        return prediction_service.list_known_teams(session)
    except NoActiveConfigurationError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
