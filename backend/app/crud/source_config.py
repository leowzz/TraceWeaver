"""Source configuration CRUD operations."""

from app.crud.base import CRUDBase
from app.models.source_config import SourceConfig
from app.schemas.source_config import SourceConfigCreate, SourceConfigUpdate


class SourceConfigCRUD(CRUDBase[SourceConfig, SourceConfigCreate, SourceConfigUpdate]):
    """CRUD operations for SourceConfig model."""

    pass


# Global instance
source_config_crud = SourceConfigCRUD(SourceConfig)
