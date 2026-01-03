"""Activity Pydantic schemas for API validation."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import SourceType


# Base schema
class ActivityBase(BaseModel):
    """Base activity schema with common fields."""

    source_type: SourceType = Field(..., description="Data source type")
    source_id: str = Field(..., description="Unique ID from the source system")
    occurred_at: datetime = Field(..., description="When the activity occurred")
    title: str = Field(..., description="Short description")
    content: str | None = Field(None, description="Detailed content")
    extra_data: dict = Field(
        default_factory=dict, description="Source-specific metadata"
    )


# Create schema
class ActivityCreate(ActivityBase):
    """Schema for creating a new activity."""

    user_id: uuid.UUID
    source_config_id: int | None = None
    fingerprint: str = Field(..., description="SHA256 hash for deduplication")


# Update schema
class ActivityUpdate(BaseModel):
    """Schema for updating an activity."""

    title: str | None = None
    content: str | None = None
    extra_data: dict | None = None


# Public schema (returned from API)
class ActivityPublic(ActivityBase):
    """Schema for activity returned from API."""

    id: int
    user_id: uuid.UUID
    source_config_id: int | None
    fingerprint: str
    created_at: datetime
    updated_at: datetime


class ActivitiesPublic(BaseModel):
    """Schema for paginated list of activities."""

    data: list[ActivityPublic]
    count: int
