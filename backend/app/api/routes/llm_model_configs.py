"""API routes for LLM Model Configuration management."""

from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep
from app.crud.llm_model_config import llm_model_config_crud
from app.models import Message
from app.schemas.llm_model_config import (
    LLMModelConfigCreate,
    LLMModelConfigPublic,
    LLMModelConfigsPublic,
    LLMModelConfigUpdate,
)

router = APIRouter(prefix="/llm-model-configs", tags=["llm-model-configs"])


@router.get("/", response_model=LLMModelConfigsPublic)
def read_llm_model_configs(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """Retrieve LLM Model configurations."""
    configs = llm_model_config_crud.get_multi(session=session, skip=skip, limit=limit)
    count = llm_model_config_crud.count(session=session)
    return LLMModelConfigsPublic(
        data=[
            LLMModelConfigPublic.model_validate(c, from_attributes=True)
            for c in configs
        ],
        count=count,
    )


@router.get("/{id}", response_model=LLMModelConfigPublic)
def read_llm_model_config(
    session: SessionDep, current_user: CurrentUser, id: int
) -> Any:
    """Get LLM Model configuration by ID."""
    config = llm_model_config_crud.get(session=session, id=id)
    if not config:
        raise HTTPException(status_code=404, detail="LLM Model Config not found")
    return config


@router.post("/", response_model=LLMModelConfigPublic)
def create_llm_model_config(
    *, session: SessionDep, current_user: CurrentUser, config_in: LLMModelConfigCreate
) -> Any:
    """Create new LLM Model configuration."""
    config = llm_model_config_crud.create(session=session, obj_in=config_in)
    return config


@router.put("/{id}", response_model=LLMModelConfigPublic)
def update_llm_model_config(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: int,
    config_in: LLMModelConfigUpdate,
) -> Any:
    """Update an LLM Model configuration."""
    config = llm_model_config_crud.get(session=session, id=id)
    if not config:
        raise HTTPException(status_code=404, detail="LLM Model Config not found")

    config = llm_model_config_crud.update(session=session, id=id, obj_in=config_in)
    return config


@router.delete("/{id}")
def delete_llm_model_config(
    session: SessionDep, current_user: CurrentUser, id: int
) -> Message:
    """Delete an LLM Model configuration."""
    config = llm_model_config_crud.get(session=session, id=id)
    if not config:
        raise HTTPException(status_code=404, detail="LLM Model Config not found")

    llm_model_config_crud.delete(session=session, id=id)
    return Message(message="LLM Model Config deleted successfully")
