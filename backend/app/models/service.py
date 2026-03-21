"""Service record and reminder models."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.customer import Customer


class ReminderType(str, Enum):
    """Reminder type enum."""
    FOLLOWUP = "followup"
    RENEWAL = "renewal"
    PROGRESS_CHECK = "progress_check"
    OTHER = "other"


class ReminderPriority(str, Enum):
    """Reminder priority enum."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ReminderStatus(str, Enum):
    """Reminder status enum."""
    PENDING = "pending"
    DONE = "done"
    CANCELED = "canceled"


class ServiceRecord(SQLModel, table=True):
    """Service record model."""

    __tablename__ = "service_records"

    id: int | None = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customers.id", index=True)
    service_type: str = Field(max_length=50)
    service_content: str | None = Field(default=None)
    service_time: datetime = Field(default_factory=datetime.utcnow)
    consultant_id: int = Field(foreign_key="users.id", index=True)
    satisfaction_score: int | None = Field(default=None, ge=1, le=5)
    notes: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    customer: "Customer" = Relationship()
    consultant: "User" = Relationship()


class ServiceReminder(SQLModel, table=True):
    """Service reminder model."""

    __tablename__ = "service_reminders"

    id: int | None = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customers.id", index=True)
    created_by: int = Field(foreign_key="users.id")
    assignee_user_id: int = Field(foreign_key="users.id", index=True)
    reminder_type: str = Field(max_length=30)
    reminder_time: datetime
    priority: str = Field(default="medium", max_length=10)
    status: str = Field(default="pending", max_length=20)
    content: str | None = Field(default=None)
    done_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: datetime | None = Field(default=None)

    # Relationships
    customer: "Customer" = Relationship()
    creator: "User" = Relationship(sa_relationship_kwargs={"foreign_keys": "[ServiceReminder.created_by]"})
    assignee: "User" = Relationship(sa_relationship_kwargs={"foreign_keys": "[ServiceReminder.assignee_user_id]"})


class ServiceRecordCreate(SQLModel):
    """Service record creation schema."""

    customer_id: int
    service_type: str
    service_content: str | None = None
    service_time: datetime
    satisfaction_score: int | None = None
    notes: str | None = None


class ServiceReminderCreate(SQLModel):
    """Service reminder creation schema."""

    customer_id: int
    assignee_user_id: int
    reminder_type: str
    reminder_time: datetime
    priority: str = "medium"
    content: str | None = None


class ServiceReminderUpdate(SQLModel):
    """Service reminder update schema."""

    assignee_user_id: int | None = None
    reminder_type: str | None = None
    reminder_time: datetime | None = None
    priority: str | None = None
    status: str | None = None
    content: str | None = None
