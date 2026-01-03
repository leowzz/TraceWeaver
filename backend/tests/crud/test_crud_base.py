"""
Comprehensive unit tests for CRUDBase with PostgreSQL support.

Run with: pytest test_crud_base.py -v
"""

import pytest
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import SQLModel, Session, Field, create_engine
from app.crud.base import CRUDBase
from pydantic import BaseModel


# Test Models
class HeroBase(SQLModel):
    name: str = Field(index=True)
    secret_name: str
    age: int | None = Field(default=None, index=True)


class Hero(HeroBase, table=True):
    id: int | None = Field(default=None, primary_key=True)


class HeroCreate(HeroBase):
    pass


class HeroUpdate(BaseModel):
    name: str | None = None
    secret_name: str | None = None
    age: int | None = None


# CRUD Instance
class CRUDHero(CRUDBase[Hero, HeroCreate, HeroUpdate]):
    pass


def replace_jsonb_with_json():
    """Replace JSONB columns with JSON for SQLite compatibility."""
    for table in SQLModel.metadata.tables.values():
        for column in table.columns:
            if isinstance(column.type, JSONB):
                column.type = JSON()


@pytest.fixture(scope="function")
def engine():
    """Create an in-memory SQLite database for testing."""
    # Replace JSONB with JSON for SQLite compatibility
    replace_jsonb_with_json()
    
    sqlite_url = "sqlite:///:memory:"
    engine = create_engine(sqlite_url, echo=False, connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def db(engine):
    """Create a new database session for a test."""
    with Session(engine) as session:
        yield session


@pytest.fixture(scope="function")
def hero_crud():
    """Create a CRUDHero instance."""
    return CRUDHero(Hero)


@pytest.fixture(scope="function")
def sample_hero(db, hero_crud):
    """Create a sample hero for testing."""
    hero_in = HeroCreate(name="Deadpond", secret_name="Dive Wilson", age=25)
    hero = hero_crud.create(db, hero_in)
    return hero


# Tests
class TestCreate:
    def test_create_with_schema(self, db, hero_crud):
        """Test creating a record with Pydantic schema."""
        hero_in = HeroCreate(name="Spider-Boy", secret_name="Pedro Parqueador", age=18)
        hero = hero_crud.create(db, hero_in)

        assert hero.id is not None
        assert hero.name == "Spider-Boy"
        assert hero.secret_name == "Pedro Parqueador"
        assert hero.age == 18

    def test_create_with_dict(self, db, hero_crud):
        """Test creating a record with dictionary."""
        hero_data = {"name": "Rusty-Man", "secret_name": "Tommy Sharp", "age": 48}
        hero = hero_crud.create(db, hero_data)

        assert hero.id is not None
        assert hero.name == "Rusty-Man"

    def test_create_many(self, db, hero_crud):
        """Test bulk creating records."""
        heroes_in = [
            HeroCreate(name="Hero1", secret_name="Secret1", age=20),
            HeroCreate(name="Hero2", secret_name="Secret2", age=30),
            {"name": "Hero3", "secret_name": "Secret3", "age": 40},
        ]
        count = hero_crud.create_many(db, heroes_in)

        assert count == 3
        all_heroes = hero_crud.get_all(db)
        assert len(all_heroes) == 3

    def test_create_many_empty_list(self, db, hero_crud):
        """Test create_many with empty list."""
        count = hero_crud.create_many(db, [])
        assert count == 0


class TestRead:
    def test_get_existing(self, db, hero_crud, sample_hero):
        """Test getting an existing record."""
        hero = hero_crud.get(db, sample_hero.id)
        assert hero is not None
        assert hero.id == sample_hero.id
        assert hero.name == sample_hero.name

    def test_get_non_existing(self, db, hero_crud):
        """Test getting a non-existing record."""
        hero = hero_crud.get(db, 99999)
        assert hero is None

    def test_get_by_ids(self, db, hero_crud):
        """Test getting multiple records by IDs."""
        hero1 = hero_crud.create(db, HeroCreate(name="Hero1", secret_name="S1"))
        hero2 = hero_crud.create(db, HeroCreate(name="Hero2", secret_name="S2"))
        hero3 = hero_crud.create(db, HeroCreate(name="Hero3", secret_name="S3"))

        heroes = hero_crud.get_by_ids(db, [hero1.id, hero3.id])
        assert len(heroes) == 2
        hero_ids = [h.id for h in heroes]
        assert hero1.id in hero_ids
        assert hero3.id in hero_ids

    def test_get_by_field(self, db, hero_crud, sample_hero):
        """Test getting a record by specific field."""
        hero = hero_crud.get_by_field(db, "name", "Deadpond")
        assert hero is not None
        assert hero.id == sample_hero.id

    def test_get_by_field_non_existing(self, db, hero_crud):
        """Test getting by field with non-existing value."""
        hero = hero_crud.get_by_field(db, "name", "NonExistent")
        assert hero is None

    def test_get_by_field_invalid_field(self, db, hero_crud):
        """Test getting by invalid field raises error."""
        with pytest.raises(ValueError, match="Field invalid_field not found"):
            hero_crud.get_by_field(db, "invalid_field", "value")

    def test_get_multi(self, db, hero_crud):
        """Test getting multiple records with pagination."""
        for i in range(5):
            hero_crud.create(
                db, HeroCreate(name=f"Hero{i}", secret_name=f"Secret{i}")
            )

        heroes = hero_crud.get_multi(db, skip=1, limit=2)
        assert len(heroes) == 2

    def test_get_multi_with_order(self, db, hero_crud):
        """Test getting multiple records with ordering."""
        hero_crud.create(db, HeroCreate(name="Charlie", secret_name="C", age=30))
        hero_crud.create(db, HeroCreate(name="Alice", secret_name="A", age=20))
        hero_crud.create(db, HeroCreate(name="Bob", secret_name="B", age=25))

        heroes = hero_crud.get_multi(db, order_by=Hero.name.asc())
        assert heroes[0].name == "Alice"
        assert heroes[1].name == "Bob"
        assert heroes[2].name == "Charlie"

    def test_get_all(self, db, hero_crud):
        """Test getting all records."""
        for i in range(3):
            hero_crud.create(
                db, HeroCreate(name=f"Hero{i}", secret_name=f"Secret{i}")
            )

        heroes = hero_crud.get_all(db)
        assert len(heroes) == 3

    def test_get_all_with_order(self, db, hero_crud):
        """Test getting all records with ordering."""
        hero_crud.create(db, HeroCreate(name="Z", secret_name="Z", age=30))
        hero_crud.create(db, HeroCreate(name="A", secret_name="A", age=20))

        heroes = hero_crud.get_all(db, order_by=Hero.age.desc())
        assert heroes[0].age == 30
        assert heroes[1].age == 20


class TestPagination:
    def test_limit_offset_page(self, db, hero_crud):
        """Test limit-offset pagination."""
        for i in range(10):
            hero_crud.create(
                db, HeroCreate(name=f"Hero{i}", secret_name=f"Secret{i}")
            )

        items, total = hero_crud.limit_offset_page(db, page=2, limit=3)
        assert total == 10
        assert len(items) == 3

    def test_limit_offset_page_with_skip(self, db, hero_crud):
        """Test limit-offset pagination with skip."""
        for i in range(10):
            hero_crud.create(
                db, HeroCreate(name=f"Hero{i}", secret_name=f"Secret{i}")
            )

        items, total = hero_crud.limit_offset_page(db, skip=1, page=2, limit=2)
        # offset = (2-1)*2 + 1 = 3
        assert total == 10
        assert len(items) == 2

    def test_has_more_page_true(self, db, hero_crud):
        """Test cursor pagination when there are more items."""
        for i in range(10):
            hero_crud.create(
                db, HeroCreate(name=f"Hero{i}", secret_name=f"Secret{i}")
            )

        items, has_more = hero_crud.has_more_page(db, limit=5)
        assert len(items) == 5
        assert has_more is True

    def test_has_more_page_false(self, db, hero_crud):
        """Test cursor pagination when there are no more items."""
        for i in range(3):
            hero_crud.create(
                db, HeroCreate(name=f"Hero{i}", secret_name=f"Secret{i}")
            )

        items, has_more = hero_crud.has_more_page(db, limit=5)
        assert len(items) == 3
        assert has_more is False

    def test_has_more_page_with_last_id(self, db, hero_crud):
        """Test cursor pagination with last_id."""
        heroes = []
        for i in range(10):
            hero = hero_crud.create(
                db, HeroCreate(name=f"Hero{i}", secret_name=f"Secret{i}")
            )
            heroes.append(hero)

        items, has_more = hero_crud.has_more_page(
            db, last_id=heroes[4].id, limit=3
        )
        assert len(items) == 3
        assert has_more is True
        # Should get items after ID 5
        assert all(item.id > heroes[4].id for item in items)


class TestUpdate:
    def test_update_with_schema(self, db, hero_crud, sample_hero):
        """Test updating a record with Pydantic schema."""
        hero_update = HeroUpdate(name="Updated Name", age=30)
        updated = hero_crud.update(db, sample_hero.id, hero_update)

        assert updated is not None
        assert updated.name == "Updated Name"
        assert updated.age == 30
        assert updated.secret_name == sample_hero.secret_name  # Unchanged

    def test_update_with_dict(self, db, hero_crud, sample_hero):
        """Test updating a record with dictionary."""
        updated = hero_crud.update(db, sample_hero.id, {"age": 35})

        assert updated is not None
        assert updated.age == 35
        assert updated.name == sample_hero.name  # Unchanged

    def test_update_non_existing(self, db, hero_crud):
        """Test updating a non-existing record."""
        result = hero_crud.update(db, 99999, HeroUpdate(name="Test"))
        assert result is None

    def test_update_exclude_unset(self, db, hero_crud, sample_hero):
        """Test that exclude_unset works correctly."""
        hero_update = HeroUpdate(name="New Name")  # Only name is set
        updated = hero_crud.update(db, sample_hero.id, hero_update)

        assert updated.name == "New Name"
        assert updated.secret_name == sample_hero.secret_name  # Should remain unchanged
        assert updated.age == sample_hero.age  # Should remain unchanged


class TestDelete:
    def test_delete_existing(self, db, hero_crud, sample_hero):
        """Test deleting an existing record."""
        deleted = hero_crud.delete(db, sample_hero.id)

        assert deleted is not None
        assert deleted.id == sample_hero.id

        # Verify it's actually deleted
        hero = hero_crud.get(db, sample_hero.id)
        assert hero is None

    def test_delete_non_existing(self, db, hero_crud):
        """Test deleting a non-existing record."""
        deleted = hero_crud.delete(db, 99999)
        assert deleted is None

    def test_delete_many(self, db, hero_crud):
        """Test bulk deleting records."""
        hero1 = hero_crud.create(db, HeroCreate(name="Hero1", secret_name="S1"))
        hero2 = hero_crud.create(db, HeroCreate(name="Hero2", secret_name="S2"))
        hero3 = hero_crud.create(db, HeroCreate(name="Hero3", secret_name="S3"))

        count = hero_crud.delete_many(db, [hero1.id, hero3.id])
        assert count == 2

        # Verify deletions
        assert hero_crud.get(db, hero1.id) is None
        assert hero_crud.get(db, hero2.id) is not None
        assert hero_crud.get(db, hero3.id) is None

    def test_delete_many_empty_list(self, db, hero_crud):
        """Test delete_many with empty list."""
        count = hero_crud.delete_many(db, [])
        assert count == 0


class TestUtility:
    def test_count(self, db, hero_crud):
        """Test counting records."""
        assert hero_crud.count(db) == 0

        for i in range(5):
            hero_crud.create(
                db, HeroCreate(name=f"Hero{i}", secret_name=f"Secret{i}")
            )

        assert hero_crud.count(db) == 5

    def test_exists_true(self, db, hero_crud, sample_hero):
        """Test exists returns True for existing record."""
        assert hero_crud.exists(db, sample_hero.id) is True

    def test_exists_false(self, db, hero_crud):
        """Test exists returns False for non-existing record."""
        assert hero_crud.exists(db, 99999) is False
