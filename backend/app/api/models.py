from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.db.session import get_session
from backend.app.schemas.model import ModelVersionResponse, TrainModelRequest
from backend.app.services import model_service
from backend.app.services.model_service import ModelTrainingError

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("", response_model=list[ModelVersionResponse])
def list_models(session: Session = Depends(get_session)) -> list[ModelVersionResponse]:
    models = model_service.list_models(session)
    return [ModelVersionResponse.model_validate(model) for model in models]


@router.post("/train", response_model=ModelVersionResponse)
def train_model(
    request: TrainModelRequest, session: Session = Depends(get_session)
) -> ModelVersionResponse:
    try:
        model_version = model_service.train_model(
            session, dataset_id=request.dataset_id, model_type=request.model_type
        )
    except ModelTrainingError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return ModelVersionResponse.model_validate(model_version)


@router.post("/{model_version_id}/activate", response_model=ModelVersionResponse)
def activate_model(
    model_version_id: int, session: Session = Depends(get_session)
) -> ModelVersionResponse:
    try:
        model_version = model_service.activate_model(session, model_version_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return ModelVersionResponse.model_validate(model_version)


@router.delete("/{model_version_id}", status_code=204)
def delete_model(model_version_id: int, session: Session = Depends(get_session)) -> None:
    try:
        model_service.delete_model(session, model_version_id)
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
