import socket
import json
import threading
import time
from Encryption import EncryptionManager

class ClientComm:
    def __init__(self, config_path="../config.json"):
        """Initialize the client communication manager."""
        self.socket = None
        self.server_ip = None
        self.server_port = None
        self.encryption = EncryptionManager()
        self.is_connected = False
        self.message_callback = None
        self.receive_thread = None
        import os

        # Get the absolute path of the config file
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
            # 1. Generate client keys
            self.encryption.generate_keys()
            
            # 2. Send public key to server
            self.send_request("key_exchange", {
                "client_public_key": self.encryption.get_public_key().decode()
            })
            
            # 3. Receive server's public key
            response = self.receive_response()
            if response["type"] != "key_exchange":
                raise ValueError("Invalid key exchange response")
            
            self.encryption.set_server_public_key(response["data"]["server_public_key"].encode())
            
            # 4. Generate and send session key
            session_key = self.encryption.generate_session_key()
            encrypted_session_key = self.encryption.encrypt_session_key()
            self.send_request("session_key", {
                "encrypted_session_key": encrypted_session_key.hex()
            })
            
            # 5. Wait for confirmation
            response = self.receive_response()
            if response["type"] != "session_confirmed":
                raise ValueError("Session establishment failed")
            
            print("Secure connection established")
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to establish secure connection: {str(e)}")
    
    def send_request(self, request_type, data):
        """Send a formatted request to the server."""
        if not self.is_connected:
            raise ConnectionError("Not connected to server")
        
        try:
            request = json.dumps({"type": request_type, "data": data})
            self.socket.sendall(request.encode())
        except Exception as e:
            self.is_connected = False
            raise RuntimeError(f"Failed to send request: {str(e)}")
    
    def receive_response(self):
        """Wait for and handle the server's response."""
        try:
            response = self.socket.recv(4096).decode()
            return json.loads(response)
        except json.JSONDecodeError:
            raise ValueError("Invalid response format")
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
                response = self.receive_response()
                # print("Received response:", response)
                
                if response["type"] == "new_message":
                    encrypted_message = bytes.fromhex(response["data"]["message"])
                    # print("Decoded hex message:", encrypted_message)
                    
                    decrypted_message = self.encryption.decrypt_message(encrypted_message)
                    print("Decrypted message:", decrypted_message)
                    
                    if self.message_callback:
                        self.message_callback(decrypted_message)
                        
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