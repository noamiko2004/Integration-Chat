import socket
import json
import threading
import time
from Encryption import EncryptionManager

class ClientComm:
    def __init__(self, config_path="../config.json"):
        self.socket = None
        self.server_ip = None
        self.server_port = None
        self.encryption = EncryptionManager()
        self.is_connected = False
        self.message_callback = None
        self.receive_thread = None
        self.response_queue = []  # Queue for responses to direct requests
        import os

        config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config.json"))
        self.load_config(config_path)
    
    def load_config(self, config_path):
        """Load server IP and port from config.json."""
        try:
            with open(config_path, "r") as file:
                config = json.load(file)
                self.server_ip = config.get("server_ip_address")
                self.server_port = config.get("server_port")
                if not self.server_ip or not self.server_port:
                    raise ValueError("Missing server configuration")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise RuntimeError(f"Failed to load configuration: {str(e)}")
    
    def connect(self):
        """Establish a connection with the server and perform secure handshake."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_ip, self.server_port))
            self.is_connected = True
            print(f"Connected to server at {self.server_ip}:{self.server_port}")
            
            # Perform secure handshake
            self._establish_secure_connection()
            
            # Start message receiving thread
            self.receive_thread = threading.Thread(target=self._receive_loop)
            self.receive_thread.daemon = True
            self.receive_thread.start()
            
            return True
        except Exception as e:
            print(f"Connection failed: {str(e)}")
            self.is_connected = False
            return False

    def _establish_secure_connection(self):
        """Perform the secure handshake protocol with the server."""
        try:
            print("Starting security handshake...")  # Debug print
            
            # 1. Generate client keys
            self.encryption.generate_keys()
            
            # 2. Send public key to server
            request = {
                "type": "key_exchange",
                "data": {
                    "client_public_key": self.encryption.get_public_key().decode()
                }
            }
            self.socket.sendall(json.dumps(request).encode())
            print("Sent key exchange request")  # Debug print
            
            # 3. Receive server's public key
            response = json.loads(self.socket.recv(4096).decode())
            print(f"Received server response: {response}")  # Debug print
            
            if response.get("type") != "key_exchange":
                raise ValueError("Invalid key exchange response")
            
            self.encryption.set_server_public_key(response["data"]["server_public_key"].encode())
            
            # 4. Generate and send session key
            session_key = self.encryption.generate_session_key()
            encrypted_session_key = self.encryption.encrypt_session_key()
            
            request = {
                "type": "session_key",
                "data": {
                    "encrypted_session_key": encrypted_session_key.hex()
                }
            }
            self.socket.sendall(json.dumps(request).encode())
            print("Sent session key")  # Debug print
            
            # 5. Wait for confirmation
            response = json.loads(self.socket.recv(4096).decode())
            print(f"Received confirmation response: {response}")  # Debug print
            
            if response.get("type") != "session_confirmed":
                raise ValueError("Session establishment failed")
            
            print("Secure connection established")
            return True
            
        except Exception as e:
            print(f"Handshake error: {str(e)}")  # Debug print
            raise RuntimeError(f"Failed to establish secure connection: {str(e)}")
        
    def send_request(self, request_type, data):
        """Send a formatted request to the server."""
        if not self.is_connected:
            raise ConnectionError("Not connected to server")
        
        try:
            request = {
                "type": request_type,
                "data": data
            }
            self.socket.sendall(json.dumps(request).encode())
            return True
        except Exception as e:
            self.is_connected = False
            raise RuntimeError(f"Failed to send request: {str(e)}")

    def receive_response(self):
        """Wait for and handle the server's response."""
        try:
            response = self.socket.recv(4096).decode()
            parsed_response = json.loads(response)
            return parsed_response['data']
        except Exception as e:
            self.is_connected = False
            raise RuntimeError(f"Failed to receive response: {str(e)}")
            
    def send_message(self, message):
        """Encrypt and send a message object to the server."""
        try:
            encrypted_message = self.encryption.encrypt_message(message)
            self.send_request("send_message", {"message": encrypted_message.hex()})
            return True
        except Exception as e:
            print(f"Failed to send message: {str(e)}")
            return False
    
    def _receive_loop(self):
        """Background thread for receiving messages."""
        while self.is_connected:
            try:
                data = self.socket.recv(4096).decode()
                if not data:
                    continue

                response = json.loads(data)
                print(f"Debug: Received in loop: {response}")  # Debug print
                
                # Handle regular chat messages
                if response.get("type") == "new_message":
                    if self.message_callback:
                        self.message_callback(response.get("data"))
                else:
                    # Store response for the main thread
                    print(f"Debug: Adding to queue: {response}")  # Debug print
                    self.response_queue.append(response)
                        
            except Exception as e:
                print(f"Error in receive loop: {str(e)}")
                self.is_connected = False
                break
            
    def set_message_callback(self, callback):
        """Set callback function for handling received messages."""
        self.message_callback = callback
    
    def disconnect(self):
        """Gracefully close the connection."""
        self.is_connected = False
        if self.socket:
            try:
                self.send_request("disconnect", {})
            except:
                pass
            self.socket.close()
        if self.receive_thread:
            self.receive_thread.join(timeout=1.0)
        print("Disconnected from server.")

    def send_register_request(self, username, password):
        """Send a registration request."""
        return self.send_request("register", {
            "username": username,
            "password": password
        })
    
    def send_login_request(self, username, password):
        """Send a login request."""
        return self.send_request("login", {
            "username": username,
            "password": password
        })

    def get_next_response(self):
        """Get the next response from the queue."""
        while self.is_connected and not self.response_queue:
            time.sleep(0.1)  # Wait for response
            
        if not self.response_queue:
            return None
            
        response = self.response_queue.pop(0)
        print(f"Debug - Raw response from queue: {response}")  # Debug print
        
        # Get the data part of the response
        response_data = response.get('data')
        if not response_data:
            return None
            
        return response_data

# Test Cases
if __name__ == "__main__":
    print("\nStarting client test...")
    client = ClientComm()
    
    def print_message(message):
        print(f"Received: {message}")
    
    try:
        # Connect and set up message handling
        if client.connect():
            client.set_message_callback(print_message)
            
            # Send a test message
            test_message = "Hello, this is a secure test message!"
            print("\nSending message:", test_message)
            client.send_message(test_message)
            
            # Keep running until user interrupts
            print("\nClient running. Press Ctrl+C to stop...")
            while True:
                time.sleep(1)
                
    except KeyboardInterrupt:
        print("\nStopping client...")
    except Exception as e:
        print(f"\nError occurred: {str(e)}")
    finally:
        if client.is_connected:
            client.disconnect()