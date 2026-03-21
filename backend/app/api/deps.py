"""API dependencies for authentication and database sessions."""

from typing import Annotated

from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select as sqlmodel_select

from app.core.exceptions import UnauthorizedException
from app.core.security import decode_token
from app.database import get_session
from app.models.user import User

# Bearer token security scheme
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    """
    Dependency that extracts and validates the current user from JWT token.
    """
    if credentials is None:
        raise UnauthorizedException("Not authenticated")

    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        raise UnauthorizedException("Invalid or expired token")

    if payload.get("type") != "access":
        raise UnauthorizedException("Invalid token type")

    user_id = payload.get("sub")
    if user_id is None:
        raise UnauthorizedException("Invalid token payload")

    # Fetch user with role using eager load
    from sqlalchemy.orm import selectinload
    stmt = (
        select(User)
        .options(selectinload(User.role))
        .where(User.id == int(user_id), User.deleted_at.is_(None))
    )
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise UnauthorizedException("User not found")

    if not user.is_active:
        raise UnauthorizedException("User is inactive")

    return user


# Type alias for current user dependency
CurrentUser = Annotated[User, Depends(get_current_user)]
