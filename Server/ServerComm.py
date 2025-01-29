import socket
import threading
import json
import time
from Encryption import EncryptionManager

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
                    
                    if message_type in ['register', 'login', 'create_chat', 'send_message', 
                                    'get_chats', 'get_messages', 'disconnect']:
                        # Process the request
                        response = self.process_request(message_type, client_socket, data.get('data', {}))
                        # Send response back to client
                        self.send_to_client(client_socket, response)
                    else:
                        print(f"Unknown message type: {message_type}")

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
    
    def _handle_client_message(self, client_socket, data):
        """Handle messages from an authenticated client."""
        client_info = self.connected_clients[client_socket]
        
        try:
            if data["type"] == "send_message":
                # Decrypt the message
                encrypted_message = bytes.fromhex(data["data"]["message"])
                decrypted_message = self.encryption.decrypt_message(
                    encrypted_message, 
                    client_info.client_id
                )
                print(f"Message from {client_info.address}: {decrypted_message}")
                
                # Message received - in actual chat app, this is where 
                # we would handle message routing to other clients
                
            elif data["type"] == "disconnect":
                raise ConnectionError("Client requested disconnect")
                
        except Exception as e:
            print(f"Error handling message: {str(e)}")
            raise
        
    def send_to_client(self, client_socket, data):
        """Send data to a specific client."""
        try:
            client_socket.sendall(json.dumps(data).encode())
        except Exception as e:
            print(f"Error sending to client: {str(e)}")
            raise    

    def receive_from_client(self, client_socket):
        """Receive data from a client."""
        try:
            data = client_socket.recv(4096).decode()
            if not data:
                raise ConnectionError("Client disconnected")
            return json.loads(data)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON received: {str(e)}")
            raise
        except Exception as e:
            print(f"Error receiving from client: {str(e)}")
            raise
        
    def close_connection(self, client_socket):
        """Close a specific client connection."""
        try:
            client_info = self.connected_clients.get(client_socket)
            if client_info:
                print(f"Closing connection from {client_info.address}")
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