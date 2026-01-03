"""Activity model - Unified activity representation from all data sources."""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum as SQLAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

from app.models.enums import SourceType


class Activity(SQLModel, table=True):
    """Unified activity model - standard representation of activities from all data sources.

    This model follows the hexagonal architecture pattern where all external data sources
    (Git, Dayflow, SiYuan) are normalized into this unified structure.
    """

    __tablename__ = "activity"

    # Primary key
    id: int | None = Field(default=None, primary_key=True)

    # Virtual foreign keys (no DB constraints)
    user_id: uuid.UUID = Field(index=True)
    source_config_id: int | None = Field(default=None, index=True)

    # Core fields
    source_type: SourceType = Field(index=True)
    title: str  # Short description (e.g., commit message first line)
    content: str | None = (
        None  # Detailed content (e.g., full commit message, note content)
    )

    # Extension fields
    extra_data: dict = Field(
        default_factory=dict, sa_column=Column(JSONB)
    )  # Source-specific data stored as JSONB

    # Deduplication
    fingerprint: str = Field(unique=True, index=True)  # SHA256 hash for deduplication

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
