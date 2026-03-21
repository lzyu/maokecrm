"""Permission checking utilities."""

from enum import Enum
from typing import Annotated

from fastapi import Depends

from app.api.deps import CurrentUser
from app.core.exceptions import ForbiddenException


class RoleName(str, Enum):
    """User role names."""

    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    SALES = "sales"
    CONSULTANT = "consultant"


# Permission levels (higher number = more permissions)
ROLE_LEVELS: dict[RoleName, int] = {
    RoleName.CONSULTANT: 1,
    RoleName.SALES: 2,
    RoleName.ADMIN: 3,
    RoleName.SUPER_ADMIN: 4,
}


def require_roles(*allowed_roles: RoleName):
    """Dependency that checks if current user has one of the allowed roles."""

    async def role_checker(current_user: CurrentUser) -> CurrentUser:
        user_role = RoleName(current_user.role_name)
        if user_role not in allowed_roles:
            raise ForbiddenException(
                f"Role '{user_role.value}' is not authorized for this action"
            )
        return current_user

    return Depends(role_checker)


def require_min_role(min_role: RoleName):
    """Dependency that checks if current user has at least the minimum role level."""

    async def role_checker(current_user: CurrentUser) -> CurrentUser:
        user_role = RoleName(current_user.role_name)
        min_level = ROLE_LEVELS[min_role]
        user_level = ROLE_LEVELS[user_role]

        if user_level < min_level:
            raise ForbiddenException(
                f"Role '{user_role.value}' does not meet minimum required role '{min_role.value}'"
            )
        return current_user

    return Depends(role_checker)


# Type aliases for common permission requirements
SuperAdminOnly = Annotated[CurrentUser, require_roles(RoleName.SUPER_ADMIN)]
AdminOrAbove = Annotated[CurrentUser, require_min_role(RoleName.ADMIN)]
SalesOrAbove = Annotated[CurrentUser, require_min_role(RoleName.SALES)]
AnyAuthenticatedUser = CurrentUser


def is_admin_or_above(role_name: str) -> bool:
    """Check if role is admin or above."""
    try:
        role = RoleName(role_name)
        return ROLE_LEVELS[role] >= ROLE_LEVELS[RoleName.ADMIN]
    except ValueError:
        return False


def can_access_all_customers(role_name: str) -> bool:
    """Check if role can access all customers (not just own)."""
    return is_admin_or_above(role_name)


def can_modify_customer(role_name: str, customer_owner_id: int, current_user_id: int) -> bool:
    """Check if user can modify a specific customer."""
    if is_admin_or_above(role_name):
        return True
    return customer_owner_id == current_user_id
