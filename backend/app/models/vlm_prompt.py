"""VLM Prompt model - Stores VLM prompt templates for image analysis."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.image_analysis import ImageAnalysis


class VLMPrompt(SQLModel, table=True):
    """VLM Prompt template for image analysis.

    Stores reusable prompt templates that define how images should be analyzed.
    """

    __tablename__ = "vlm_prompt"

    # Primary key
    id: int | None = Field(default=None, primary_key=True)

    # Core fields
    name: str = Field(index=True, description="Prompt template name")
    content: str = Field(description="Prompt template content")
    is_active: bool = Field(default=True, description="Whether this prompt is active")

    # Relationship
    image_analyses: list["ImageAnalysis"] = Relationship(
        back_populates="vlm_prompt",
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

