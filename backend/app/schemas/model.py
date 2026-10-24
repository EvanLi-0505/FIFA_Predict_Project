from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from core.config import DEFAULT_FEATURE_VERSION


class ModelVersionResponse(BaseModel):
    id: int
    model_id: str
    model_type: str
    dataset_id: int
    feature_version: str
    metrics: dict[str, Any] | None
    is_active: bool
    is_builtin: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TrainModelRequest(BaseModel):
    dataset_id: int
    model_type: str = Field(default="logistic_regression")
    feature_version: str = Field(default=DEFAULT_FEATURE_VERSION)
