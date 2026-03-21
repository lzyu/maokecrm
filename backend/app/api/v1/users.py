"""Users API endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_session
from app.core.exceptions import ConflictException, ForbiddenException, NotFoundException
from app.core.permissions import RoleName, is_admin_or_above
from app.core.security import get_password_hash
from app.models.user import Role, User, UserRead

router = APIRouter()


class UserListResponse(BaseModel):
    items: list[UserRead]
    total: int
    page: int
    page_size: int


class UserCreateRequest(BaseModel):
    name: str
    password: str
    email: str | None = None
    phone: str | None = None
    role_id: int


class UserUpdateRequest(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    status: str | None = None
    role_id: int | None = None


@router.get("", response_model=UserListResponse)
async def list_users(
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str | None = Query(None),
    role_id: int | None = Query(None),
    status: str | None = Query(None),
):
    """
    List users with pagination and filtering.
    Requires admin or above role.
    """
    if not is_admin_or_above(current_user.role_name):
        raise ForbiddenException("Admin access required")

    # Build query
    stmt = select(User).where(User.deleted_at.is_(None))

    if keyword:
        stmt = stmt.where(
            or_(
                User.name.ilike(f"%{keyword}%"),
                User.email.ilike(f"%{keyword}%"),
                User.phone.ilike(f"%{keyword}%"),
            )
        )

    if role_id:
        stmt = stmt.where(User.role_id == role_id)

    if status:
        stmt = stmt.where(User.status == status)

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await session.execute(count_stmt)
    total = total_result.scalar()

    # Paginate
    offset = (page - 1) * page_size
    stmt = stmt.order_by(User.created_at.desc()).offset(offset).limit(page_size)

    result = await session.execute(stmt)
    users = result.scalars().all()

    # Build response with role info
    user_reads = []
    for user in users:
        role_stmt = select(Role).where(Role.id == user.role_id)
        role_result = await session.execute(role_stmt)
        role = role_result.scalar_one_or_none()

        user_reads.append(
            UserRead(
                id=user.id,
                name=user.name,
                email=user.email,
                phone=user.phone,
                role_id=user.role_id,
                role_name=role.role_name if role else "",
                status=user.status,
                created_at=user.created_at,
                updated_at=user.updated_at,
                last_login_at=user.last_login_at,
            )
        )

    return UserListResponse(
        items=user_reads,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: UserCreateRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """
    Create a new user.
    Requires admin or above role.
    """
    if not is_admin_or_above(current_user.role_name):
        raise ForbiddenException("Admin access required")

    # Check if phone or email exists
    if request.phone:
        existing_stmt = select(User).where(User.phone == request.phone, User.deleted_at.is_(None))
        existing_result = await session.execute(existing_stmt)
        if existing_result.scalar_one_or_none():
            raise ConflictException("Phone number already exists")

    if request.email:
        existing_stmt = select(User).where(User.email == request.email, User.deleted_at.is_(None))
        existing_result = await session.execute(existing_stmt)
        if existing_result.scalar_one_or_none():
            raise ConflictException("Email already exists")

    # Verify role exists
    role_stmt = select(Role).where(Role.id == request.role_id)
    role_result = await session.execute(role_stmt)
    role = role_result.scalar_one_or_none()
    if not role:
        raise NotFoundException("Role not found")

    # Create user
    user = User(
        name=request.name,
        password_hash=get_password_hash(request.password),
        email=request.email,
        phone=request.phone,
        role_id=request.role_id,
        status="active",
    )

    session.add(user)
    await session.commit()
    await session.refresh(user)

    return UserRead(
        id=user.id,
        name=user.name,
        email=user.email,
        phone=user.phone,
        role_id=user.role_id,
        role_name=role.role_name,
        status=user.status,
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login_at=user.last_login_at,
    )


@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: int,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """
    Get user by ID.
    Requires admin or above role.
    """
    if not is_admin_or_above(current_user.role_name):
        raise ForbiddenException("Admin access required")

    stmt = select(User).where(User.id == user_id, User.deleted_at.is_(None))
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise NotFoundException("User not found")

    # Load role
    role_stmt = select(Role).where(Role.id == user.role_id)
    role_result = await session.execute(role_stmt)
    role = role_result.scalar_one_or_none()

    return UserRead(
        id=user.id,
        name=user.name,
        email=user.email,
        phone=user.phone,
        role_id=user.role_id,
        role_name=role.role_name if role else "",
        status=user.status,
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login_at=user.last_login_at,
    )


@router.put("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: int,
    request: UserUpdateRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """
    Update user by ID.
    Requires admin or above role.
    """
    if not is_admin_or_above(current_user.role_name):
        raise ForbiddenException("Admin access required")

    stmt = select(User).where(User.id == user_id, User.deleted_at.is_(None))
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise NotFoundException("User not found")

    # Update fields
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    user.updated_at = datetime.utcnow()
    session.add(user)
    await session.commit()
    await session.refresh(user)

    # Load role
    role_stmt = select(Role).where(Role.id == user.role_id)
    role_result = await session.execute(role_stmt)
    role = role_result.scalar_one_or_none()

    return UserRead(
        id=user.id,
        name=user.name,
        email=user.email,
        phone=user.phone,
        role_id=user.role_id,
        role_name=role.role_name if role else "",
        status=user.status,
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login_at=user.last_login_at,
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """
    Soft delete user by ID.
    Only super_admin can delete users.
    """
    if current_user.role_name != RoleName.SUPER_ADMIN.value:
        raise ForbiddenException("Only super admin can delete users")

    # Cannot delete self
    if current_user.id == user_id:
        raise ForbiddenException("Cannot delete your own account")

    stmt = select(User).where(User.id == user_id, User.deleted_at.is_(None))
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise NotFoundException("User not found")

    # Soft delete
    user.deleted_at = datetime.utcnow()
    session.add(user)
    await session.commit()
