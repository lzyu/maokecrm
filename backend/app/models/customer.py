"""Customer and Tag models."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.user import User


class CustomerStatus(str, Enum):
    """Customer status enum."""

    POTENTIAL = "potential"
    INTERESTED = "interested"
    CONVERTED = "converted"
    LOST = "lost"


class TagType(str, Enum):
    """Tag type enum."""

    SALES = "sales"
    CONSULTANT = "consultant"


class Tag(SQLModel, table=True):
    """Customer tag model."""

    __tablename__ = "tags"

    id: int | None = Field(default=None, primary_key=True)
    tag_name: str = Field(max_length=100)
    tag_type: str = Field(max_length=20)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    customer_links: list["CustomerTag"] = Relationship(back_populates="tag")


class CustomerTag(SQLModel, table=True):
    """Customer-Tag relationship model."""

    __tablename__ = "customer_tags"

    id: int | None = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customers.id", index=True)
    tag_id: int = Field(foreign_key="tags.id", index=True)
    created_by: int | None = Field(default=None, foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    customer: "Customer" = Relationship(back_populates="tag_links")
    tag: Tag = Relationship(back_populates="customer_links")


class Customer(SQLModel, table=True):
    """Customer model matching DDL structure."""

    __tablename__ = "customers"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    phone: str | None = Field(default=None, max_length=32)
    wechat: str | None = Field(default=None, max_length=64)
    company_name: str | None = Field(default=None, max_length=255)
    industry: str | None = Field(default=None, max_length=100)
    source_channel: str | None = Field(default=None, max_length=100)
    owner_user_id: int = Field(foreign_key="users.id", index=True)
    customer_status: str = Field(default="potential", max_length=20)
    last_followup_at: datetime | None = Field(default=None)
    next_followup_at: datetime | None = Field(default=None)
    created_by: int | None = Field(default=None, foreign_key="users.id")
    updated_by: int | None = Field(default=None, foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: datetime | None = Field(default=None, nullable=True)

    # Relationships - specify foreign_keys to avoid ambiguity
    owner: "User" = Relationship(
        back_populates="customers",
        sa_relationship_kwargs={"foreign_keys": "[Customer.owner_user_id]"}
    )
    tag_links: list[CustomerTag] = Relationship(back_populates="customer")

    @property
    def tags(self) -> list[Tag]:
        return [link.tag for link in self.tag_links]


class CustomerCreate(SQLModel):
    """Customer creation schema."""

    name: str = Field(max_length=100)
    phone: str | None = Field(default=None, max_length=32)
    wechat: str | None = Field(default=None, max_length=64)
    company_name: str | None = Field(default=None, max_length=255)
    industry: str | None = Field(default=None, max_length=100)
    source_channel: str | None = Field(default=None, max_length=100)
    customer_status: str = Field(default="potential")
    owner_user_id: int | None = Field(default=None)
    tag_ids: list[int] = Field(default_factory=list)


class CustomerUpdate(SQLModel):
    """Customer update schema."""

    name: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=32)
    wechat: str | None = Field(default=None, max_length=64)
    company_name: str | None = Field(default=None, max_length=255)
    industry: str | None = Field(default=None, max_length=100)
    source_channel: str | None = Field(default=None, max_length=100)
    customer_status: str | None = Field(default=None)
    owner_user_id: int | None = Field(default=None)
    tag_ids: list[int] | None = Field(default=None)


class CustomerRead(SQLModel):
    """Customer response schema."""

    id: int
    name: str
    phone: str | None
    wechat: str | None
    company_name: str | None
    industry: str | None
    source_channel: str | None
    customer_status: str
    owner_user_id: int
    owner_name: str | None = None
    created_at: datetime
    updated_at: datetime
    last_followup_at: datetime | None
    tags: list[dict] = Field(default_factory=list)


class TagCreate(SQLModel):
    """Tag creation schema."""

    tag_name: str = Field(max_length=100)
    tag_type: str = Field(max_length=20)


class TagUpdate(SQLModel):
    """Tag update schema."""

    tag_name: str | None = Field(default=None, max_length=100)
    tag_type: str | None = Field(default=None, max_length=20)


class TagRead(SQLModel):
    """Tag response schema."""

    id: int
    tag_name: str
    tag_type: str
    created_at: datetime
