"""Source configuration CRUD operations."""

from typing import Any

from sqlmodel import Session, func, select

from app.crud.base import CRUDBase
from app.models.source_config import SourceConfig
from app.schemas.source_config import SourceConfigCreate, SourceConfigUpdate


class SourceConfigCRUD(CRUDBase[SourceConfig, SourceConfigCreate, SourceConfigUpdate]):
    """CRUD operations for SourceConfig model."""

    def get_multi_by_user(
        self, session: Session, *, user_id: Any, skip: int = 0, limit: int = 100
    ) -> tuple[list[SourceConfig], int]:
        """
        Retrieve source configurations for a specific user.
        """
        count_statement = (
            select(func.count())
            .select_from(SourceConfig)
            .where(SourceConfig.user_id == user_id)
        )
        count = session.exec(count_statement).one()

        statement = (
            select(SourceConfig)
            .where(SourceConfig.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .order_by(SourceConfig.created_at.desc())
        )
        configs = session.exec(statement).all()

        return list(configs), count


# Global instance
source_config_crud = SourceConfigCRUD(SourceConfig)
