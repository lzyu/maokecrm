"""Audit log and consultation analysis models."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional, Any

from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy import Column, JSON

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.customer import Customer


class AuditLog(SQLModel, table=True):
    """Audit log model."""

    __tablename__ = "audit_logs"

    id: int | None = Field(default=None, primary_key=True)
    actor_user_id: int | None = Field(default=None, foreign_key="users.id", index=True)
    action: str = Field(max_length=50)
    resource_type: str = Field(max_length=50)
    resource_id: int | None = Field(default=None)
    before_data: dict | None = Field(default=None, sa_column=Column(JSON))
    after_data: dict | None = Field(default=None, sa_column=Column(JSON))
    ip_address: str | None = Field(default=None, max_length=45)
    user_agent: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    actor: Optional["User"] = Relationship()


class ConsultationAnalysis(SQLModel, table=True):
    """Consultation analysis model."""

    __tablename__ = "consultation_analysis"

    id: int | None = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customers.id", index=True)
    file_name: str | None = Field(default=None, max_length=255)
    file_path: str | None = Field(default=None)
    analysis_type: str = Field(max_length=50)
    analysis_result: str | None = Field(default=None)
    created_by: int = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: datetime | None = Field(default=None)

    # Relationships
    customer: "Customer" = Relationship()
    creator: "User" = Relationship()
