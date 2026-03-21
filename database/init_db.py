"""Script to initialize database with DDL and seed data."""

import asyncio
import asyncpg
from pathlib import Path


async def init_database():
    """Execute DDL script and seed data."""
    # Read SQL file
    sql_file = Path(__file__).parent / "init_db.sql"
    sql_content = sql_file.read_text(encoding="utf-8")

    # Connect to database
    conn = await asyncpg.connect(
        host="192.168.3.16",
        port=8881,
        user="root",
        password="sk1234",
        database="maoke",
    )

    try:
        # Execute SQL
        await conn.execute(sql_content)
        print("Database initialized successfully!")

        # Verify tables
        tables = await conn.fetch("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        print(f"\nCreated tables: {[t['table_name'] for t in tables]}")

        # Verify roles
        roles = await conn.fetch("SELECT id, role_name FROM roles ORDER BY id")
        print(f"\nRoles: {[(r['id'], r['role_name']) for r in roles]}")

        # Verify admin user
        admin = await conn.fetchrow("""
            SELECT u.id, u.name, r.role_name
            FROM users u
            JOIN roles r ON u.role_id = r.id
            WHERE r.role_name = 'super_admin'
        """)
        if admin:
            print(f"\nAdmin user: id={admin['id']}, name={admin['name']}, role={admin['role_name']}")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(init_database())
