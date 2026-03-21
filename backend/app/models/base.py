"""Base model with common fields."""

from datetime import datetime
from typing import Annotated

from sqlmodel import Field, SQLModel
from sqlmodel import Field as SQLField


class BaseModel(SQLModel):
    """Base model with common timestamp fields."""

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SoftDeleteMixin:
    """Mixin for soft delete functionality."""

    deleted_at: datetime | None = Field(default=None, nullable=True)

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
