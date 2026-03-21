"""Roles API endpoints."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_session
from app.core.permissions import is_admin_or_above
from app.core.exceptions import ForbiddenException
from app.models.user import Role

router = APIRouter()


class RoleResponseModel(BaseModel):
    id: int
    role_name: str
    created_at: str

    class Config:
        from_attributes = True


@router.get("", response_model=list[RoleResponseModel])
async def list_roles(
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """
    List all roles.
    Requires admin or above role.
    """
    if not is_admin_or_above(current_user.role_name):
        raise ForbiddenException("Admin access required")

    stmt = select(Role).order_by(Role.id)
    result = await session.execute(stmt)
    roles = result.scalars().all()

    return [
        RoleResponseModel(
            id=role.id,
            role_name=role.role_name,
            created_at=role.created_at.isoformat()
        )
        for role in roles
    ]
