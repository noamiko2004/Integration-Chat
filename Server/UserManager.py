"""
UserManager.py

Manages user registration, authentication, and session handling.

Responsibilities:
1. Register new users:
   - Ensure usernames are unique.
   - Hash and securely store passwords.
2. Authenticate users:
   - Validate credentials during login.
   - Return session tokens for authenticated users.
3. Manage session tokens:
   - Generate and verify session tokens for active users.

Key Classes:
- UserManager: Handles user-related operations like registration, login, and session validation.

Key Functions:
- register_user(username, password): Add a new user to the database with a hashed password.
- authenticate_user(username, password): Validate login credentials and generate a session token.
- validate_session(token): Check if a session token is valid.
- load_user_data(): Load existing user data from the database.
- save_user_data(): Save updated user data back to the database.

Key Variables:
- db_connection: The database connection object for storing and retrieving user data.
- active_sessions: A dictionary mapping session tokens to user information.
"""
