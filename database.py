import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash


DATABASE_NAME = "convora.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_NAME)

    connection.row_factory = sqlite3.Row

    return connection


def init_database():

    connection = get_connection()

    cursor = connection.cursor()

    # ==========================================
    # USERS TABLE
    # ==========================================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            username TEXT NOT NULL UNIQUE,

            email TEXT NOT NULL UNIQUE,

            password_hash TEXT NOT NULL,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
        """
    )

    # ==========================================
    # MESSAGES TABLE
    # ==========================================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            role TEXT NOT NULL,

            content TEXT NOT NULL,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE

        )
        """
    )

    connection.commit()

    connection.close()


# ==========================================
# CREATE USER
# ==========================================

def create_user(username, email, password):

    connection = get_connection()

    try:

        password_hash = generate_password_hash(password)

        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO users
            (
                username,
                email,
                password_hash
            )

            VALUES (?, ?, ?)
            """,
            (
                username,
                email,
                password_hash
            )
        )

        connection.commit()

        return True

    except sqlite3.IntegrityError:

        return False

    finally:

        connection.close()


# ==========================================
# GET USER
# ==========================================

def get_user_by_email(email):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE email = ?
        """,
        (email,)
    )

    user = cursor.fetchone()

    connection.close()

    return user


# ==========================================
# VERIFY LOGIN
# ==========================================

def verify_user(email, password):

    user = get_user_by_email(email)

    if not user:

        return None

    if not check_password_hash(
        user["password_hash"],
        password
    ):

        return None

    return user


# ==========================================
# SAVE MESSAGE
# ==========================================

def save_message(
    user_id,
    role,
    content
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO messages
        (
            user_id,
            role,
            content
        )

        VALUES (?, ?, ?)
        """,
        (
            user_id,
            role,
            content
        )
    )

    connection.commit()

    connection.close()


# ==========================================
# GET USER CHAT HISTORY
# ==========================================

def get_messages(
    user_id,
    limit=10
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT role, content
        FROM messages

        WHERE user_id = ?

        ORDER BY id DESC

        LIMIT ?
        """,
        (
            user_id,
            limit
        )
    )

    rows = cursor.fetchall()

    connection.close()

    # Reverse because query gets newest first

    rows = list(reversed(rows))

    return [
        {
            "role": row["role"],
            "content": row["content"]
        }

        for row in rows
    ]


# ==========================================
# DELETE USER CHAT
# ==========================================

def clear_user_messages(user_id):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM messages
        WHERE user_id = ?
        """,
        (user_id,)
    )

    connection.commit()

    connection.close()