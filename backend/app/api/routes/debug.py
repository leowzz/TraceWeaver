"""Debug API routes - Admin only."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from pydantic import BaseModel
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
