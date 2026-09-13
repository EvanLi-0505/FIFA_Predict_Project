from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class DatasetResponse(BaseModel):
    id: int
    version_label: str
    name: str
    source: str
    is_builtin: bool
    is_active: bool
    validation_status: str
    row_count: int
    schema_version: str
    created_at: datetime
    activated_at: datetime | None

    model_config = {"from_attributes": True}


class DatasetUploadResponse(BaseModel):
    dataset: DatasetResponse
    validation_issues: list[str]
