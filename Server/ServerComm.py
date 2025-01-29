import socket
import threading
import json

class ServerConnection:
    def __init__(self, config_path="../config.json"):
        """Initialize the server connection manager."""
        self.server_socket = None
        self.connected_clients = {}  # {client_socket: client_address}
        self.server_ip = None
        self.server_port = None
        self.load_config(config_path)
    
    def load_config(self, config_path):
        """Load server IP and port from config.json."""
        import os
        config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config.json"))
        with open(config_path, "r") as file:
            config = json.load(file)
            self.server_ip = config.get("server_ip_address")
            self.server_port = config.get("server_port")
    
    def start_server(self):
        """Start the server and listen for incoming connections."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.server_ip, self.server_port))
        self.server_socket.listen(10)
        print(f"Server started on {self.server_ip}:{self.server_port}")
        
        while True:
            client_socket, client_address = self.server_socket.accept()
            self.connected_clients[client_socket] = client_address
            print(f"New connection from {client_address}")
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()
    
    def handle_client(self, client_socket):
        """Handle communication with a connected client."""
        try:
            while True:
                message = self.receive_from_client(client_socket)
                if message:
                    print(f"Received from {self.connected_clients[client_socket]}: {message}")
        except (ConnectionResetError, ConnectionAbortedError):
            print(f"Client {self.connected_clients[client_socket]} disconnected.")
            self.close_connection(client_socket)
    
    def send_to_client(self, client_socket, data):
        """Send data to a specific client."""
        client_socket.sendall(json.dumps(data).encode())
    
    def receive_from_client(self, client_socket):
        """Receive data from a client."""
        try:
            data = client_socket.recv(4096).decode()
            return json.loads(data)
        except json.JSONDecodeError:
            return None
    
    def broadcast(self, data, group_id=None):
        """Send data to all clients or a specific group."""
        for client_socket in self.connected_clients:
            self.send_to_client(client_socket, data)
    
    def close_connection(self, client_socket):
        """Gracefully handle client disconnections."""
        client_socket.close()
        del self.connected_clients[client_socket]
        print("Client connection closed.")

# Example Usage:
server = ServerConnection()
server.start_server()
