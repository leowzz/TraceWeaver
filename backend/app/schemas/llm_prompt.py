"""Schemas for LLM Prompt API."""

from pydantic import BaseModel, Field


class LLMPromptBase(BaseModel):
    """Base schema for LLM Prompt."""

    name: str = Field(..., description="Prompt template name")
    content: str = Field(..., description="Prompt template content")
    is_active: bool = Field(default=True, description="Whether prompt is active")


class LLMPromptCreate(LLMPromptBase):
    """Schema for creating LLM Prompt."""

    pass


class LLMPromptUpdate(BaseModel):
    """Schema for updating LLM Prompt."""

    name: str | None = None
    content: str | None = None
    is_active: bool | None = None


class LLMPromptPublic(LLMPromptBase):
    """Public schema for LLM Prompt (API response)."""

    id: int


class LLMPromptsPublic(BaseModel):
    """List of LLM Prompts."""

    data: list[LLMPromptPublic]
    count: int


class LLMPromptTestRequest(BaseModel):
    """Request schema for testing LLM Prompt with an image."""

    llm_model_config_id: int = Field(..., description="ID of LLM Model Config to use")


class LLMPromptTestResponse(BaseModel):
    """Response schema for LLM Prompt test."""

    result: str = Field(..., description="Analysis result from LLM")
