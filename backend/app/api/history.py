from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.db.session import get_session
from backend.app.schemas.prediction import (
    ConfidenceBucketResponse,
    HistoryStatsResponse,
    PredictionHistoryItem,
)
from backend.app.services import history_service

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("", response_model=list[PredictionHistoryItem])
def list_prediction_history(
    limit: int = Query(default=50, ge=1, le=500),
    session: Session = Depends(get_session),
) -> list[PredictionHistoryItem]:
    records = history_service.list_recent(session, limit=limit)
    return [PredictionHistoryItem.model_validate(record) for record in records]


@router.get("/stats", response_model=HistoryStatsResponse)
def get_history_stats(session: Session = Depends(get_session)) -> HistoryStatsResponse:
    stats = history_service.get_stats(session)
    return HistoryStatsResponse(
        total=stats.total,
        by_outcome=stats.by_outcome,
        confidence_buckets=[
            ConfidenceBucketResponse(range_label=bucket.range_label, count=bucket.count)
            for bucket in stats.confidence_buckets
        ],
    )


@router.delete("/{prediction_id}", status_code=204)
def delete_prediction(prediction_id: int, session: Session = Depends(get_session)) -> None:
    history_service.delete_prediction(session, prediction_id)


@router.delete("", status_code=200)
def clear_history(session: Session = Depends(get_session)) -> dict[str, int]:
    deleted_count = history_service.clear_history(session)
    return {"deleted_count": deleted_count}
