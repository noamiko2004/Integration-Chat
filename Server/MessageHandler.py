"""
MessageHandler.py

Manages chat messages and chat history.

Responsibilities:
1. Save incoming messages to the database.
2. Fetch chat history for private and group chats.
3. Broadcast messages to group chat participants.

Key Classes:
- MessageHandler: Handles all chat-related operations.

Key Functions:
- save_message(chat_id, sender_id, content): Save a message to the database.
- fetch_chat_history(chat_id, limit=None): Retrieve the message history for a specific chat.
- broadcast_message(chat_id, message): Send a message to all participants in a group chat.
- create_chat(participants, chat_type): Create a new chat (private or group).

Key Variables:
- db_connection: The database connection object for storing and retrieving messages.
"""
