"""Pydantic schemas for LLM client."""

from pydantic import BaseModel, Field


class LLMChatMessage(BaseModel):
    """Single chat message for LLM."""

    role: str = Field(..., description="Message role (e.g., 'user', 'assistant')")
    content: str = Field(..., description="Message content/text")
    images: list[str] | None = Field(
        default=None, description="Base64 encoded images (for multimodal models)"
    )


class LLMChatResponse(BaseModel):
    """Response from LLM chat API."""

    content: str = Field(..., description="Response content/text")
