"""Script to reset admin password with bcrypt."""

import psycopg2
import bcrypt


def reset_admin_password():
    """Reset admin password."""
    # Generate new password hash with bcrypt directly
    password = "admin123"
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    print(f"New password hash: {hashed}")

    # Connect to database
    conn = psycopg2.connect(
        host="192.168.3.16",
        port=5432,
        user="root",
        password="sk1234",
        database="maoke",
    )

    try:
        cursor = conn.cursor()

        # Update password
        cursor.execute(
            "UPDATE users SET password_hash = %s WHERE id = 1",
            (hashed,)
        )
        conn.commit()
        print("Admin password updated successfully!")

        cursor.close()

    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    reset_admin_password()
