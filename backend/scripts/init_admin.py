"""Initialize admin user for testing."""

import asyncio
import asyncpg
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.security import get_password_hash

async def init_admin():
    conn = await asyncpg.connect(
        host="192.168.3.16",
        port=5432,
        user="root",
        password="sk1234",
        database="maoke"
    )

    try:
        # Check if admin exists
        existing = await conn.fetchrow(
            "SELECT id FROM users WHERE phone = 'admin' AND deleted_at IS NULL"
        )

        if existing:
            print("Admin user already exists")
            return

        # Get super_admin role
        role = await conn.fetchrow(
            "SELECT id FROM roles WHERE role_name = 'super_admin'"
        )

        if not role:
            print("super_admin role not found, creating roles...")
            await conn.execute("""
                INSERT INTO roles (role_name)
                VALUES ('sales'), ('consultant'), ('admin'), ('super_admin')
                ON CONFLICT (role_name) DO NOTHING
            """)
            role = await conn.fetchrow(
                "SELECT id FROM roles WHERE role_name = 'super_admin'"
            )

        # Create admin user
        password_hash = get_password_hash("admin123")
        await conn.execute("""
            INSERT INTO users (name, role_id, phone, password_hash, status, created_at, updated_at)
            VALUES ('管理员', $1, 'admin', $2, 'active', NOW(), NOW())
        """, role['id'], password_hash)

        print("Admin user created successfully!")
        print("账号: admin")
        print("密码: admin123")

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(init_admin())
