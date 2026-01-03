"""Source configuration model - User's data source connection settings."""

import uuid
from datetime import datetime

from sqlalchemy import Column, Enum as SQLAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

from app.models.enums import SourceType


class SourceConfig(SQLModel, table=True):
    """Data source configuration - stores user's connection settings for external data sources.

    Example config_payload for different source types:

    Git:
        {"repo_path": "/path/to/repo", "branch": "main"}

    Dayflow:
        {"api_token": "xxx", "api_url": "https://api.dayflow.com"}

    SiYuan:
        {"api_url": "http://localhost:6806", "api_token": "xxx"}
    """

    __tablename__ = "source_config"
    # Primary key
    id: int | None = Field(default=None, primary_key=True)

    # Virtual foreign key (no DB constraint)
    user_id: uuid.UUID = Field(index=True)

    # Configuration fields
    type: SourceType = Field(index=True)
    name: str  # User-defined name (e.g., "Backend Repo", "Work Dayflow")
    config_payload: dict = Field(
        default_factory=dict, sa_column=Column(JSONB)
    )  # Connection config stored as JSONB

    # Status
    is_active: bool = Field(default=True)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
