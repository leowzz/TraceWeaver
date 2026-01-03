"""CRUD operations for VLM Prompt model."""

from app.crud.base import CRUDBase
from app.models.vlm_prompt import VLMPrompt


class VLMPromptCRUD(CRUDBase[VLMPrompt, VLMPrompt, VLMPrompt]):
    """CRUD operations for VLM Prompt."""

    pass


vlm_prompt_crud = VLMPromptCRUD(VLMPrompt)

