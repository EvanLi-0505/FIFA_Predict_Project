from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from backend.app.db.session import get_session
from backend.app.schemas.dataset import DatasetResponse, DatasetUploadResponse
from backend.app.services import dataset_service
from backend.app.services.dataset_service import DatasetUploadError

router = APIRouter(prefix="/api/datasets", tags=["datasets"])


@router.get("", response_model=list[DatasetResponse])
def list_datasets(session: Session = Depends(get_session)) -> list[DatasetResponse]:
    datasets = dataset_service.list_datasets(session)
    return [DatasetResponse.model_validate(dataset) for dataset in datasets]


@router.post("/upload", response_model=DatasetUploadResponse)
async def upload_dataset(
    file: UploadFile = File(...), session: Session = Depends(get_session)
) -> DatasetUploadResponse:
    file_bytes = await file.read()

    try:
        result = dataset_service.upload_dataset(
            session,
            original_filename=file.filename or "upload.csv",
            file_bytes=file_bytes,
        )
    except DatasetUploadError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return DatasetUploadResponse(
        dataset=DatasetResponse.model_validate(result.dataset),
        validation_issues=[
            f"{issue.field}: {issue.message}" for issue in result.validation.issues
        ],
    )


@router.post("/{dataset_id}/activate", response_model=DatasetResponse)
def activate_dataset(
    dataset_id: int, session: Session = Depends(get_session)
) -> DatasetResponse:
    try:
        dataset = dataset_service.activate_dataset(session, dataset_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return DatasetResponse.model_validate(dataset)


@router.delete("/{dataset_id}", status_code=204)
def delete_dataset(dataset_id: int, session: Session = Depends(get_session)) -> None:
    try:
        dataset_service.delete_dataset(session, dataset_id)
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
