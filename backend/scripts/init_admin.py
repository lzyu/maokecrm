"""Initialize super_admin user (uses DATABASE_URL from .env / .env.local)."""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select

from app.core.security import get_password_hash
from app.database import async_session_maker
from app.models.user import Role, User

DEFAULT_PHONE = "admin"
DEFAULT_PASSWORD = "admin123"
DEFAULT_NAME = "管理员"


async def init_admin() -> None:
    async with async_session_maker() as session:
        r_roles = await session.execute(select(Role))
        if not r_roles.scalars().all():
            for name in ("sales", "consultant", "admin", "super_admin"):
                session.add(Role(role_name=name))
            await session.commit()

        r_user = await session.execute(
            select(User).where(User.phone == DEFAULT_PHONE, User.deleted_at.is_(None))
        )
        if r_user.scalar_one_or_none():
            print("管理员已存在，跳过创建。")
            print(f"登录账号: {DEFAULT_PHONE}")
            print(f"密码: {DEFAULT_PASSWORD}")
            return

        r_role = await session.execute(
            select(Role).where(Role.role_name == "super_admin")
        )
        role = r_role.scalar_one_or_none()
        if role is None:
            raise RuntimeError("缺少 super_admin 角色")

        session.add(
            User(
                name=DEFAULT_NAME,
                role_id=role.id,
                phone=DEFAULT_PHONE,
                password_hash=get_password_hash(DEFAULT_PASSWORD),
                status="active",
            )
        )
        await session.commit()

        print("已创建超级管理员。")
        print(f"登录账号（手机号字段）: {DEFAULT_PHONE}")
        print(f"密码: {DEFAULT_PASSWORD}")
        print("角色: super_admin")


if __name__ == "__main__":
    asyncio.run(init_admin())
