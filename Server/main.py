import json
import os
from ServerComm import ServerConnection
from UserManager import UserManager
from MessageHandler import MessageHandler
from Encryption import EncryptionManager
import signal
import sys
from datetime import datetime  # Add this import
import time

class ChatServer:
   def __init__(self):
      """Initialize the chat server and its components."""
      self.load_config()
      self.user_manager = UserManager()
      self.message_handler = MessageHandler(self.user_manager)
      self.encryption = EncryptionManager()
      self.running = False
      
      # Create message handlers before creating server
      self.setup_message_handlers()
      
      # Initialize server with handlers
      self.server = ServerConnection(handlers=self.handlers)

   def setup_message_handlers(self):
      """Set up handlers for different types of client messages."""
      self.handlers = {
         "register": self.handle_registration,
         "login": self.handle_login,
         "start_private_chat": self.handle_start_private_chat,
         "send_message": self.handle_chat_message,
         "disconnect": self.handle_disconnect,
         "create_chat": self.handle_create_chat,
         "get_chats": self.handle_get_chats,
         "get_messages": self.handle_get_messages,
      }

   def load_config(self):
      """Load server configuration from config.json."""
      try:
         config_path = os.path.join(os.path.dirname(__file__), "..", "config.json")
         with open(config_path, 'r') as f:
               self.config = json.load(f)
         print("Configuration loaded successfully")
      except Exception as e:
         print(f"Error loading configuration: {e}")
         sys.exit(1)

   def start(self):
      """Start the chat server."""
      try:
         self.running = True
         print("Starting chat server...")
         
         # Initialize encryption
         self.encryption.generate_keys()
         print("Encryption keys generated")
         
         # Start the server
         if self.server.start_server():
               print(f"Server running on {self.config['server_ip_address']}:{self.config['server_port']}")
               
               # Set up message handlers
               self.setup_message_handlers()
               
               # Keep the server running
               last_cleanup = time.time()
               while self.running:
                  # Cleanup old sessions every hour
                  current_time = time.time()
                  if current_time - last_cleanup > 3600:  # 3600 seconds = 1 hour
                     self.user_manager.cleanup_old_sessions()
                     last_cleanup = current_time
                  time.sleep(1)  # Sleep for 1 second to prevent high CPU usage
                  
         else:
               print("Failed to start server")
               sys.exit(1)
               
      except Exception as e:
         print(f"Server error: {e}")
         self.shutdown()
         
   def handle_registration(self, client_socket, data):
      """Handle user registration requests."""
      username = data.get("username")
      password = data.get("password")
      
      if not username or not password:
         return {"success": False, "message": "Missing credentials"}
         
      success, message = self.user_manager.register_user(username, password)
      return {"success": success, "message": message}
   
   def handle_login(self, client_socket, data):
      """Handle user login requests."""
      username = data.get("username")
      password = data.get("password")
      
      if not username or not password:
         return {"success": False, "message": "Missing credentials"}
         
      success, message, token = self.user_manager.authenticate_user(username, password)
      return {
         "success": success,
         "message": message,
         "token": token if success else None
      }

   def handle_create_chat(self, client_socket, data):
      """Handle chat creation requests."""
      token = data.get("token")
      participants = data.get("participants", [])
      chat_type = data.get("type", "private")
      
      # Validate session
      is_valid, user_id = self.user_manager.validate_session(token)
      if not is_valid:
         return {"success": False, "message": "Invalid session"}
         
      success, chat_id = self.message_handler.create_chat(user_id, participants, chat_type)
      return {
         "success": success,
         "chat_id": chat_id if success else None
      }

   def handle_message(self, client_socket, data):
      """Handle message sending requests."""
      token = data.get("token")
      chat_id = data.get("chat_id")
      content = data.get("content")
      
      # Validate session
      is_valid, user_id = self.user_manager.validate_session(token)
      if not is_valid:
         return {"success": False, "message": "Invalid session"}
         
      success, message_id = self.message_handler.save_message(
         chat_id, user_id, content
      )
      return {
         "success": success,
         "message_id": message_id if success else None
      }

   def handle_get_chats(self, client_socket, data):
      """Handle requests to get user's chats."""
      token = data.get("token")
      
      # Validate session
      is_valid, user_id = self.user_manager.validate_session(token)
      if not is_valid:
         return {"success": False, "message": "Invalid session"}
         
      chats = self.message_handler.get_user_chats(user_id)
      return {
         "success": True,
         "chats": chats
      }

   def handle_get_messages(self, client_socket, data):
      """Handle requests to get chat messages."""
      token = data.get("token")
      chat_id = data.get("chat_id")
      limit = data.get("limit", 50)
      
      # Validate session
      is_valid, user_id = self.user_manager.validate_session(token)
      if not is_valid:
         return {"success": False, "message": "Invalid session"}
         
      success, messages = self.message_handler.fetch_chat_history(
         chat_id, user_id, limit
      )
      return {
         "success": success,
         "messages": messages if success else []
      }

   def handle_disconnect(self, client_socket, data):
      """Handle client disconnect requests."""
      token = data.get("token")
      if token:
         # Clean up user session
         is_valid, user_id = self.user_manager.validate_session(token)
         if is_valid:
               # Additional cleanup if needed
               pass
      return {"success": True, "message": "Disconnected"}

   def handle_shutdown(self, signum, frame):
      """Handle shutdown signals gracefully."""
      print("\nShutting down server...")
      self.shutdown()

   def shutdown(self):
      """Clean shutdown of the server."""
      self.running = False
      if hasattr(self, 'server'):
         self.server.stop_server()
      if hasattr(self, 'user_manager'):
         self.user_manager.close()
      print("Server shutdown complete")
      sys.exit(0)

   def handle_start_private_chat(self, client_socket, data):
      """Handle request to start a private chat with another user."""
      token = data.get("token")
      target_username = data.get("target_username")
      
      try:
         # Validate session and get requester's ID
         is_valid, user_id = self.user_manager.validate_session(token)
         if not is_valid:
            return {"success": False, "message": "Invalid session"}
         
         # Get target user
         target_user = self.user_manager.get_user_by_username(target_username)
         if not target_user:
            return {"success": False, "message": "User not found"}
               
         # Can't chat with yourself
         if user_id == target_user['user_id']:
            return {"success": False, "message": "Cannot start chat with yourself"}
               
         # Get or create chat between users
         chat_id = self.user_manager.get_or_create_private_chat(user_id, target_user['user_id'])
         if not chat_id:
            return {"success": False, "message": "Failed to create chat"}
               
         # Get chat history with message limit from config
         messages = self.user_manager.get_formatted_chat_messages(
            chat_id, 
            limit=self.config['chat_settings']['message_history_limit']
         )
         
         # Format messages for client
         formatted_messages = []
         for msg in messages:
            formatted_messages.append({
               'message_id': msg['message_id'],
               'content': msg['message_content'],
               'timestamp': msg['timestamp'],
               'username': msg['sender_username']
            })
               
         return {
            "success": True,
            "chat_id": chat_id,
            "target_username": target_user['username'],
            "messages": formatted_messages
         }
         
      except Exception as e:
         print(f"Error in handle_start_private_chat: {e}")
         return {"success": False, "message": "Internal server error"}

   def handle_chat_message(self, client_socket, data):
      """Handle a new chat message."""
      token = data.get("token")
      chat_id = data.get("chat_id")
      content = data.get("content")
      
      try:
         # Validate session
         is_valid, user_id = self.user_manager.validate_session(token)
         if not is_valid:
            return {"success": False, "message": "Invalid session"}
               
         # Validate message length
         if len(content) > self.config['chat_settings']['max_message_length']:
            return {"success": False, "message": "Message too long"}
               
         # Store message
         success, message_id = self.user_manager.store_message(chat_id, user_id, content)
         if not success:
            return {"success": False, "message": "Failed to store message"}
               
         # Get message details for broadcast
         sender_info = self.user_manager.get_user_by_id(user_id)
         current_time = datetime.now()
         timestamp = current_time.strftime("%Y-%m-%d %H:%M:%S")
         
         # Prepare message broadcast
         message_data = {
            "message_id": message_id,
            "chat_id": chat_id,
            "content": content,
            "timestamp": timestamp,
            "username": sender_info['username']
         }
         
         # Broadcast to all chat members
         self._broadcast_to_chat_members(chat_id, {
            "type": "new_message",
            "data": message_data
         }, exclude_socket=client_socket)
         
         return {
            "success": True,
            "message_id": message_id,
            "timestamp": timestamp
      }
         
      except Exception as e:
         print(f"Error in handle_chat_message: {e}")
         return {"success": False, "message": "Internal server error"}
    
   def _broadcast_to_chat_members(self, chat_id, message, exclude_socket=None):
      """Broadcast message to all members of a chat."""
      try:
         # Get all chat members
         members = self.user_manager.get_chat_members(chat_id)
         
         # Access connected clients through the ServerConnection instance
         connected_clients = {
            socket: client_info for socket, client_info in self.server.connected_clients.items()
         }
         
         for socket, client_info in connected_clients.items():
            if socket != exclude_socket:
               try:
                  self.server.send_to_client(socket, message)
               except Exception as e:
                  print(f"Error broadcasting to client: {e}")
                     
      except Exception as e:
         print(f"Error in broadcast: {e}")
   
if __name__ == "__main__":
    server = ChatServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nServer shutdown requested by user")
        server.shutdown()