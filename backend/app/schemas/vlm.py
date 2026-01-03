"""Pydantic schemas for LLM image analysis task data."""

from pydantic import BaseModel, Field

from app.models.enums import ImageSourceType


class ImageAnalysisTaskData(BaseModel):
    """Schema for image analysis task data from queue.

    This schema validates the task data structure when processing
    image analysis tasks from Redis queue.
    """

    img_path: str = Field(..., description="Image path from source")
    source_type: ImageSourceType = Field(..., description="Source type")
    llm_prompt_id: int = Field(..., description="LLM prompt template ID")
    model_name: str = Field(..., description="LLM model name/ID to use")

