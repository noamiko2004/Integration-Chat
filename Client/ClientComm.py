import socket
import json
from Encryption import EncryptionManager

class ClientComm:
    def __init__(self, config_path="../config.json"):
        """Initialize the client communication manager."""
        self.socket = None
        self.server_ip = None
        self.server_port = None
        self.encryption = EncryptionManager()
        import os

        # Get the absolute path of the config file
        config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config.json"))
        self.load_config(config_path)
    
    def load_config(self, config_path):
        """Load server IP and port from config.json."""
        with open(config_path, "r") as file:
            config = json.load(file)
            self.server_ip = config.get("server_ip_address")
            self.server_port = config.get("server_port")
    
    def connect(self):
        """Establish a connection with the server."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.server_ip, self.server_port))
        print(f"Connected to server at {self.server_ip}:{self.server_port}")
    
    def send_request(self, request_type, data):
        """Send a formatted request to the server."""
        request = json.dumps({"type": request_type, "data": data})
        self.socket.sendall(request.encode())
    
    def receive_response(self):
        """Wait for and handle the server's response."""
        response = self.socket.recv(4096).decode()
        return json.loads(response)
    
    def send_message(self, message):
        """Encrypt and send a message object to the server."""
        encrypted_message = self.encryption.encrypt_message(message)
        self.send_request("send_message", {"message": encrypted_message.hex()})
    
    def receive_message(self):
        """Receive a new message from the server during an active session."""
        response = self.receive_response()
        if response["type"] == "new_message":
            encrypted_message = bytes.fromhex(response["data"]["message"])
            decrypted_message = self.encryption.decrypt_message(encrypted_message)
            return decrypted_message
    
    def disconnect(self):
        """Gracefully close the connection."""
        self.socket.close()
        print("Disconnected from server.")

# Example Usage:
client = ClientComm()
client.connect()

# Test Registration
client.send_request("register", {"username": "testuser", "password": "testpass"})
response = client.receive_response()
print("Register Response:", response)

# Test Login
client.send_request("login", {"username": "testuser", "password": "testpass"})
response = client.receive_response()
print("Login Response:", response)

# Test Sending Encrypted Message
test_message = "Hello, this is a secure message!"
client.send_message(test_message)
print("Sent Encrypted Message:", test_message)

# Test Receiving Message
received_message = client.receive_message()
print("Received Decrypted Message:", received_message)

# Test Disconnecting
client.disconnect()
print("Client disconnected successfully.")
