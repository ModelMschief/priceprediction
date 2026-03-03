import sqlite3

DB_NAME = "users.db"

def init_db():
    """Creates the tables if they don't exist."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        conn.commit()

def create_user(username, email, hashed_password):
    """Inserts a new user into the database."""
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", 
                           (username, email, hashed_password))
            conn.commit()
        return True, "User registered successfully"
    except sqlite3.IntegrityError:
        return False, "Username or Email already exists"

def get_user_by_email(email):
    """Fetches a user by their email address."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password FROM users WHERE email = ?", (email,))
        return cursor.fetchone() # Returns a tuple like (1, 'tiku', 'hash') or None

def update_user_password(email, hashed_password):
    """Updates the password for a given email."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password = ? WHERE email = ?", (hashed_password, email))
        conn.commit()
        # Return True if a row was actually updated, False if email wasn't found
        return cursor.rowcount > 0