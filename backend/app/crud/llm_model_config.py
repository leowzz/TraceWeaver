"""CRUD operations for LLM Model Config model."""

from sqlmodel import Session, select

from app.crud.base import CRUDBase
from app.models.enums import LLMProvider
from app.models.llm_model_config import LLMModelConfig


class LLMModelConfigCRUD(CRUDBase[LLMModelConfig, LLMModelConfig, LLMModelConfig]):
    """CRUD operations for LLM Model Config."""

    def get_by_model_name(
        self, session: Session, model_name: str
    ) -> LLMModelConfig | None:
        """Get model config by model name/ID.

        Args:
            session: Database session
            model_name: Model name/ID to lookup

        Returns:
            Model config if found, None otherwise
        """
        statement = select(LLMModelConfig).where(
            LLMModelConfig.model_id == model_name, LLMModelConfig.is_active == True
        )
        return session.exec(statement).first()

    def get_active_by_provider(
        self, session: Session, provider: LLMProvider
    ) -> list[LLMModelConfig]:
        """Get all active model configs for a provider.

        Args:
            session: Database session
            provider: Provider type

        Returns:
            List of active model configs
        """
        statement = select(LLMModelConfig).where(
            LLMModelConfig.provider == provider, LLMModelConfig.is_active == True
        )
        return list(session.exec(statement).all())


llm_model_config_crud = LLMModelConfigCRUD(LLMModelConfig)

