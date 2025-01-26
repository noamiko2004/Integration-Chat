"""
ServerComm.py

Handles all socket-based communication between the server and connected clients.

Responsibilities:
1. Accept and manage client connections.
2. Send and receive data from clients.
3. Handle disconnections and broadcast messages in group chats.

Key Classes:
- ServerConnection: Manages the server socket and client connections.

Key Functions:
- accept_connections(): Accept new client connections and assign them to threads.
- send_to_client(client_socket, data): Send data to a specific client.
- receive_from_client(client_socket): Receive data from a client.
- broadcast(data, group_id=None): Send data to all clients or a specific group.
- close_connection(client_socket): Gracefully handle client disconnections.

Key Variables:
- server_socket: The socket object for managing the server.
- connected_clients: A dictionary to track connected clients (e.g., `{client_socket: client_info}`).
"""
