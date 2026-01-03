"""CRUD operations for LLM Prompt model."""

from app.crud.base import CRUDBase
from app.models.llm_prompt import LLMPrompt


class LLMPromptCRUD(CRUDBase[LLMPrompt, LLMPrompt, LLMPrompt]):
    """CRUD operations for LLM Prompt."""

    pass


llm_prompt_crud = LLMPromptCRUD(LLMPrompt)

