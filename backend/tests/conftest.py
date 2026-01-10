import tempfile
import uuid
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import JSON, String, TypeDecorator
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.sqlite import CHAR
from sqlmodel import Session, SQLModel, create_engine

from app.api.deps import get_db
from app.core.config import settings
from app.core.db import init_db
from app.main import app

# Import all models to ensure they are registered with SQLModel.metadata
# Import from models.__init__ first to get all models
from app.models import (  # noqa: F401
    Activity,
    ImageAnalysis,
    Item,
    LLMPrompt,
    SourceConfig,
    User,
)

# Explicitly import model classes to ensure they're available for relationship resolution
from app.models.image_analysis import ImageAnalysis  # noqa: F401
from app.models.llm_prompt import LLMPrompt  # noqa: F401

# Ensure User and Item are imported (they're in the same file)
from app.models.user import Item, User  # noqa: F401
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import get_superuser_token_headers


class GUID(TypeDecorator):
    """Platform-independent GUID type for SQLite compatibility.

    Uses CHAR(36) on SQLite, and uses the native UUID type on PostgreSQL.
    This prevents the 'str' object has no attribute 'hex' error when SQLAlchemy
    tries to process UUID values from SQLite.
    """

    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(uuid.UUID)
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return str(value) if isinstance(value, uuid.UUID) else value
        else:
            # For SQLite, always store as string
            if isinstance(value, uuid.UUID):
                return str(value)
            elif isinstance(value, str):
                # Validate it's a valid UUID string
                try:
                    uuid.UUID(value)
                    return value
                except (ValueError, AttributeError):
                    return str(uuid.UUID(value))
            else:
                return str(uuid.UUID(str(value)))

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        # Convert string from SQLite to UUID object
        if isinstance(value, str):
            try:
                return uuid.UUID(value)
            except (ValueError, AttributeError):
                # If it's already a valid UUID string format, try direct conversion
                return uuid.UUID(value)
        elif isinstance(value, uuid.UUID):
            return value
        else:
            # Fallback: try to convert whatever we got
            return uuid.UUID(str(value))


def replace_jsonb_with_json():
    """Replace JSONB columns with JSON and UUID types with GUID for SQLite compatibility."""
    from sqlalchemy import UUID as SQLA_UUID

    for table in SQLModel.metadata.tables.values():
        for column in table.columns:
            if isinstance(column.type, JSONB):
                column.type = JSON()
            # Replace UUID types with GUID for SQLite compatibility
            # Check multiple ways UUID might be represented
            elif isinstance(column.type, SQLA_UUID):
                column.type = GUID()
            else:
                # Try to check python_type safely - some types raise NotImplementedError
                # Use getattr with exception handling since hasattr() can trigger the exception
                python_type = None
                try:
                    python_type = column.type.python_type
                except (NotImplementedError, AttributeError):
                    # Type doesn't support python_type or doesn't have it, skip this check
                    pass

                if python_type == uuid.UUID:
                    column.type = GUID()


@pytest.fixture(scope="session")
def test_engine():
    """Create an in-memory SQLite engine for testing."""
    # Ensure all models are registered by accessing their __table__ attribute
    # This forces SQLModel to register them in metadata
    # Do this before replacing JSONB to ensure tables are properly registered
    try:
        _ = User.__table__
        _ = Item.__table__
        _ = Activity.__table__
        _ = SourceConfig.__table__
        _ = ImageAnalysis.__table__
        _ = LLMPrompt.__table__
    except AttributeError:
        # If __table__ doesn't exist yet, models will be registered when create_all is called
        pass

    # Replace JSONB with JSON for SQLite compatibility
    replace_jsonb_with_json()

    # Use a temporary file-based database instead of in-memory
    # This ensures all connections share the same database
    db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    db_path = db_file.name
    db_file.close()

    sqlite_url = f"sqlite:///{db_path}"
    engine = create_engine(
        sqlite_url, echo=False, connect_args={"check_same_thread": False}
    )

    # Create all tables - this will register any models that weren't registered yet
    SQLModel.metadata.create_all(engine)

    # Verify critical tables exist
    with Session(engine) as session:
        from sqlalchemy import inspect

        inspector = inspect(engine)
        tables = inspector.get_table_names()
        if "user" not in tables:
            # Try to create tables again
            SQLModel.metadata.create_all(engine, checkfirst=True)
            tables = inspector.get_table_names()
            if "user" not in tables:
                raise RuntimeError(
                    f"User table not created. Available tables: {tables}. "
                    f"Metadata tables: {list(SQLModel.metadata.tables.keys())}"
                )

    try:
        yield engine
    finally:
        # Clean up
        SQLModel.metadata.drop_all(engine)
        engine.dispose()
        # Remove temporary database file
        try:
            Path(db_path).unlink(missing_ok=True)
        except Exception:
            pass


@pytest.fixture(scope="session", autouse=True)
def db(test_engine) -> Generator[Session, None, None]:
    """Create a database session for testing."""
    # Initialize database (create superuser, etc.)
    with Session(test_engine) as session:
        init_db(session)
        session.commit()

    # Create a new session for tests
    with Session(test_engine) as session:
        yield session


@pytest.fixture(scope="module")
def client(test_engine) -> Generator[TestClient, None, None]:
    """Create a test client with overridden database dependency."""
    # Ensure tables exist before creating client
    SQLModel.metadata.create_all(test_engine, checkfirst=True)

    def override_get_db() -> Generator[Session, None, None]:
        with Session(test_engine) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    # Clean up dependency override
    app.dependency_overrides.clear()


@pytest.fixture(scope="module")
def superuser_token_headers(client: TestClient) -> dict[str, str]:
    return get_superuser_token_headers(client)


@pytest.fixture(scope="module")
def normal_user_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    return authentication_token_from_email(
        client=client, email=settings.auth.email_test_user, db=db
    )
