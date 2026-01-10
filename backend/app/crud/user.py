"""User CRUD operations."""

from typing import Any

from sqlmodel import Session

from app.core.security import get_password_hash, verify_password
from app.crud.base import CRUDBase
from app.models import User, UserCreate, UserUpdate


class UserCRUD(CRUDBase[User, UserCreate, UserUpdate]):
    """CRUD operations for User model."""

    def create(self, session: Session, obj_in: UserCreate | dict[str, Any]) -> User:
        """Create a new user with hashed password."""
        if isinstance(obj_in, dict):
            user_create = UserCreate.model_validate(obj_in)
        else:
            user_create = obj_in

        db_obj = User.model_validate(
            user_create,
            update={"hashed_password": get_password_hash(user_create.password)},
        )
        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
        return db_obj

    def update(
        self,
        session: Session,
        id: Any,
        obj_in: UserUpdate | dict[str, Any],
    ) -> User | None:
        """Update a user, handling password hashing."""
        db_user = session.get(User, id)
        if not db_user:
            return None

        if isinstance(obj_in, dict):
            user_data = obj_in
        else:
            user_data = obj_in.model_dump(exclude_unset=True)

        extra_data = {}
        if "password" in user_data:
            password = user_data.pop("password")
            hashed_password = get_password_hash(password)
            extra_data["hashed_password"] = hashed_password

        db_user.sqlmodel_update(user_data, update=extra_data)
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        return db_user

    def update_obj(self, session: Session, db_user: User, user_in: UserUpdate) -> User:
        """Update user object directly (for backward compatibility)."""
        user_data = user_in.model_dump(exclude_unset=True)
        extra_data = {}
        if "password" in user_data:
            password = user_data["password"]
            hashed_password = get_password_hash(password)
            extra_data["hashed_password"] = hashed_password
        db_user.sqlmodel_update(user_data, update=extra_data)
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        return db_user

    def get_by_email(self, session: Session, email: str) -> User | None:
        """Get user by email."""
        return self.get_by_field(session, "email", email)

    def authenticate(self, session: Session, email: str, password: str) -> User | None:
        """Authenticate a user by email and password."""
        db_user = self.get_by_email(session, email)
        if not db_user:
            return None
        if not verify_password(password, db_user.hashed_password):
            return None
        return db_user


# Global instance
user_crud = UserCRUD(User)
