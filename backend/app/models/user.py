"""User and Role models."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.customer import Customer


class Role(SQLModel, table=True):
    """Role model for user permissions."""

    __tablename__ = "roles"

    id: int | None = Field(default=None, primary_key=True)
    role_name: str = Field(max_length=32, unique=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    users: list["User"] = Relationship(back_populates="role")


class User(SQLModel, table=True):
    """User model matching DDL structure."""

    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    role_id: int = Field(foreign_key="roles.id", index=True)
    phone: str | None = Field(default=None, max_length=32)
    email: str | None = Field(default=None, max_length=255)
    password_hash: str | None = Field(default=None, max_length=255)
    status: str = Field(default="active", max_length=20)
    last_login_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: datetime | None = Field(default=None, nullable=True)

    # Relationships
    role: Role = Relationship(back_populates="users")
    # Only use owner_user_id for the relationship, specify foreign_keys explicitly
    customers: list["Customer"] = Relationship(
        back_populates="owner",
        sa_relationship_kwargs={"foreign_keys": "Customer.owner_user_id"}
    )

    @property
    def is_active(self) -> bool:
        return self.status == "active" and self.deleted_at is None

    @property
    def role_name(self) -> str:
        return self.role.role_name if self.role else ""


class UserCreate(SQLModel):
    """User creation schema."""

    name: str = Field(max_length=100)
    password: str = Field(min_length=6, max_length=100)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=32)
    role_id: int


class UserUpdate(SQLModel):
    """User update schema."""

    name: str | None = Field(default=None, max_length=100)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=32)
    status: str | None = Field(default=None, max_length=20)
    role_id: int | None = Field(default=None)


class UserRead(SQLModel):
    """User response schema."""

    id: int
    name: str
    email: str | None
    phone: str | None
    role_id: int
    role_name: str
    status: str
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None
