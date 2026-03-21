"""Authentication API endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_session
from app.core.exceptions import UnauthorizedException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.models.user import Role, User

router = APIRouter()


class LoginRequestModel(BaseModel):
    username: str  # Can be phone or email
    password: str


class LoginResponseModel(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


class RefreshTokenRequestModel(BaseModel):
    refresh_token: str


class RefreshTokenResponseModel(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CurrentUserResponseModel(BaseModel):
    id: int
    name: str
    email: str | None
    phone: str | None
    role_id: int
    role_name: str
    status: str

    class Config:
        from_attributes = True


@router.post("/login", response_model=LoginResponseModel)
async def login(
    request: LoginRequestModel,
    session: AsyncSession = Depends(get_session),
):
    """
    User login endpoint.
    Returns JWT access token and refresh token.
    """
    # Find user by phone or email
    stmt = select(User).where(
        or_(User.phone == request.username, User.email == request.username),
        User.deleted_at.is_(None),
    )
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise UnauthorizedException("Invalid username or password")

    if not user.password_hash or not verify_password(request.password, user.password_hash):
        raise UnauthorizedException("Invalid username or password")

    if user.status != "active":
        raise UnauthorizedException("User account is disabled")

    # Update last login time
    user.last_login_at = datetime.utcnow()
    session.add(user)
    await session.commit()

    # Load role
    role_stmt = select(Role).where(Role.id == user.role_id)
    role_result = await session.execute(role_stmt)
    role = role_result.scalar_one()

    # Generate tokens
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)

    return LoginResponseModel(
        access_token=access_token,
        refresh_token=refresh_token,
        user={
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
            "role_id": user.role_id,
            "role_name": role.role_name,
            "status": user.status,
        },
    )


@router.post("/refresh", response_model=RefreshTokenResponseModel)
async def refresh_token(
    request: RefreshTokenRequestModel,
    session: AsyncSession = Depends(get_session),
):
    """
    Refresh access token using refresh token.
    """
    payload = decode_token(request.refresh_token)

    if payload is None:
        raise UnauthorizedException("Invalid or expired refresh token")

    if payload.get("type") != "refresh":
        raise UnauthorizedException("Invalid token type")

    user_id = payload.get("sub")
    if user_id is None:
        raise UnauthorizedException("Invalid token payload")

    # Verify user exists and is active
    stmt = select(User).where(User.id == int(user_id), User.deleted_at.is_(None))
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None or user.status != "active":
        raise UnauthorizedException("User not found or inactive")

    # Generate new access token
    access_token = create_access_token(subject=user.id)

    return RefreshTokenResponseModel(access_token=access_token)


@router.post("/logout")
async def logout(current_user: CurrentUser):
    """
    User logout endpoint.
    In a stateless JWT system, this is mainly for client-side token removal.
    """
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=CurrentUserResponseModel)
async def get_current_user_info(current_user: CurrentUser):
    """
    Get current authenticated user information.
    """
    return CurrentUserResponseModel(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        phone=current_user.phone,
        role_id=current_user.role_id,
        role_name=current_user.role_name,
        status=current_user.status,
    )
