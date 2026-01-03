"""Activity CRUD operations."""

from app.crud.base import CRUDBase
from app.models.activity import Activity
from app.schemas.activity import ActivityCreate, ActivityUpdate


class ActivityCRUD(CRUDBase[Activity, ActivityCreate, ActivityUpdate]):
    """CRUD operations for Activity model."""

    pass


# Global instance
activity_crud = ActivityCRUD(Activity)
