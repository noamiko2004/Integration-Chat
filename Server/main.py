import json
import os
from ServerComm import ServerConnection
from UserManager import UserManager
from MessageHandler import MessageHandler
from Encryption import EncryptionManager
import signal
import sys
import time

class ChatServer:
    def __init__(self):
        """Initialize the chat server and its components."""
        self.load_config()
        self.user_manager = UserManager()
        self.message_handler = MessageHandler(self.user_manager)
        self.server = ServerConnection()
        self.encryption = EncryptionManager()
        self.running = False
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)

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
            
    def setup_message_handlers(self):
        """Set up handlers for different types of client messages."""
        self.handlers = {
            "register": self.handle_registration,
            "login": self.handle_login,
            "create_chat": self.handle_create_chat,
            "send_message": self.handle_message,
            "get_chats": self.handle_get_chats,
            "get_messages": self.handle_get_messages,
            "disconnect": self.handle_disconnect
        }

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

if __name__ == "__main__":
    server = ChatServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nServer shutdown requested by user")
        server.shutdown()