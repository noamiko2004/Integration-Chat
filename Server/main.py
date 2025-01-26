"""
main.py

Entry point for the server-side application.

Responsibilities:
1. Initialize the server:
   - Load configuration settings (e.g., IP, port) from config.json.
   - Set up necessary components (e.g., database, encryption).
2. Start accepting client connections and manage active sessions.
3. Delegate tasks to other modules:
   - UserManager: Handle user registration and authentication.
   - MessageHandler: Manage chat messages and history.
   - ServerComm: Handle client-server communication.

Key Functions:
- start_server(): Initialize and start the server.
- handle_client(client_socket, client_address): Manage an individual client connection.

Key Variables:
- active_clients: A list or dictionary to track connected clients.
"""
