import uuid

from sqlmodel import Session

from app.crud.user import user_crud
from app.models import Item, ItemCreate, User, UserCreate, UserUpdate


def create_item(*, session: Session, item_in: ItemCreate, owner_id: uuid.UUID) -> Item:
    db_item = Item.model_validate(item_in, update={"owner_id": owner_id})
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


# User CRUD wrapper functions for backward compatibility with tests
def create_user(*, session: Session, user_create: UserCreate) -> User:
    """Create a new user."""
    return user_crud.create(session, user_create)


def authenticate(*, session: Session, email: str, password: str) -> User | None:
    """Authenticate a user by email and password."""
    return user_crud.authenticate(session, email, password)


def update_user(*, session: Session, db_user: User, user_in: UserUpdate) -> User:
    """Update a user."""
    return user_crud.update_obj(session, db_user, user_in)
