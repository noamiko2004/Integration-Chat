import sqlite3
import hashlib
import os
import uuid

class UserManager:
    def __init__(self, db_path="../users.db"):
        """Initialize the user manager and database connection."""
        self.db_path = db_path
        self.active_sessions = {}  # {session_token: username}
        self.connect_db()
        self.create_users_table()
    
    def connect_db(self):
        """Establish a connection to the database."""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
    
    def create_users_table(self):
        """Ensure the users table exists."""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash TEXT
            )
        """
        )
        self.conn.commit()
    
    def register_user(self, username, password):
        """Register a new user with a hashed password."""
        self.cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
        if self.cursor.fetchone():
            return False, "Username already exists."
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        self.cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
        self.conn.commit()
        return True, "User registered successfully."
    
    def authenticate_user(self, username, password):
        """Validate user credentials and return a session token."""
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        self.cursor.execute("SELECT username FROM users WHERE username = ? AND password_hash = ?", (username, password_hash))
        if self.cursor.fetchone():
            session_token = str(uuid.uuid4())
            self.active_sessions[session_token] = username
            return True, session_token
        return False, "Invalid username or password."
    
    def validate_session(self, token):
        """Check if a session token is valid."""
        return token in self.active_sessions
    
    def close_db(self):
        """Close the database connection."""
        self.conn.close()

# Example Usage:
user_manager = UserManager()
print(user_manager.register_user("user1", "securepass"))
print(user_manager.authenticate_user("user1", "securepass"))
