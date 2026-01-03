"""Image Analysis model - Stores VLM image analysis results."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, Enum as SQLAEnum
from sqlmodel import Field, Relationship, SQLModel

from app.models.enums import AnalysisStatus, SourceType, ImageSourceType

if TYPE_CHECKING:
    from app.models.vlm_prompt import VLMPrompt


class ImageAnalysis(SQLModel, table=True):
    """Image analysis result from VLM processing.

    Stores the analysis results of images processed by VLM models.
    """

    __tablename__ = "image_analysis"

    # Primary key
    id: int | None = Field(default=None, primary_key=True)

    # Core fields
    img_path: str = Field(index=True, description="Image path from source")
    source_type: ImageSourceType = Field(
        index=True, description="Source type"
    )
    # Virtual foreign key (no DB constraint)
    vlm_prompt_id: int = Field(
        index=True, description="VLM prompt template ID"
    )
    analysis_result: str | None = Field(
        default=None, description="Analysis result text"
    )
    model_name: str = Field(description="VLM model name used (e.g., qwen3-vl:2B)")
    status: AnalysisStatus = Field(
        default=AnalysisStatus.PENDING,
        index=True,
        description="Analysis status",
    )
    error_message: str | None = Field(
        default=None, description="Error message if analysis failed"
    )

    # Relationship
    vlm_prompt: Optional["VLMPrompt"] = Relationship(
        back_populates="image_analyses",
        sa_relationship_kwargs={
            "primaryjoin": "ImageAnalysis.vlm_prompt_id==VLMPrompt.id",
            "foreign_keys": "[ImageAnalysis.vlm_prompt_id]",
        },
    )

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"onupdate": datetime.now},
    )
