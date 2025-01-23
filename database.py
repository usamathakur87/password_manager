import sqlite3

def create_connection():
    """
    Create a database connection to the SQLite database
    """
    conn = None
    try:
        conn = sqlite3.connect("password_manager.db")
        # Enforce foreign key constraints
        conn.execute("PRAGMA foreign_keys = 1;")
        return conn
    except sqlite3.Error as e:
        print(f"Error creating DB connection: {e}")
    return conn

def create_tables():
    """
    Create the necessary tables in the SQLite database if not present
    """
    conn = create_connection()
    cursor = conn.cursor()

    # Create users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    );
    """)

    # Create suppliers table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS suppliers (
        supplier_id INTEGER PRIMARY KEY AUTOINCREMENT,
        supplier_name TEXT NOT NULL,
        office_id TEXT,
        user_id TEXT,
        password TEXT NOT NULL,
        url TEXT,
        date_created TEXT DEFAULT CURRENT_TIMESTAMP,
        last_reset TEXT,
        owner_user_id INTEGER NOT NULL,
        FOREIGN KEY (owner_user_id) REFERENCES users(user_id)
    );
    """)

    conn.commit()
    conn.close()
