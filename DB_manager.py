import sqlite3
import json

DB_NAME = "users.db"

def init_db():
    """Creates the tables if they don't exist."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        
        # Sellers table (username is NOT unique, phone IS unique)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                phone TEXT UNIQUE NOT NULL,
                address TEXT NOT NULL
            )
        ''')
        
        # Houses table (linked to seller via seller_id)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS houses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                seller_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                bedrooms INTEGER NOT NULL,
                bathrooms REAL NOT NULL,
                sqft_living INTEGER NOT NULL,
                sqft_lot INTEGER,
                floors REAL,
                waterfront INTEGER DEFAULT 0,
                view INTEGER DEFAULT 0,
                condition INTEGER DEFAULT 3,
                grade INTEGER DEFAULT 7,
                yr_built INTEGER,
                yr_renovated INTEGER DEFAULT 0,
                address TEXT NOT NULL,
                city TEXT,
                state TEXT,
                zipcode TEXT,
                lat REAL,
                long REAL,
                parking INTEGER DEFAULT 0,
                garden INTEGER DEFAULT 0,
                pool INTEGER DEFAULT 0,
                furnished INTEGER DEFAULT 0,
                images TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (seller_id) REFERENCES users(id)
            )
        ''')
        
        conn.commit()


# ==========================================
# USER / SELLER FUNCTIONS
# ==========================================

def create_user(username, email, hashed_password, phone, address):
    """Inserts a new seller into the database."""
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, email, password, phone, address) VALUES (?, ?, ?, ?, ?)", 
                (username, email, hashed_password, phone, address)
            )
            conn.commit()
        return True, "Seller registered successfully"
    except sqlite3.IntegrityError as e:
        error_msg = str(e).lower()
        if "phone" in error_msg:
            return False, "Phone number already registered"
        elif "email" in error_msg:
            return False, "Email already registered"
        return False, "Email or Phone already exists"

def get_user_by_email(email):
    """Fetches a user by their email address."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password, phone, address FROM users WHERE email = ?", (email,))
        return cursor.fetchone()  # Returns (id, username, hash, phone, address) or None

def update_user_password(email, hashed_password):
    """Updates the password for a given email."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password = ? WHERE email = ?", (hashed_password, email))
        conn.commit()
        return cursor.rowcount > 0


# ==========================================
# HOUSE LISTING FUNCTIONS
# ==========================================

def create_house(seller_id, house_data):
    """Inserts a new house listing into the database. Returns (success, house_id or error)."""
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO houses (
                    seller_id, title, description, price,
                    bedrooms, bathrooms, sqft_living, sqft_lot, floors,
                    waterfront, view, condition, grade,
                    yr_built, yr_renovated,
                    address, city, state, zipcode, lat, long,
                    parking, garden, pool, furnished, images
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                seller_id,
                house_data["title"],
                house_data.get("description", ""),
                house_data["price"],
                house_data["bedrooms"],
                house_data["bathrooms"],
                house_data["sqft_living"],
                house_data.get("sqft_lot"),
                house_data.get("floors"),
                house_data.get("waterfront", 0),
                house_data.get("view", 0),
                house_data.get("condition", 3),
                house_data.get("grade", 7),
                house_data.get("yr_built"),
                house_data.get("yr_renovated", 0),
                house_data["address"],
                house_data.get("city"),
                house_data.get("state"),
                house_data.get("zipcode"),
                house_data.get("lat"),
                house_data.get("long"),
                house_data.get("parking", 0),
                house_data.get("garden", 0),
                house_data.get("pool", 0),
                house_data.get("furnished", 0),
                json.dumps(house_data.get("images", []))
            ))
            conn.commit()
            return True, cursor.lastrowid
    except Exception as e:
        return False, str(e)

def get_houses_by_seller(seller_id):
    """Fetches all houses listed by a specific seller."""
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM houses WHERE seller_id = ? ORDER BY created_at DESC", (seller_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def get_all_houses():
    """Fetches all houses with seller info (for public browsing)."""
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT houses.*, users.username as seller_name, users.phone as seller_phone
            FROM houses 
            JOIN users ON houses.seller_id = users.id
            ORDER BY houses.created_at DESC
        ''')
        rows = cursor.fetchall()
        return [dict(row) for row in rows]