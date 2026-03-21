"""Pipeline event model for timeline aggregation."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional, Any

from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.customer import Customer


class PipelineEvent(SQLModel, table=True):
    """Pipeline event model for customer timeline."""

    __tablename__ = "pipeline_events"

    id: int | None = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customers.id", index=True)
    event_type: str = Field(max_length=30)
    event_time: datetime
    title: str = Field(max_length=200)
    description: str | None = Field(default=None)
    operator_id: int | None = Field(default=None, foreign_key="users.id")
    reference_id: int | None = Field(default=None)
    extra_data: dict | None = Field(default=None, sa_column=Column(JSONB))
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    customer: "Customer" = Relationship()
    operator: Optional["User"] = Relationship()
