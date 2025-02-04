import socket
import threading
import json
import time
from Encryption import EncryptionManager

class RateLimiter:
    def __init__(self):
        self.message_timestamps = {}  # user_id -> list of timestamps
        self.WINDOW_SIZE = 5  # seconds
        self.MAX_MESSAGES = 10  # max messages per window
        
    def can_send_message(self, user_id):
        """Check if user can send a message based on rate limit."""
        current_time = time.time()
        
        # Get user's message timestamps
        timestamps = self.message_timestamps.get(user_id, [])
        
        # Remove timestamps outside the window
        timestamps = [ts for ts in timestamps if current_time - ts <= self.WINDOW_SIZE]
        
        # Update timestamps list
        self.message_timestamps[user_id] = timestamps
        
        # Check if user is within rate limit
        if len(timestamps) >= self.MAX_MESSAGES:
            return False
            
        # Add new timestamp
        timestamps.append(current_time)
        return True


class ServerConnection:
    def __init__(self, handlers=None, config_path="../config.json"):
        """Initialize the server connection manager."""
        self.server_socket = None
        self.connected_clients = {}  # {client_socket: ClientInfo}
        self.server_ip = None
        self.server_port = None
        self.encryption = EncryptionManager()
        self.is_running = False
        self.accept_thread = None
        self.handlers = handlers or {}  # Store message handlers
        self.receive_buffers = {}  # Add buffer for each client
        self.load_config(config_path)
        
        # Generate server keys on initialization
        self.encryption.generate_keys()

    def process_request(self, message_type, client_socket, data):
        """Process a client request and return the appropriate response."""
        try:
            print(f"Processing {message_type} request with data: {data}")
            
            # Use the handler from our handlers dictionary
            if message_type in self.handlers:
                handler = self.handlers[message_type]
                try:
                    handler_response = handler(client_socket, data)
                    
                    # Format the response properly with required type field
                    response = {
                        "type": f"{message_type}_response",
                        "data": handler_response
                    }
                except Exception as handler_error:
                    print(f"Handler error: {handler_error}")
                    response = {
                        "type": "error_response",
                        "data": {
                            "success": False,
                            "message": str(handler_error)
                        }
                    }
            else:
                response = {
                    "type": "error_response",
                    "data": {
                        "success": False,
                        "message": f"Unknown request type: {message_type}"
                    }
                }
                
            print(f"Sending response: {response}")
            return response
            
        except Exception as e:
            print(f"Error processing request: {e}")
            return {
                "type": "error_response",
                "data": {
                    "success": False,
                    "message": str(e)
                }
            }        
        
    class ClientInfo:
        """Helper class to store client-specific information."""
        def __init__(self, address, client_id):
            self.address = address
            self.client_id = client_id
            self.public_key = None
            self.session_established = False
            self.last_activity = time.time()
            self.user_id = None  # Store user_id after login

    class MessageHandler:
        def __init__(self, user_manager):
            self.user_manager = user_manager
            self.encryption = EncryptionManager()
            self.pending_messages = {}
            self.rate_limiter = RateLimiter()  # Add rate limiter

        def save_message(self, chat_id, sender_id, content, encryption_keys=None):
            """Save a message with rate limiting."""
            try:
                # Check rate limit
                if not self.rate_limiter.can_send_message(sender_id):
                    return False, "Message rate limit exceeded. Please wait a few seconds."

                # Verify sender is in chat
                is_member = self._verify_chat_membership(chat_id, sender_id)
                if not is_member:
                    return False, "Sender is not a member of this chat"

                # Rest of the existing save_message code...
                
            except Exception as e:
                return False, f"Error saving message: {str(e)}"

    
    def load_config(self, config_path):
        """Load server IP and port from config.json."""
        try:
            import os
            config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config.json"))
            with open(config_path, "r") as file:
                config = json.load(file)
                self.server_ip = config.get("server_ip_address")
                self.server_port = config.get("server_port")
                if not self.server_ip or not self.server_port:
                    raise ValueError("Missing server configuration")
        except Exception as e:
            raise RuntimeError(f"Failed to load configuration: {str(e)}")
    
    def start_server(self):
        """Start the server and listen for incoming connections."""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.server_ip, self.server_port))
            self.server_socket.listen(10)
            self.is_running = True
            print(f"Server started on {self.server_ip}:{self.server_port}")
            
            # Start accepting connections in a separate thread
            self.accept_thread = threading.Thread(target=self._accept_connections)
            self.accept_thread.daemon = True
            self.accept_thread.start()
            
            return True
        except Exception as e:
            print(f"Failed to start server: {str(e)}")
            self.is_running = False
            return False
    
    def _accept_connections(self):
        """Handle incoming connection requests."""
        while self.is_running:
            try:
                client_socket, client_address = self.server_socket.accept()
                client_id = id(client_socket)
                client_info = self.ClientInfo(client_address, client_id)
                self.connected_clients[client_socket] = client_info
                print(f"New connection from {client_address}")
                
                # Start client handler thread
                threading.Thread(target=self.handle_client, 
                               args=(client_socket,),
                               daemon=True).start()
            except Exception as e:
                if self.is_running:
                    print(f"Error accepting connection: {str(e)}")
                    time.sleep(1)  # Prevent tight loop on error
    
    def handle_client(self, client_socket):
        """Handle communication with a connected client."""
        client_info = self.connected_clients.get(client_socket)
        if not client_info:
            return
        
        try:
            while self.is_running:
                data = self.receive_from_client(client_socket)
                if not data:
                    break
                
                if not client_info.session_established:
                    # Handle secure connection establishment
                    if not self._handle_security_handshake(client_socket, data):
                        break
                    else:
                        print(f"Security handshake completed with {client_info.address}")
                else:
                    # Process the message based on its type
                    message_type = data.get('type')
                    print(f"Received message type: {message_type} from {client_info.address}")
                    
                    if message_type in self.handlers:
                        # Process the request
                        response = self.process_request(message_type, client_socket, data.get('data', {}))
                        # Send response back to client
                        self.send_to_client(client_socket, response)
                    else:
                        print(f"Unknown message type: {message_type}")
                        response = {
                            "type": "error_response",
                            "data": {
                                "success": False,
                                "message": f"Unknown message type: {message_type}"
                            }
                        }
                        self.send_to_client(client_socket, response)

                client_info.last_activity = time.time()
                
        except Exception as e:
            print(f"Error handling client {client_info.address}: {str(e)}")
        finally:
            self.close_connection(client_socket)

    def _handle_security_handshake(self, client_socket, data):
        """Handle the security handshake protocol."""
        client_info = self.connected_clients[client_socket]
        try:
            if not isinstance(data, dict):
                print(f"Invalid data format received: {data}")
                return False

            print(f"Processing handshake data: {data}")  # Debug print
            
            msg_type = data.get('type', '')
            msg_data = data.get('data', {})

            if msg_type == "key_exchange":
                # Receive client's public key and send server's
                client_info.public_key = msg_data.get("client_public_key", "").encode()
                response = {
                    "type": "key_exchange",
                    "data": {
                        "server_public_key": self.encryption.get_public_key().decode()
                    }
                }
                self.send_to_client(client_socket, response)
                return True
                
            elif msg_type == "session_key":
                # Receive and store client's session key
                encrypted_key = bytes.fromhex(msg_data.get("encrypted_session_key", ""))
                session_key = self.encryption.decrypt_session_key(encrypted_key)
                self.encryption.store_client_session_key(client_info.client_id, session_key)
                
                # Confirm session establishment
                response = {
                    "type": "session_confirmed",
                    "data": {}
                }
                self.send_to_client(client_socket, response)
                
                client_info.session_established = True
                print(f"Secure session established with {client_info.address}")
                return True
                
        except Exception as e:
            print(f"Security handshake failed: {str(e)}")
            return False
        
        return True
    
    def send_to_client(self, client_socket, data):
        """Send data to a specific client with message framing."""
        try:
            # Convert response to JSON string
            json_data = json.dumps(data)
            
            # Create frame with message length prefix and delimiter
            frame = f"{len(json_data)}::{json_data}"
            
            # Send the framed message
            client_socket.sendall(frame.encode())
        except Exception as e:
            print(f"Error sending to client: {str(e)}")
            raise

    def receive_from_client(self, client_socket):
        """Receive framed data from a client."""
        try:
            if client_socket not in self.receive_buffers:
                self.receive_buffers[client_socket] = ""
            
            buffer = self.receive_buffers[client_socket]
            
            while True:
                # Read more data if needed
                if '::' not in buffer:
                    data = client_socket.recv(4096).decode()
                    if not data:
                        raise ConnectionError("Client disconnected")
                    buffer += data
                
                # Process framed message
                if '::' in buffer:
                    length_str, rest = buffer.split('::', 1)
                    try:
                        length = int(length_str)
                    except ValueError:
                        # Invalid length prefix, clear buffer and try again
                        buffer = ""
                        continue
                    
                    # Check if we have a complete message
                    if len(rest) >= length:
                        message = rest[:length]
                        buffer = rest[length:]  # Keep remaining data
                        self.receive_buffers[client_socket] = buffer
                        
                        try:
                            return json.loads(message)
                        except json.JSONDecodeError as e:
                            print(f"Invalid JSON received: {str(e)}")
                            raise
                    
                    # Need more data for complete message
                    continue
                
                # No complete message yet, read more
                data = client_socket.recv(4096).decode()
                if not data:
                    raise ConnectionError("Client disconnected")
                buffer += data
                
        except Exception as e:
            print(f"Error receiving from client: {str(e)}")
            raise
        
    def close_connection(self, client_socket):
        """Close a specific client connection."""
        try:
            client_info = self.connected_clients.get(client_socket)
            if client_info:
                print(f"Closing connection from {client_info.address}")
                if client_socket in self.receive_buffers:
                    del self.receive_buffers[client_socket]
                del self.connected_clients[client_socket]
            client_socket.close()
        except Exception as e:
            print(f"Error closing connection: {str(e)}")
    
    def stop_server(self):
        """Stop the server and close all connections."""
        self.is_running = False
        
        # Close all client connections
        for client_socket in list(self.connected_clients.keys()):
            self.close_connection(client_socket)
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        # Wait for accept thread to finish
        if self.accept_thread:
            self.accept_thread.join(timeout=2.0)
        
        print("Server stopped.")

    def broadcast_to_users(self, user_ids, message):
        """Broadcast a message to specific users."""
        for client_socket, client_info in self.connected_clients.items():
            if client_info.user_id in user_ids:
                try:
                    self.send_to_client(client_socket, message)
                except Exception as e:
                    print(f"Error broadcasting to user {client_info.user_id}: {e}")

# Test Cases
if __name__ == "__main__":
    print("\nStarting server for testing...")
    server = ServerConnection()
    try:
        server.start_server()
        print("Server is running. Press Ctrl+C to stop...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping server...")
    finally:
        server.stop_server()