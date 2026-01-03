import uuid

from sqlmodel import Session

from app.models import Item, ItemCreate
from typing import Any
# Import user_crud for backward compatibility
from app.crud.user import user_crud

# Backward compatibility functions
def create_user(*, session: Session, user_create) -> Any:  # type: ignore
    """Backward compatibility wrapper for user_crud.create."""
    return user_crud.create(session, user_create)


def update_user(*, session: Session, db_user, user_in) -> Any:  # type: ignore
    """Backward compatibility wrapper for user_crud.update_obj."""
    return user_crud.update_obj(session, db_user, user_in)


def get_user_by_email(*, session: Session, email: str) -> Any:  # type: ignore
    """Backward compatibility wrapper for user_crud.get_by_email."""
    return user_crud.get_by_email(session, email)


def authenticate(*, session: Session, email: str, password: str) -> Any:  # type: ignore
    """Backward compatibility wrapper for user_crud.authenticate."""
    return user_crud.authenticate(session, email, password)


def create_item(*, session: Session, item_in: ItemCreate, owner_id: uuid.UUID) -> Item:
    db_item = Item.model_validate(item_in, update={"owner_id": owner_id})
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item
