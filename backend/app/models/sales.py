"""Sales followup and opportunity models."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.customer import Customer


class ContactMethod(str, Enum):
    """Contact method enum."""
    PHONE = "phone"
    WECHAT = "wechat"
    VISIT = "visit"
    EMAIL = "email"
    OTHER = "other"


class FollowupResult(str, Enum):
    """Followup result enum."""
    NO_ANSWER = "no_answer"
    CONTACTED = "contacted"
    INTERESTED = "interested"
    REJECTED = "rejected"
    PENDING = "pending"


class OpportunityStage(str, Enum):
    """Opportunity stage enum."""
    NEW = "new"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"


class SalesFollowup(SQLModel, table=True):
    """Sales followup model."""

    __tablename__ = "sales_followups"

    id: int | None = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customers.id", index=True)
    sales_id: int = Field(foreign_key="users.id", index=True)
    followup_time: datetime = Field(default_factory=datetime.utcnow)
    contact_method: str = Field(max_length=20)
    content: str | None = Field(default=None)
    result: str | None = Field(default=None, max_length=20)
    next_action_time: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    customer: "Customer" = Relationship()
    sales: "User" = Relationship()


class SalesOpportunity(SQLModel, table=True):
    """Sales opportunity model."""

    __tablename__ = "sales_opportunities"

    id: int | None = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customers.id", index=True)
    opportunity_name: str = Field(max_length=200)
    expected_amount: float = Field(default=0)
    probability: int = Field(default=0, ge=0, le=100)
    stage: str = Field(default="new", max_length=20)
    expected_close_date: datetime | None = Field(default=None)
    owner_user_id: int = Field(foreign_key="users.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    customer: "Customer" = Relationship()
    owner: "User" = Relationship()


class SalesFollowupCreate(SQLModel):
    """Sales followup creation schema."""

    customer_id: int
    followup_time: datetime
    contact_method: str
    content: str | None = None
    result: str | None = None
    next_action_time: datetime | None = None


class SalesOpportunityCreate(SQLModel):
    """Sales opportunity creation schema."""

    customer_id: int
    opportunity_name: str
    expected_amount: float | None = None
    probability: int | None = None
    stage: str = "new"
    expected_close_date: datetime | None = None


class SalesOpportunityUpdate(SQLModel):
    """Sales opportunity update schema."""

    opportunity_name: str | None = None
    expected_amount: float | None = None
    probability: int | None = None
    stage: str | None = None
    expected_close_date: datetime | None = None
