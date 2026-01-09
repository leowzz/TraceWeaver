"""Debug API routes - Admin only."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from pydantic import BaseModel, Field
from sqlmodel import select

from app.api.deps import SessionDep, get_current_active_superuser
from app.connectors import registry
from app.models.enums import SourceType
from app.models.source_config import SourceConfig
from app.models.user import User

router = APIRouter(prefix="/debug", tags=["debug"])


class SiYuanSQLRequest(BaseModel):
    """Request body for SiYuan SQL execution."""
    stmt: str


class SiYuanSQLResponse(BaseModel):
    """Response for SiYuan SQL execution."""
    success: bool
    data: list[dict] | None = None
    error: str | None = None


class VectorSearchRequest(BaseModel):
    """Request body for vector search."""
    query: str
    top_k: int = Field(default=5, ge=1, le=50)
    min_similarity: float = Field(default=0.0, ge=0.0, le=1.0)


class VectorSearchResult(BaseModel):
    """Single vector search result."""
    activity_id: int
    activity_title: str
    chunk_text: str
    chunk_index: int
    similarity: float
    metadata: dict


class VectorSearchResponse(BaseModel):
    """Response for vector search."""
    success: bool
    query: str
    results: list[VectorSearchResult] | None = None
    error: str | None = None
    query_embedding_dimensions: int | None = None


@router.post("/siyuan-sql", response_model=SiYuanSQLResponse)
async def execute_siyuan_sql(
    session: SessionDep,
    request: SiYuanSQLRequest,
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """Execute SQL query on SiYuan.
    
    Admin only. Use for debugging purposes.
    """
    try:
        # Get active SiYuan source config
        statement = select(SourceConfig).where(
            SourceConfig.type == SourceType.SIYUAN,
            SourceConfig.is_active == True,
        )
        source_config = session.exec(statement).first()
        
        if not source_config:
            raise HTTPException(
                status_code=400,
                detail="No active SiYuan source configuration found"
            )
        
        # Get SiYuan connector and client
        connector = registry.get(source_config)
        from app.connectors.impl.siyuan_connector import SiYuanConnector
        
        if not isinstance(connector, SiYuanConnector):
            raise HTTPException(
                status_code=500,
                detail="Invalid connector type for SiYuan"
            )
        
        client = connector._get_client()
        
        # Execute SQL
        logger.info(f"Admin {current_user.email} executing SiYuan SQL: {request.stmt[:100]}...")
        result = await client.query_sql(request.stmt)
        
        return SiYuanSQLResponse(
            success=True,
            data=result if isinstance(result, list) else [result] if result else [],
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SiYuan SQL execution failed: {e}")
        return SiYuanSQLResponse(
            success=False,
            error=str(e),
        )


@router.post("/vector-search", response_model=VectorSearchResponse)
async def vector_search(
    session: SessionDep,
    request: VectorSearchRequest,
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """Execute vector similarity search.
    
    Admin only. Use for debugging and testing vector embeddings.
    """
    from sqlalchemy import text
    from app.services.embedding_service import EmbeddingService
    
    try:
        # Initialize embedding service
        embedding_service = EmbeddingService()
        
        # Generate query embedding
        logger.info(
            f"Admin {current_user.email} executing vector search: {request.query[:100]}..."
        )
        query_embedding = embedding_service.embedder.get_embedding(request.query)
        query_embedding_dimensions = len(query_embedding)
        
        # Prepare query embedding for pgvector
        # pgvector expects vector in string format like '[1.0, 2.0, ...]'
        embedding_str = str(query_embedding)
        
        # Execute vector similarity search
        sql = text("""
            SELECT 
                ae.id,
                ae.activity_id,
                ae.chunk_text,
                ae.chunk_index,
                ae.chunk_metadata,
                a.title as activity_title,
                1 - (ae.embedding <=> :query_embedding) AS similarity
            FROM activity_embedding ae
            JOIN activity a ON ae.activity_id = a.id
            WHERE ae.user_id = :user_id
              AND 1 - (ae.embedding <=> :query_embedding) >= :min_similarity
            ORDER BY ae.embedding <=> :query_embedding
            LIMIT :top_k
        """)
        
        result = session.execute(
            sql,
            {
                "query_embedding": embedding_str,
                "user_id": str(current_user.id),
                "min_similarity": request.min_similarity,
                "top_k": request.top_k,
            }
        ).fetchall()
        
        # Format results
        search_results = []
        for row in result:
            search_results.append(
                VectorSearchResult(
                    activity_id=row.activity_id,
                    activity_title=row.activity_title,
                    chunk_text=row.chunk_text,
                    chunk_index=row.chunk_index,
                    similarity=float(row.similarity),
                    metadata=row.chunk_metadata or {},
                )
            )
        
        logger.info(f"Vector search returned {len(search_results)} results")
        
        return VectorSearchResponse(
            success=True,
            query=request.query,
            results=search_results,
            query_embedding_dimensions=query_embedding_dimensions,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Vector search failed: {e}", exc_info=True)
        return VectorSearchResponse(
            success=False,
            query=request.query,
            error=str(e),
        )
