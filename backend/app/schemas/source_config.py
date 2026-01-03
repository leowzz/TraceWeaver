"""Source configuration schemas including specific config schemas for each data source."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl

from app.models.enums import SourceType


# Specific configuration schemas for each data source
class GitConfig(BaseModel):
    """Git repository configuration."""

    repo_path: str = Field(..., description="Absolute path to git repository")
    branch: str = Field(default="main", description="Branch to track")


class DayflowConfig(BaseModel):
    """Dayflow API configuration."""

    api_url: HttpUrl = Field(..., description="Dayflow API URL")
    api_token: str = Field(..., description="API authentication token")


class SiYuanConfig(BaseModel):
    """SiYuan note-taking app configuration."""

    api_url: HttpUrl = Field(
        default="http://localhost:6806", description="SiYuan API URL"
    )
    api_token: str = Field(..., description="API authentication token")


# Base schema
class SourceConfigBase(BaseModel):
    """Base source configuration schema."""

    type: SourceType = Field(..., description="Data source type")
    name: str = Field(..., description="User-defined name for this configuration")
    config_payload: dict = Field(..., description="Source-specific configuration")
    is_active: bool = Field(default=True, description="Whether this config is active")


# Create schema
class SourceConfigCreate(SourceConfigBase):
    """Schema for creating a new source configuration."""

    user_id: uuid.UUID


# Update schema
class SourceConfigUpdate(BaseModel):
    """Schema for updating source configuration."""

    name: str | None = None
    config_payload: dict | None = None
    is_active: bool | None = None


# Public schema
class SourceConfigPublic(SourceConfigBase):
    """Schema for source configuration returned from API."""

    id: int
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class SourceConfigsPublic(BaseModel):
    """Schema for paginated list of source configurations."""

    data: list[SourceConfigPublic]
    count: int
