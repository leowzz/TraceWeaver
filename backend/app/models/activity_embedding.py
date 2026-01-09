"""ActivityEmbedding model for storing vector embeddings of activities."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class ActivityEmbedding(SQLModel, table=True):
    """Vector embeddings of activity content chunks.
    
    Each activity can have multiple embeddings (one per chunk).
    Used for semantic search and RAG.
    """
    
    __tablename__ = "activity_embedding"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    activity_id: int = Field(index=True, description="Foreign key to activity.id")
    user_id: UUID = Field(index=True, description="User ID for data isolation")
    
    # Vector data
    embedding: list[float] = Field(
        sa_column=Column(Vector(1024)),
        description="Vector embedding of the chunk"
    )

    # Chunk metadata
    chunk_text: str = Field(description="Original text of this chunk")
    chunk_index: int = Field(description="Position of chunk in the activity")
    chunk_metadata: dict = Field(
        default_factory=dict,
        sa_column=Column(JSONB),
        description="Additional metadata about the chunk"
    )
    
    # Model information
    embedder_model: str = Field(description="Name of the embedding model used")
    embedder_provider: str = Field(description="Embedding provider (e.g., 'ollama')")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
