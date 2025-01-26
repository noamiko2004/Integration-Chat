"""
ClientComm.py

Manages all communication between the client and server.

Responsibilities:
1. Establish and maintain a secure connection to the server.
2. Send requests for user actions (registration, login, fetching chats).
3. Send and receive messages during active chat sessions.
4. Fetch chat history from the server when entering a conversation.

Key Classes:
- Message: Represents a message with attributes like content, sender, timestamp, and chat ID.

Key Functions:
- connect(): Establish a connection with the server using IP and port from config.json.
- send_request(request_type, data): Send a formatted request to the server (e.g., register, login, fetch chat history).
- receive_response(): Wait for and handle the server's response.
- send_message(message): Send a message object to the server.
- receive_message(): Receive a new message from the server during an active session.
- disconnect(): Gracefully close the connection.

Key Variables:
- socket: The socket object for managing the connection.
- server_ip: Loaded from config.json, specifies the server's IP address.
- server_port: Loaded from config.json, specifies the server's port.
"""
