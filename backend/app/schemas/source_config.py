import uuid
from datetime import datetime

from pydantic import ConfigDict, Field, HttpUrl
from sqlmodel import SQLModel

from app.models.enums import SourceType


# Specific configuration schemas for each data source
class GitConfig(SQLModel):
    """Git repository configuration."""

    repo_path: str = Field(..., description="Absolute path to git repository")
    branch: str = Field(default="main", description="Branch to track")


class DayflowConfig(SQLModel):
    """Dayflow API configuration."""

    api_url: HttpUrl = Field(..., description="Dayflow API URL")
    api_token: str = Field(..., description="API authentication token")


class SiYuanConfig(SQLModel):
    """SiYuan note-taking app configuration."""

    api_url: HttpUrl = Field(
        default="http://localhost:6806", description="SiYuan API URL"
    )
    api_token: str = Field(..., description="API authentication token")


# Base schema
class SourceConfigBase(SQLModel):
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
class SourceConfigUpdate(SQLModel):
    """Schema for updating source configuration."""

    name: str | None = None
    config_payload: dict | None = None
    is_active: bool | None = None


# Public schema
class SourceConfigPublic(SQLModel):
    """Schema for source configuration returned from API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: uuid.UUID
    type: SourceType = Field(..., description="Data source type")
    name: str = Field(..., description="User-defined name for this configuration")
    is_active: bool = Field(default=True, description="Whether this config is active")
    created_at: datetime
    updated_at: datetime


class SourceConfigsPublic(SQLModel):
    """Schema for paginated list of source configurations."""

    data: list[SourceConfigPublic]
    count: int
