"""API routes for LLM Prompt management."""

from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from loguru import logger

from app.api.deps import CurrentUser, SessionDep
from app.clients.llm.client import LLMClient, LLMClientError
from app.crud.llm_model_config import llm_model_config_crud
from app.crud.llm_prompt import llm_prompt_crud
from app.models import Message
from app.schemas.llm_prompt import (
    LLMPromptCreate,
    LLMPromptPublic,
    LLMPromptsPublic,
    LLMPromptTestResponse,
    LLMPromptUpdate,
)

router = APIRouter(prefix="/llm-prompts", tags=["llm-prompts"])


@router.get("/", response_model=LLMPromptsPublic)
def read_llm_prompts(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """Retrieve LLM Prompts."""
    prompts = llm_prompt_crud.get_multi(session=session, skip=skip, limit=limit)
    count = llm_prompt_crud.count(session=session)
    return LLMPromptsPublic(
        data=[LLMPromptPublic.model_validate(p, from_attributes=True) for p in prompts],
        count=count,
    )


@router.get("/{id}", response_model=LLMPromptPublic)
def read_llm_prompt(session: SessionDep, current_user: CurrentUser, id: int) -> Any:
    """Get LLM Prompt by ID."""
    prompt = llm_prompt_crud.get(session=session, id=id)
    if not prompt:
        raise HTTPException(status_code=404, detail="LLM Prompt not found")
    return prompt


@router.post("/", response_model=LLMPromptPublic)
def create_llm_prompt(
    *, session: SessionDep, current_user: CurrentUser, prompt_in: LLMPromptCreate
) -> Any:
    """Create new LLM Prompt."""
    prompt = llm_prompt_crud.create(session=session, obj_in=prompt_in)
    return prompt


@router.put("/{id}", response_model=LLMPromptPublic)
def update_llm_prompt(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: int,
    prompt_in: LLMPromptUpdate,
) -> Any:
    """Update an LLM Prompt."""
    prompt = llm_prompt_crud.get(session=session, id=id)
    if not prompt:
        raise HTTPException(status_code=404, detail="LLM Prompt not found")

    prompt = llm_prompt_crud.update(session=session, id=id, obj_in=prompt_in)
    return prompt


@router.delete("/{id}")
def delete_llm_prompt(
    session: SessionDep, current_user: CurrentUser, id: int
) -> Message:
    """Delete an LLM Prompt."""
    prompt = llm_prompt_crud.get(session=session, id=id)
    if not prompt:
        raise HTTPException(status_code=404, detail="LLM Prompt not found")

    llm_prompt_crud.delete(session=session, id=id)
    return Message(message="LLM Prompt deleted successfully")


@router.post("/{id}/test", response_model=LLMPromptTestResponse)
async def test_llm_prompt(
    session: SessionDep,
    current_user: CurrentUser,
    id: int,
    llm_model_config_id: int = Form(...),
    image: UploadFile = File(...),
) -> LLMPromptTestResponse:
    """Test an LLM Prompt with an uploaded image.

    This endpoint allows testing a prompt template with a specific LLM model
    and an uploaded image to preview the analysis result.
    """
    # Get prompt
    prompt = llm_prompt_crud.get(session=session, id=id)
    if not prompt:
        raise HTTPException(status_code=404, detail="LLM Prompt not found")

    # Get model config
    model_config = llm_model_config_crud.get(session=session, id=llm_model_config_id)
    if not model_config:
        raise HTTPException(status_code=404, detail="LLM Model Config not found")

    if not model_config.is_active:
        raise HTTPException(status_code=400, detail="LLM Model Config is not active")

    # Read image bytes
    try:
        image_bytes = await image.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read image: {e}")

    # Call LLM
    client = None
    try:
        client = LLMClient(
            provider=model_config.provider,
            model_id=model_config.model_id,
            base_url=model_config.base_url,
            api_key=model_config.api_key,
            config=model_config.config or {},
        )

        response = await client.analyze_image(image_bytes, prompt.content)
        return LLMPromptTestResponse(result=response.content)

    except LLMClientError as e:
        logger.error(f"LLM client error during test: {e}")
        raise HTTPException(status_code=500, detail=f"LLM analysis failed: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during LLM test: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Test failed: {e}")
    finally:
        if client is not None:
            await client.close()
