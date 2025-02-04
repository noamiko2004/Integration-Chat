import socket
import json
import threading
import time
from datetime import datetime
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
        self.response_queue = []
        self.receive_buffer = ""
        self.shutting_down = False  # Add flag for clean shutdown
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
        if self.shutting_down:
            return False
            
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
            print("Starting security handshake...")
            
            # 1. Generate client keys
            self.encryption.generate_keys()
            
            # 2. Send public key to server with framing
            request = {
                "type": "key_exchange",
                "data": {
                    "client_public_key": self.encryption.get_public_key().decode()
                }
            }
            json_data = json.dumps(request)
            frame = f"{len(json_data)}::{json_data}"
            self.socket.sendall(frame.encode())
            
            # 3. Receive server's public key (using framed message handling)
            response = self._receive_one_message()
            if response.get("type") != "key_exchange":
                raise ValueError("Invalid key exchange response")
            
            self.encryption.set_server_public_key(response["data"]["server_public_key"].encode())
            
            # 4. Generate and send session key with framing
            session_key = self.encryption.generate_session_key()
            encrypted_session_key = self.encryption.encrypt_session_key()
            
            request = {
                "type": "session_key",
                "data": {
                    "encrypted_session_key": encrypted_session_key.hex()
                }
            }
            json_data = json.dumps(request)
            frame = f"{len(json_data)}::{json_data}"
            self.socket.sendall(frame.encode())
            
            # 5. Wait for confirmation (using framed message handling)
            response = self._receive_one_message()
            if response.get("type") != "session_confirmed":
                raise ValueError("Session establishment failed")
            
            print("Secure connection established")
            return True
            
        except Exception as e:
            print(f"Handshake error: {str(e)}")
            raise RuntimeError(f"Failed to establish secure connection: {str(e)}")
        
    def _receive_one_message(self):
        """Receive exactly one complete framed message."""
        buffer = ""
        while True:
            data = self.socket.recv(4096).decode()
            if not data:
                raise ConnectionError("Server disconnected")
                
            buffer += data
            
            if '::' in buffer:
                length_str, rest = buffer.split('::', 1)
                try:
                    length = int(length_str)
                except ValueError:
                    buffer = ""
                    continue
                    
                if len(rest) >= length:
                    message = rest[:length]
                    return json.loads(message)


    def send_request(self, request_type, data):
        """Send a formatted request to the server."""
        if self.shutting_down:
            return False
            
        if not self.is_connected:
            # Only try to reconnect if we're not shutting down
            if not self.shutting_down and not self.reconnect():
                raise ConnectionError("Not connected to server")
        
        try:
            request = {
                "type": request_type,
                "data": data
            }
            json_data = json.dumps(request)
            frame = f"{len(json_data)}::{json_data}"
            self.socket.sendall(frame.encode())
            return True
        except Exception as e:
            if not self.shutting_down:
                self.is_connected = False
            raise RuntimeError(f"Failed to send request: {str(e)}")
    
    def reconnect(self):
        """Attempt to reconnect to the server."""
        if self.shutting_down:
            return False
            
        try:
            print("Attempting to reconnect to server...")
            self.disconnect()  # Clean up old connection
            self.shutting_down = False  # Reset shutdown flag for new connection
            return self.connect()
        except Exception as e:
            print(f"Reconnection failed: {e}")
            return False

    def receive_response(self):
        """Wait for and handle the server's response."""
        try:
            response = self.socket.recv(4096).decode()
            parsed_response = json.loads(response)
            return parsed_response['data']
        except Exception as e:
            self.is_connected = False
            raise RuntimeError(f"Failed to receive response: {str(e)}")
            
    def send_message(self, message_data):
        """Send a message object to the server."""
        try:
            # Ensure message has timestamp
            if isinstance(message_data, dict):
                if 'timestamp' not in message_data:
                    message_data['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            self.send_request("send_message", message_data)
            return True
        except Exception as e:
            print(f"Failed to send message: {str(e)}")
            return False
    
    def _receive_message(self):
        """Receive a complete message with framing."""
        while self.is_connected:
            try:
                # Read data into buffer
                data = self.socket.recv(4096).decode()
                if not data:
                    continue
                
                self.receive_buffer += data
                
                # Process all complete messages in buffer
                while '::' in self.receive_buffer:
                    # Find the message length and content
                    length_str, rest = self.receive_buffer.split('::', 1)
                    try:
                        length = int(length_str)
                    except ValueError:
                        # Invalid length prefix, clear buffer and continue
                        self.receive_buffer = ""
                        break
                    
                    # Check if we have a complete message
                    if len(rest) >= length:
                        message = rest[:length]
                        self.receive_buffer = rest[length:]  # Keep remaining data
                        
                        try:
                            # Parse and handle the message
                            response = json.loads(message)
                            if response.get("type") == "new_message":
                                if self.message_callback:
                                    self.message_callback(response)
                            else:
                                self.response_queue.append(response)
                        except json.JSONDecodeError as e:
                            print(f"Error decoding message: {e}")
                    else:
                        # Incomplete message, wait for more data
                        break
                        
            except Exception as e:
                print(f"Error in receive loop: {e}")
                self.is_connected = False
                break

    def _receive_loop(self):
        """Background thread for receiving messages."""
        while self.is_connected and not self.shutting_down:
            try:
                self._receive_message()
            except Exception as e:
                if not self.shutting_down:
                    print(f"Error in receive loop: {e}")
                    self.is_connected = False
                break
            
    def set_message_callback(self, callback):
        """Set callback function for handling received messages."""
        self.message_callback = callback
    
    def disconnect(self):
        """Gracefully close the connection."""
        self.shutting_down = True  # Set shutdown flag first
        self.is_connected = False
        
        if self.socket:
            try:
                # Send disconnect request only if we were connected
                if not self.socket._closed:
                    try:
                        self.send_request("disconnect", {})
                    except:
                        pass
                self.socket.close()
            except:
                pass
        
        # Wait for receive thread to finish with a short timeout
        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join(timeout=1.0)
        
        # Clear any remaining state
        self.receive_buffer = ""
        self.response_queue.clear()
        self.message_callback = None
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
        """Get the next response from the queue with timeout."""
        if self.shutting_down:
            return None
            
        start_time = time.time()
        timeout = 5.0  # 5 second timeout
        
        while self.is_connected and not self.response_queue and (time.time() - start_time) < timeout:
            time.sleep(0.1)  # Wait for response
            
        if not self.response_queue:
            if not self.is_connected and not self.shutting_down:
                raise ConnectionError("Not connected to server")
            return None
            
        try:
            response = self.response_queue.pop(0)
            if isinstance(response, dict):
                return response.get('data', {})
            return {}
        except IndexError:
            return None

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