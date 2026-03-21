"""Import batch and error models."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional, Any

from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy import Column, JSON
from sqlalchemy.dialects.postgresql import JSONB

if TYPE_CHECKING:
    from app.models.user import User


class ImportType(str, Enum):
    """Import type enum."""
    COURSE_PURCHASE = "course_purchase"
    COURSE_ATTENDANCE = "course_attendance"


class ImportStatus(str, Enum):
    """Import status enum."""
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL_SUCCESS = "partial_success"


class ImportBatch(SQLModel, table=True):
    """Import batch model."""

    __tablename__ = "import_batches"

    id: int | None = Field(default=None, primary_key=True)
    batch_no: str = Field(max_length=64, unique=True)
    import_type: str = Field(max_length=30)
    file_name: str = Field(max_length=255)
    file_url: str | None = Field(default=None)
    status: str = Field(default="processing", max_length=20)
    total_rows: int = Field(default=0)
    success_rows: int = Field(default=0)
    failed_rows: int = Field(default=0)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: datetime | None = Field(default=None)
    created_by: int = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    creator: "User" = Relationship()


class ImportError(SQLModel, table=True):
    """Import error model."""

    __tablename__ = "import_errors"

    id: int | None = Field(default=None, primary_key=True)
    batch_id: int = Field(foreign_key="import_batches.id", index=True)
    row_no: int
    error_code: str = Field(max_length=50)
    error_message: str
    row_data: dict | None = Field(default=None, sa_column=Column(JSONB))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CoursePurchaseRecord(SQLModel, table=True):
    """Course purchase record model."""

    __tablename__ = "course_purchase_records"

    id: int | None = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customers.id", index=True)
    course_name: str = Field(max_length=255)
    purchase_date: datetime
    amount: float = Field(default=0)
    currency: str = Field(default="CNY", max_length=10)
    import_batch_id: int | None = Field(default=None, foreign_key="import_batches.id")
    import_source: str = Field(default="manual", max_length=30)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: datetime | None = Field(default=None)


class CourseAttendanceRecord(SQLModel, table=True):
    """Course attendance record model."""

    __tablename__ = "course_attendance_records"

    id: int | None = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customers.id", index=True)
    course_name: str = Field(max_length=255)
    class_date: datetime
    status: str = Field(max_length=20)  # attended, absent, leave
    import_batch_id: int | None = Field(default=None, foreign_key="import_batches.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: datetime | None = Field(default=None)
