from typing import Any, Generic, TypeVar, Union, Sequence

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlmodel import Session, SQLModel, col, delete, func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

ModelType = TypeVar("ModelType", bound=SQLModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).
        """
        self.model = model

    def get(self, session: Session, id: Any) -> ModelType | None:
        return session.get(self.model, id)
    
    def get_by_ids(self, session: Session, ids: Sequence[Any]) -> list[ModelType]:
        statement = select(self.model).where(col(self.model.id).in_(ids))
        return list(session.exec(statement).all())

    def get_by_field(
        self, session: Session, field: str, value: Any
    ) -> ModelType | None:
        column = getattr(self.model, field, None)
        if column is None:
             raise ValueError(f"Field {field} not found in model {self.model.__tablename__}")
        statement = select(self.model).where(column == value)
        return session.exec(statement).first()

    def get_multi(
        self, session: Session, *, skip: int = 0, limit: int = 100, order_by: Any = None
    ) -> list[ModelType]:
        statement = select(self.model)
        if order_by is not None:
            statement = statement.order_by(order_by)
        statement = statement.offset(skip).limit(limit)
        return list(session.exec(statement).all())

    def get_all(
        self, session: Session, *, order_by: Any = None
    ) -> list[ModelType]:
        statement = select(self.model)
        if order_by is not None:
            statement = statement.order_by(order_by)
        return list(session.exec(statement).all())

    def limit_offset_page(
        self, session: Session, *, skip: int = 0, page: int = 1, limit: int = 20, order_by: Any = None
    ) -> tuple[list[ModelType], int]:
        statement = select(self.model)
        count_stmt = select(func.count()).select_from(self.model)
        
        if order_by is not None:
            statement = statement.order_by(order_by)
            
        offset = (page - 1) * limit + skip
        statement = statement.offset(offset).limit(limit)
        
        total = session.exec(count_stmt).one()
        items = list(session.exec(statement).all())
        return items, total

    def has_more_page(
        self, session: Session, *, last_id: Any = None, page: int = 1, limit: int = 20, order_by: Any = None
    ) -> tuple[list[ModelType], bool]:
        statement = select(self.model)
        
        if last_id is not None:
            # Assuming 'id' is the primary key and we want > last_id
            # This logic might need adjustment based on specific model PK or order
             statement = statement.where(col(self.model.id) > last_id)
        elif page > 1:
            statement = statement.offset((page - 1) * limit)

        if order_by is not None:
            statement = statement.order_by(order_by)
        else:
             statement = statement.order_by(col(self.model.id).asc())
        
        # Fetch limit + 1
        statement = statement.limit(limit + 1)
        items = list(session.exec(statement).all())
        
        has_more = False
        if len(items) > limit:
            has_more = True
            items = items[:limit]
            
        return items, has_more

    def count(self, session: Session) -> int:
        statement = select(func.count()).select_from(self.model)
        return session.exec(statement).one()

    def exists(self, session: Session, id: Any) -> bool:
        statement = select(func.count()).select_from(self.model).where(col(self.model.id) == id)
        count = session.exec(statement).one()
        return count > 0

    def create(self, session: Session, obj_in: CreateSchemaType | dict[str, Any]) -> ModelType:
        if isinstance(obj_in, dict):
            create_data = obj_in
        else:
            create_data = obj_in.model_dump()
            
        db_obj = self.model(**create_data)
        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
        return db_obj

    def create_many(
        self, session: Session, objs_in: list[CreateSchemaType | dict[str, Any]]
    ) -> int:
        if not objs_in:
            return 0
            
        data_list = []
        for obj in objs_in:
            if isinstance(obj, dict):
                data_list.append(obj)
            else:
                 data_list.append(obj.model_dump())
        
        # Using SQLAlchemy Core for bulk insert which is faster
        stmt = pg_insert(self.model).values(data_list)
        result = session.exec(stmt)
        session.commit()
        return result.rowcount

    def upsert(
        self,
        session: Session,
        obj_in: CreateSchemaType | dict[str, Any],
        *,
        update_fields: list[str] | None = None,
    ) -> int:
        if isinstance(obj_in, dict):
            data = obj_in
        else:
            data = obj_in.model_dump()
            
        insert_stmt = pg_insert(self.model).values(**data)
        
        if update_fields:
            update_dict = {field: insert_stmt.excluded[field] for field in update_fields if field in data}
        else:
            # Update all except PK (assuming 'id')
            update_dict = {
                k: insert_stmt.excluded[k]
                for k in data.keys()
                if k != 'id'
            }
            
        if update_dict:
            # PostgreSQL uses ON CONFLICT ... DO UPDATE
            stmt = insert_stmt.on_conflict_do_update(
                index_elements=['id'],  # Primary key constraint
                set_=update_dict
            )
        else:
            stmt = insert_stmt
            
        result = session.exec(stmt)
        session.commit()
        return result.rowcount

    def update(
        self,
        session: Session,
        # id: Any, # Removed ID from signature to match typical SQLModel update(db_obj, obj_in) pattern?
        # WAIT, user request specifically has `update(self, id, obj_in)`. I should respect that.
        id: Any, 
        obj_in: UpdateSchemaType | dict[str, Any],
    ) -> ModelType | None:
        db_obj = session.get(self.model, id)
        if not db_obj:
            return None
            
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
            
        for key, value in update_data.items():
            setattr(db_obj, key, value)
            
        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
        return db_obj

    def delete(self, session: Session, id: Any) -> ModelType | None:
        db_obj = session.get(self.model, id)
        if db_obj:
            session.delete(db_obj)
            session.commit()
        return db_obj

    def delete_many(self, session: Session, ids: list[Any]) -> int:
        statement = delete(self.model).where(col(self.model.id).in_(ids))
        result = session.exec(statement)
        session.commit()
        return result.rowcount
