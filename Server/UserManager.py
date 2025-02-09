import sqlite3
import bcrypt
import secrets
from datetime import datetime
import time
import os
import re

class UserManager:
    def __init__(self, db_path="./server/storage/chat_database.db"):
        """Initialize the UserManager with database connection."""
        # Get the absolute path of the current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Construct storage path relative to server directory
        self.db_path = os.path.join(current_dir, "storage", "chat_database.db")
        self._ensure_db_directory()
        self.conn = self._create_connection()
        self._create_tables()

    def _ensure_db_directory(self):
        """Ensure the database directory exists."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def _create_connection(self):
        """Create a database connection."""
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row  # This enables name-based access to columns
            return conn
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")
            raise

    def _create_tables(self):
        """Create necessary database tables if they don't exist."""
        try:
            cursor = self.conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Chats table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chats (
                    chat_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_type TEXT CHECK(chat_type IN ('private', 'group')) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Chat members table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_members (
                    chat_id INTEGER,
                    user_id INTEGER,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (chat_id, user_id),
                    FOREIGN KEY (chat_id) REFERENCES chats (chat_id),
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Messages table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER,
                    sender_id INTEGER,
                    message_content TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (chat_id) REFERENCES chats (chat_id),
                    FOREIGN KEY (sender_id) REFERENCES users (user_id)
                )
            ''')
            
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error creating tables: {e}")
            raise

    def validate_username(self, username):
        """
        Validate username according to rules:
        - Length between 4 and 20 characters
        - Only English letters, numbers, and special characters
        """
        
        # Check length
        if len(username) < 4 or len(username) > 20:
            return False, "Username must be between 4 and 20 characters"
            
        # Check characters using regex
        if not re.match(r'^[a-zA-Z0-9!@#$%]+$', username):
            return False, "Username can only contain English letters, numbers, and special characters (!@#$%)"
        
        return True, "Username is valid"

    def validate_password(self, password):
        """
        Validate password according to rules:
        - Length between 8 and 100 characters
        - Only English letters, numbers, and special characters
        """
        
        # Check length
        if len(password) < 8 or len(password) > 100:
            return False, "Password must be between 8 and 100 characters"
            
        # Check characters using regex
        if not re.match(r'^[a-zA-Z0-9!@#$%^&*()_+\-=\[\]{};:,.<>?]+$', password):
            return False, "Password can only contain English letters, numbers, and special characters"
        
        return True, "Password is valid"

    def register_user(self, username, password):
        """Register a new user with validation."""
        try:
            cursor = self.conn.cursor()
            
            # Validate username
            is_valid, message = self.validate_username(username)
            if not is_valid:
                return False, message
                
            # Validate password
            is_valid, message = self.validate_password(password)
            if not is_valid:
                return False, message
            
            # Check if username already exists (case insensitive)
            cursor.execute('SELECT 1 FROM users WHERE LOWER(username) = LOWER(?)', (username,))
            if cursor.fetchone():
                return False, "Username already exists"
            
            # Hash the password
            salt = bcrypt.gensalt()
            password_hash = bcrypt.hashpw(password.encode(), salt)
            
            # Insert new user (with original case)
            cursor.execute(
                'INSERT INTO users (username, password_hash) VALUES (?, ?)',
                (username, password_hash)
            )
            self.conn.commit()
            
            return True, "User registered successfully"
            
        except sqlite3.Error as e:
            self.conn.rollback()
            return False, f"Database error: {str(e)}"

    def authenticate_user(self, username, password):
        """Authenticate a user and return a session token."""
        try:
            cursor = self.conn.cursor()
            
            # Get user data (case insensitive username match)
            cursor.execute(
                'SELECT user_id, username, password_hash FROM users WHERE LOWER(username) = LOWER(?)',
                (username,)
            )
            user = cursor.fetchone()
            
            if not user:
                return False, "Invalid username or password", None
            
            # Verify password
            if not bcrypt.checkpw(password.encode(), user['password_hash'].encode()):
                return False, "Invalid username or password", None
            
            # Generate session token
            session_token = secrets.token_urlsafe(32)
            
            # Store session
            cursor.execute(
                'INSERT INTO sessions (session_id, user_id) VALUES (?, ?)',
                (session_token, user['user_id'])
            )
            self.conn.commit()
            
            return True, "Authentication successful", session_token
        except sqlite3.Error as e:
            self.conn.rollback()
            return False, f"Database error: {str(e)}", None
        
    def validate_session(self, session_token):
        """Validate a session token and return user_id if valid."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                'SELECT user_id FROM sessions WHERE session_id = ?',
                (session_token,)
            )
            session = cursor.fetchone()
            
            if session:
                return True, session['user_id']
            return False, None
        except sqlite3.Error as e:
            return False, None

    def create_chat(self, user_ids, chat_type='private'):
        """Create a new chat between users."""
        try:
            cursor = self.conn.cursor()
            
            # Create new chat
            cursor.execute(
                'INSERT INTO chats (chat_type) VALUES (?)',
                (chat_type,)
            )
            chat_id = cursor.lastrowid
            
            # Add members to chat
            for user_id in user_ids:
                cursor.execute(
                    'INSERT INTO chat_members (chat_id, user_id) VALUES (?, ?)',
                    (chat_id, user_id)
                )
            
            self.conn.commit()
            return True, chat_id
        except sqlite3.Error as e:
            self.conn.rollback()
            return False, str(e)

    def store_message(self, chat_id, sender_id, message_content):
        """Store an encrypted message."""
        try:
            cursor = self.conn.cursor()
            
            # Verify sender is member of chat
            cursor.execute(
                'SELECT 1 FROM chat_members WHERE chat_id = ? AND user_id = ?',
                (chat_id, sender_id)
            )
            if not cursor.fetchone():
                return False, "User is not a member of this chat"
            
            # Store message
            cursor.execute(
                '''INSERT INTO messages 
                   (chat_id, sender_id, message_content) 
                   VALUES (?, ?, ?)''',
                (chat_id, sender_id, message_content)
            )
            self.conn.commit()
            return True, cursor.lastrowid
        except sqlite3.Error as e:
            self.conn.rollback()
            return False, str(e)

    def get_user_chats(self, user_id):
        """Get all chats for a user."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT c.chat_id, c.chat_type, c.created_at
                FROM chats c
                JOIN chat_members cm ON c.chat_id = cm.chat_id
                WHERE cm.user_id = ?
            ''', (user_id,))
            return cursor.fetchall()
        except sqlite3.Error as e:
            return []

    def get_chat_messages(self, chat_id, user_id, limit=50):
        """Get messages for a chat (if user is a member)."""
        try:
            cursor = self.conn.cursor()
            
            # Verify user is member of chat
            cursor.execute(
                'SELECT 1 FROM chat_members WHERE chat_id = ? AND user_id = ?',
                (chat_id, user_id)
            )
            if not cursor.fetchone():
                return False, "User is not a member of this chat"
            
            # Get messages
            cursor.execute('''
                SELECT message_id, sender_id, message_content, timestamp
                FROM messages
                WHERE chat_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (chat_id, limit))
            
            return True, cursor.fetchall()
        except sqlite3.Error as e:
            return False, str(e)

    def cleanup_old_sessions(self, max_age_hours=24):
        """Remove sessions older than specified hours."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                'DELETE FROM sessions WHERE created_at < datetime("now", "-24 hours")'
            )
            self.conn.commit()
        except sqlite3.Error as e:
            self.conn.rollback()
            print(f"Error cleaning up sessions: {e}")
            
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()

    def get_user_by_username(self, username):
        """Get user info by username."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                'SELECT user_id, username, created_at FROM users WHERE LOWER(username) = LOWER(?)',
                (username,)
            )
            return cursor.fetchone()
        except sqlite3.Error:
            return None

    def get_or_create_private_chat(self, user1_id, user2_id):
        """Get existing private chat between users or create new one."""
        try:
            cursor = self.conn.cursor()
            
            # Check if private chat already exists
            cursor.execute('''
                SELECT c.chat_id
                FROM chats c
                JOIN chat_members cm1 ON c.chat_id = cm1.chat_id
                JOIN chat_members cm2 ON c.chat_id = cm2.chat_id
                WHERE c.chat_type = 'private'
                AND cm1.user_id = ?
                AND cm2.user_id = ?
                AND (
                    SELECT COUNT(*) FROM chat_members 
                    WHERE chat_id = c.chat_id
                ) = 2
            ''', (user1_id, user2_id))
            
            result = cursor.fetchone()
            if result:
                return result['chat_id']
                
            # Create new private chat
            success, chat_id = self.create_chat([user1_id, user2_id], 'private')
            if success:
                return chat_id
            return None
                
        except sqlite3.Error:
            return None

    def get_formatted_chat_messages(self, chat_id, limit=50):
        """Get messages with sender usernames and formatted timestamps."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT 
                    m.message_id,
                    m.message_content,
                    m.timestamp,
                    u.username as sender_username
                FROM messages m
                JOIN users u ON m.sender_id = u.user_id
                WHERE m.chat_id = ?
                ORDER BY m.timestamp DESC
                LIMIT ?
            ''', (chat_id, limit))
            
            return cursor.fetchall()
        except sqlite3.Error:
            return []
        
    def get_user_by_id(self, user_id):
        """Get user info by ID."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                'SELECT user_id, username, created_at FROM users WHERE user_id = ?',
                (user_id,)
            )
            return cursor.fetchone()
        except sqlite3.Error:
            return None

    def get_chat_members(self, chat_id):
        """Get all member IDs for a chat."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                'SELECT user_id FROM chat_members WHERE chat_id = ?',
                (chat_id,)
            )
            return [row['user_id'] for row in cursor.fetchall()]
        except sqlite3.Error:
            return []


# Example usage and testing
if __name__ == "__main__":
    # Create UserManager instance
    user_manager = UserManager()
    
    try:
        # Test user registration
        success, message = user_manager.register_user("testuser", "password123")
        print(f"Registration: {message}")
        
        # Test authentication
        success, message, token = user_manager.authenticate_user("testuser", "password123")
        print(f"Authentication: {message}")
        if token:
            print(f"Session token: {token}")
        
        # Validate session
        if token:
            is_valid, user_id = user_manager.validate_session(token)
            print(f"Session valid: {is_valid}, User ID: {user_id}")
        
        # Create a chat
        if user_id:
            success, chat_id = user_manager.create_chat([user_id])
            print(f"Chat created: {success}, Chat ID: {chat_id}")
            
            # Store a message
            if success:
                success, msg_id = user_manager.store_message(
                    chat_id, 
                    user_id, 
                    "Hello, this is an encrypted test message!"
                )
                print(f"Message stored: {success}, Message ID: {msg_id}")
        
    except Exception as e:
        print(f"Error during testing: {e}")
    finally:
        user_manager.close()