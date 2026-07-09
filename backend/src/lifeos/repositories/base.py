"""Generic CRUD repository.

Repositories never commit; they ``flush`` so generated ids are available while
leaving transaction boundaries to the caller (``session_scope``). This keeps
multi-step operations atomic.
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlmodel import Session, SQLModel, select

from lifeos.models.base import utcnow

ModelT = TypeVar("ModelT", bound=SQLModel)


class BaseRepository(Generic[ModelT]):
    """CRUD operations shared by every entity repository."""

    model: type[ModelT]

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, obj: ModelT) -> ModelT:
        self.session.add(obj)
        self.session.flush()
        self.session.refresh(obj)
        return obj

    def get(self, obj_id: int) -> ModelT | None:
        return self.session.get(self.model, obj_id)

    def list(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        order_by: str = "id",
        **filters: Any,
    ) -> list[ModelT]:
        statement = select(self.model)
        for field, value in filters.items():
            if value is not None:
                statement = statement.where(getattr(self.model, field) == value)
        statement = statement.order_by(getattr(self.model, order_by))
        statement = statement.offset(offset).limit(limit)
        return list(self.session.exec(statement).all())

    def update(self, obj_id: int, data: SQLModel | dict[str, Any]) -> ModelT | None:
        obj = self.get(obj_id)
        if obj is None:
            return None
        changes = self._as_changes(data)
        for field, value in changes.items():
            setattr(obj, field, value)
        obj.updated_at = utcnow()  # type: ignore[attr-defined]
        self.session.add(obj)
        self.session.flush()
        self.session.refresh(obj)
        return obj

    def delete(self, obj_id: int) -> bool:
        obj = self.get(obj_id)
        if obj is None:
            return False
        self.session.delete(obj)
        self.session.flush()
        return True

    def count(self, **filters: Any) -> int:
        statement = select(self.model)
        for field, value in filters.items():
            if value is not None:
                statement = statement.where(getattr(self.model, field) == value)
        return len(list(self.session.exec(statement).all()))

    @staticmethod
    def _as_changes(data: SQLModel | dict[str, Any]) -> dict[str, Any]:
        """Normalize an update payload to a dict of set fields only."""
        if isinstance(data, SQLModel):
            return data.model_dump(exclude_unset=True)
        return {k: v for k, v in data.items() if v is not None}
