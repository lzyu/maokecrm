"""Script to initialize database with DDL and seed data."""

import psycopg2
from pathlib import Path


def init_database():
    """Execute DDL script and seed data."""
    # Read SQL file
    sql_file = Path(__file__).parent / "init_db.sql"
    sql_content = sql_file.read_text(encoding="utf-8")

    # Connect to database with SSL disabled
    conn = psycopg2.connect(
        host="192.168.3.16",
        port=5432,
        user="root",
        password="sk1234",
        database="maoke",
        sslmode="disable",
        connect_timeout=10,
    )

    try:
        cursor = conn.cursor()

        # Execute SQL
        cursor.execute(sql_content)
        conn.commit()
        print("Database initialized successfully!")

        # Verify tables
        cursor.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        print(f"\nCreated tables: {[t[0] for t in tables]}")

        # Verify roles
        cursor.execute("SELECT id, role_name FROM roles ORDER BY id")
        roles = cursor.fetchall()
        print(f"\nRoles: {roles}")

        # Verify admin user
        cursor.execute("""
            SELECT u.id, u.name, r.role_name
            FROM users u
            JOIN roles r ON u.role_id = r.id
            WHERE r.role_name = 'super_admin'
        """)
        admin = cursor.fetchone()
        if admin:
            print(f"\nAdmin user: id={admin[0]}, name={admin[1]}, role={admin[2]}")

        cursor.close()

    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    init_database()
