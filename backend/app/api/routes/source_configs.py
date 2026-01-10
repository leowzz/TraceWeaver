"""API routes for source configuration management."""

from typing import Any

from fastapi import APIRouter, HTTPException
from loguru import logger

from app.api.deps import CurrentUser, SessionDep
from app.connectors.registry import registry
from app.core.context import ctx
from app.crud.source_config import source_config_crud
from app.models import Message
from app.schemas.source_config import (
    SourceConfigCreate,
    SourceConfigPublic,
    SourceConfigsPublic,
    SourceConfigUpdate,
)

router = APIRouter(prefix="/source-configs", tags=["source-configs"])


@router.get("/", response_model=SourceConfigsPublic)
def read_source_configs(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve source configurations for the current user.
    """
    configs, count = source_config_crud.get_multi_by_user(
        session=session, user_id=current_user.id, skip=skip, limit=limit
    )
    return SourceConfigsPublic(data=configs, count=count)


@router.get("/{id}", response_model=SourceConfigPublic)
def read_source_config(session: SessionDep, current_user: CurrentUser, id: int) -> Any:
    """
    Get source configuration by ID.
    """
    config = source_config_crud.get(session=session, id=id)
    if not config:
        raise HTTPException(status_code=404, detail="Source configuration not found")

    # Ensure user can only access their own configs
    if config.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    return config


@router.post("/", response_model=SourceConfigPublic)
def create_source_config(
    *, session: SessionDep, current_user: CurrentUser, config_in: SourceConfigCreate
) -> Any:
    """
    Create new source configuration.
    """
    # Ensure the user_id matches the current user
    if config_in.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Cannot create configuration for another user"
        )

    config = source_config_crud.create(session=session, obj_in=config_in)
    return config


@router.put("/{id}", response_model=SourceConfigPublic)
def update_source_config(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: int,
    config_in: SourceConfigUpdate,
) -> Any:
    """
    Update a source configuration.
    """
    config = source_config_crud.get(session=session, id=id)
    if not config:
        raise HTTPException(status_code=404, detail="Source configuration not found")

    # Ensure user can only update their own configs
    if config.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    config = source_config_crud.update(session=session, id=id, obj_in=config_in)
    return config


@router.delete("/{id}")
def delete_source_config(
    session: SessionDep, current_user: CurrentUser, id: int
) -> Message:
    """
    Delete a source configuration.
    """
    config = source_config_crud.get(session=session, id=id)
    if not config:
        raise HTTPException(status_code=404, detail="Source configuration not found")

    # Ensure user can only delete their own configs
    if config.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    source_config_crud.delete(session=session, id=id)
    return Message(message="Source configuration deleted successfully")


@router.post("/{id}/test", response_model=Message)
async def test_source_config_connection(
    session: SessionDep, current_user: CurrentUser, id: int
) -> Message:
    """
    Test the connection to a configured data source.
    """
    logger.info(f"{ctx.user_id=}")
    config = source_config_crud.get(session=session, id=id)
    if not config:
        raise HTTPException(status_code=404, detail="Source configuration not found")

    # Ensure user can only test their own configs
    if config.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    try:
        connector = registry.get(config)
    except ValueError as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )

    try:
        # Test the connection (assuming connectors have a test_connection method)

        # Test the connection (assuming connectors have a test_connection method)
        # If they don't have this method, we'll need to add it
        if hasattr(connector, "test_connection"):
            await connector.test_connection()
            return Message(message="Connection test successful")
        else:
            # Fallback: just try to instantiate
            return Message(message="Connector initialized successfully")
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Connection test failed: {str(e)}",
        )
