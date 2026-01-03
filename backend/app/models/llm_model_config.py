"""LLM/LLM Model Configuration model - Stores model provider configurations."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

from app.models.enums import LLMProvider

if TYPE_CHECKING:
    from app.models.image_analysis import ImageAnalysis


class LLMModelConfig(SQLModel, table=True):
    """LLM/LLM Model Configuration.

    Stores configuration for different LLM/LLM model providers,
    including provider type, model ID, base_url, and other connection settings.
    """

    __tablename__ = "llm_model_config"

    # Primary key
    id: int | None = Field(default=None, primary_key=True)

    # Core fields
    name: str = Field(index=True, description="Configuration name (e.g., 'GPT-4 Vision', 'Claude 3')")
    provider: LLMProvider = Field(index=True, description="Model provider type")
    model_id: str = Field(index=True, description="Model ID/name (e.g., 'gpt-4-vision-preview', 'claude-3-opus')")
    base_url: str = Field(description="API base_url URL")
    api_key: str | None = Field(default=None, description="API key (optional, may be stored elsewhere)")

    # Additional configuration stored as JSON
    config: dict | None = Field(default_factory=dict, sa_column=Column(JSONB), description="Additional provider-specific configuration")

    # Status
    is_active: bool = Field(default=True, index=True, description="Whether this config is active")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"onupdate": datetime.now},
    )
