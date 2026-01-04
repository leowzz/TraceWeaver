"""Schemas for Image Analysis API."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import AnalysisStatus, ImageSourceType


class ImageAnalysisPublic(BaseModel):
    """Public schema for Image Analysis (API response)."""

    id: int
    img_path: str
    source_type: ImageSourceType
    llm_prompt_id: int
    model_name: str
    status: AnalysisStatus
    analysis_result: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ImageAnalysesPublic(BaseModel):
    """List of Image Analyses."""

    data: list[ImageAnalysisPublic]
    count: int
