"""
main.py

Entry point for the client-side application.

Responsibilities:
1. Display the main menu for user actions:
   - Register a new user.
   - Log in to an existing account.
   - Join or start a chat (private or group).
2. Handle user input and interact with:
   - ClientComm: For communication with the server.
   - Encryption: For secure message exchange.
3. Load chat history from the server when entering a conversation.

Key Functions:
- display_menu(): Show the main menu and handle user choices.
- handle_chat(): Manage user interactions in an active chat session.
- handle_login(): Prompt for login credentials and send to the server.
- handle_registration(): Prompt for registration details and send to the server.

Key Variables:
- session_token: Holds the authentication token after a successful login.
"""
