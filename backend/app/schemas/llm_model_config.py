"""Schemas for LLM Model Configuration API."""

from pydantic import BaseModel, Field

from app.models.enums import LLMProvider


class LLMModelConfigBase(BaseModel):
    """Base schema for LLM Model Config."""

    name: str = Field(..., description="Configuration name")
    provider: LLMProvider = Field(..., description="Model provider type")
    model_id: str = Field(..., description="Model ID/name")
    base_url: str = Field(..., description="API base URL")
    config: dict | None = Field(default=None, description="Additional configuration")
    is_active: bool = Field(default=True, description="Whether config is active")


class LLMModelConfigCreate(LLMModelConfigBase):
    """Schema for creating LLM Model Config."""

    api_key: str | None = Field(default=None, description="API key")


class LLMModelConfigUpdate(BaseModel):
    """Schema for updating LLM Model Config."""

    name: str | None = None
    provider: LLMProvider | None = None
    model_id: str | None = None
    base_url: str | None = None
    api_key: str | None = None
    config: dict | None = None
    is_active: bool | None = None


class LLMModelConfigPublic(LLMModelConfigBase):
    """Public schema for LLM Model Config (API response)."""

    id: int
    # api_key is intentionally excluded for security


class LLMModelConfigsPublic(BaseModel):
    """List of LLM Model Configs."""

    data: list[LLMModelConfigPublic]
    count: int
