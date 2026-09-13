"""Prediction history management: listing, deletion, and dashboard
aggregates (Development Prompt.md Section 20, plus the Dashboard page
requested after Stage 4 manual testing).
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from database.models import Prediction
from database.repositories.sqlalchemy_repositories import PredictionRepositoryImpl

_prediction_repo = PredictionRepositoryImpl()

# Fixed-width confidence buckets (confidence is always the max class
# probability, so it never falls below 1/3 for this 3-class problem — but
# the buckets stay generic 0-100% in case a future model has more classes).
_BUCKET_WIDTH = 0.1


@dataclass
class ConfidenceBucket:
    range_label: str
    count: int


@dataclass
class HistoryStats:
    total: int
    by_outcome: dict[str, int]
    confidence_buckets: list[ConfidenceBucket]


def list_recent(session: Session, limit: int = 50) -> list[Prediction]:
    return _prediction_repo.list_recent(session, limit=limit)


def delete_prediction(session: Session, prediction_id: int) -> None:
    _prediction_repo.delete(session, prediction_id)
    session.commit()


def clear_history(session: Session) -> int:
    deleted_count = _prediction_repo.delete_all(session)
    session.commit()
    return deleted_count


def get_stats(session: Session) -> HistoryStats:
    by_outcome = _prediction_repo.count_by_outcome(session)
    confidences = _prediction_repo.list_all_confidences(session)

    bucket_counts: dict[int, int] = {}
    for confidence in confidences:
        bucket_index = min(int(confidence / _BUCKET_WIDTH), int(1 / _BUCKET_WIDTH) - 1)
        bucket_counts[bucket_index] = bucket_counts.get(bucket_index, 0) + 1

    num_buckets = int(1 / _BUCKET_WIDTH)
    confidence_buckets = [
        ConfidenceBucket(
            range_label=f"{int(i * _BUCKET_WIDTH * 100)}-{int((i + 1) * _BUCKET_WIDTH * 100)}%",
            count=bucket_counts.get(i, 0),
        )
        for i in range(num_buckets)
    ]

    return HistoryStats(
        total=sum(by_outcome.values()),
        by_outcome=by_outcome,
        confidence_buckets=confidence_buckets,
    )
