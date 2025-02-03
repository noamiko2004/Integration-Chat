from ClientComm import ClientComm
import threading
import time
import json
import os
import sys
import random
import re
from shutil import get_terminal_size

class ChatClient:
   def __init__(self):
      """Initialize the chat client."""
      self.client = ClientComm()
      self.session_token = None
      self.current_chat = None
      self.running = True
      self.user_id = None
      self.action_history = []  # Store recent actions/messages
      
   def add_to_history(self, message):
      """Add a message to action history, keeping only last 3."""
      self.action_history.append(message)
      if len(self.action_history) > 3:
         self.action_history.pop(0)
      
   def display_menu(self):
      """Display the main menu options."""
      display_menu_header()
      
      # Display recent action history
      if self.action_history:
         print("\nRecent Actions:")
         for action in self.action_history:
            print(f"  → {action}")
         print("\n" + "=" * get_terminal_size().columns + "\n")
            
      if not self.session_token:
         options = [
            "1. Register",
            "2. Login",
            "3. Exit"
         ]
      else:
         options = [
            "1. Create new chat",
            "2. List chats",
            "3. Join chat",
            "4. Logout",
            "5. Exit"
         ]
            
      # Center and display options
      padding = get_center_padding(max(len(opt) for opt in options))
      for option in options:
         print(" " * padding + option)
            
      print("\n" + "=" * get_terminal_size().columns)
      choice = input("\nChoose an option: ")
        
      # Handle invalid input immediately
      if not self.session_token and choice not in ["1", "2", "3"]:
         self.add_to_history(f"Invalid option '{choice}' selected")
         return choice
      elif self.session_token and choice not in ["1", "2", "3", "4", "5"]:
         self.add_to_history(f"Invalid option '{choice}' selected")
         return choice
            
      return choice

   def start(self):
      """Start the chat client."""
      try:
         clear_screen()
         
         # Initial splash screen
         logo_path = os.path.join(os.path.dirname(__file__), 'assets', 'LogoBanner.txt')
         logo_banner = read_file_content(logo_path)
         display_centered_banner(logo_banner)
         print("\n" * 2)
         title_banner = get_random_title_banner()
         display_centered_banner(title_banner)
         
         # Keep splash screen for 3 seconds
         time.sleep(3)
         
         if not self.client.connect():
               print("Failed to connect to server.")
               return

         self.add_to_history("Connected to chat server!")
         time.sleep(0.5)
         clear_screen()
         
         # Store a title banner to use consistently
         self.menu_title_banner = get_random_title_banner()
         
         while self.running:
            clear_screen()
            print("\n")
            display_centered_banner(self.menu_title_banner)
            choice = self.display_menu()
            
            if not self.session_token:
               # Not logged in menu
               if choice == "1":
                  self.handle_registration()
               elif choice == "2":
                  self.handle_login()
               elif choice == "3":
                  self.running = False
            else:
               # Logged in menu
               if choice == "1":
                  self.handle_create_chat()
               elif choice == "2":
                  self.list_chats()
               elif choice == "3":
                  self.handle_join_chat()
               elif choice == "4":
                  self.handle_logout()
               elif choice == "5":
                  self.running = False
                        
      except KeyboardInterrupt:
         print("\nShutting down...")
      finally:
         self.cleanup()

   def validate_username(self, username):
      """Client-side username validation."""
      
      if len(username) < 4:
         return False, "Username is too short (minimum 4 characters)"
      if len(username) > 20:
         return False, "Username is too long (maximum 20 characters)"
      if not re.match(r'^[a-zA-Z0-9!@#$%]+$', username):
         return False, "Username can only contain English letters, numbers, and special characters (!@#$%)"
      
      return True, "Username is valid"

   def validate_password(self, password):
      """Client-side password validation."""
      
      if len(password) < 8:
         return False, "Password is too short (minimum 8 characters)"
      if len(password) > 100:
         return False, "Password is too long (maximum 100 characters)"
      if not re.match(r'^[a-zA-Z0-9!@#$%^&*()_+\-=\[\]{};:,.<>?]+$', password):
         return False, "Password can only contain English letters, numbers, and special characters"
      
      return True, "Password is valid"


   def handle_registration(self):
      """Handle user registration with validation."""
      try:
         while True:
            username = input("Enter username (4-20 characters, letters, numbers, !@#$%): ")
            is_valid, message = self.validate_username(username)
            if not is_valid:
               self.add_to_history(message)
               continue
               
            password = input("Enter password (8-100 characters, letters, numbers, special characters): ")
            is_valid, message = self.validate_password(password)
            if not is_valid:
               self.add_to_history(message)
               continue
               
            break
         
         self.client.send_register_request(username, password)
         response = self.client.get_next_response()
         
         # Debug print to see exact response
         print(f"Debug - Registration response: {response}")
         
         if response:
            success = response.get('success', False)
            message = response.get('message', 'Unknown error')
            
            if success:
               self.add_to_history(f"Successfully registered user: {username}")
            else:
               self.add_to_history(f"Registration failed: {message}")
               return  # Exit the function if registration failed
         else:
            self.add_to_history("No response received from server")
               
      except Exception as e:
         self.add_to_history(f"Error during registration: {e}")

   def handle_login(self):
      """Handle user login."""
      try:
         username = input("Enter username: ")
         password = input("Enter password: ")
         
         self.client.send_login_request(username, password)
         response = self.client.get_next_response()
         
         if response:
            if response.get('success'):
                  self.session_token = response.get('token')
                  self.add_to_history(f"Successfully logged in as: {username}")
            else:
                  self.add_to_history(f"Login failed: {response.get('message', 'Unknown error')}")
         else:
            self.add_to_history("No response received from server")
            
      except Exception as e:
         self.add_to_history(f"Error during login: {e}")
         
   def handle_create_chat(self):
      """Handle chat creation."""
      chat_type = input("Enter chat type (private/group): ").lower()
      if chat_type not in ['private', 'group']:
         print("Invalid chat type!")
         return
         
      participants = input("Enter participant usernames (comma-separated): ").split(',')
      participants = [p.strip() for p in participants if p.strip()]
      
      self.client.send_request("create_chat", {
         "token": self.session_token,
         "type": chat_type,
         "participants": participants
      })
      
      response = self.client.receive_response()
      if response.get("success"):
         print(f"Chat created! Chat ID: {response.get('chat_id')}")
      else:
         print(f"Failed to create chat: {response.get('message', 'Unknown error')}")

   def list_chats(self):
      """List all user's chats."""
      self.client.send_request("get_chats", {
         "token": self.session_token
      })
      
      response = self.client.receive_response()
      if response.get("success"):
         chats = response.get("chats", [])
         if not chats:
               print("No active chats.")
               return
               
         print("\n=== Your Chats ===")
         for chat in chats:
               print(f"Chat ID: {chat['chat_id']}")
               print(f"Type: {chat['chat_type']}")
               print(f"Participants: {', '.join(str(p) for p in chat['participants'])}")
               print("-" * 20)
      else:
         print(f"Failed to get chats: {response.get('message', 'Unknown error')}")

   def handle_join_chat(self):
      """Handle joining a chat."""
      chat_id = input("Enter chat ID to join: ")
      try:
         chat_id = int(chat_id)
      except ValueError:
         print("Invalid chat ID!")
         return
         
      self.current_chat = chat_id
      print(f"Joined chat {chat_id}. Type /exit to leave, /help for commands.")
      
      # Get chat history
      self.client.send_request("get_messages", {
         "token": self.session_token,
         "chat_id": chat_id
      })
      
      response = self.client.receive_response()
      if response.get("success"):
         messages = response.get("messages", [])
         print("\n=== Chat History ===")
         for msg in messages:
               print(f"User {msg['sender_id']}: {msg['content']}")
         print("=" * 20)
      
      # Enter chat loop
      self.chat_loop()

   def chat_loop(self):
      """Handle sending and receiving messages in a chat."""
      while self.current_chat:
         try:
               message = input()
               
               if message.lower() == '/exit':
                  self.current_chat = None
                  break
               elif message.lower() == '/help':
                  print("Available commands:")
                  print("/exit - Leave the chat")
                  print("/help - Show this message")
                  continue
               
               if message:
                  self.client.send_request("send_message", {
                     "token": self.session_token,
                     "chat_id": self.current_chat,
                     "content": message
                  })
                  
         except KeyboardInterrupt:
               self.current_chat = None
               break

   def handle_incoming_message(self, message):
      """Handle incoming messages from the server."""
      try:
         if isinstance(message, dict):
               # Handle structured messages
               if 'success' in message:
                  print(f"Server response: {message.get('message', 'No message provided')}")
               else:
                  # Handle chat messages
                  sender_id = message.get('sender_id', 'Unknown')
                  content = message.get('content', '')
                  print(f"\nUser {sender_id}: {content}")
         else:
               print(f"\nReceived: {message}")
         
         # Reprint input prompt if in chat
         if self.current_chat:
               print("> ", end='', flush=True)
      except Exception as e:
         print(f"Error handling message: {e}")

   def handle_logout(self):
      """Handle user logout and reset client state."""
      if self.session_token:
         self.client.send_request("disconnect", {
            "token": self.session_token
         })
         
         # Reset ALL client state
         self.session_token = None
         self.current_chat = None
         self.client = ClientComm()  # Create fresh client instance
         self.client.connect()  # Reconnect with fresh state
         self.add_to_history("Successfully logged out")

   def cleanup(self):
      """Clean up resources."""
      if self.session_token:
         self.handle_logout()
      if hasattr(self, 'client'):
         self.client.disconnect()

def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def get_center_padding(text_width):
    """Get padding needed to center text."""
    terminal_width = get_terminal_size().columns
    return max(0, (terminal_width - text_width) // 2)

def read_file_content(filepath):
    """Read and return file content."""
    try:
        with open(filepath, 'r') as file:
            return file.read()
    except Exception as e:
        print(f"Error reading file {filepath}: {e}")
        return ""

def display_centered_banner(banner_text):
    """Display banner text centered on screen."""
    lines = banner_text.split('\n')
    max_width = max(len(line) for line in lines)
    padding = get_center_padding(max_width)
    
    for line in lines:
        print(' ' * padding + line)

def get_random_title_banner():
    """Get a random title banner from the TitleBanners folder."""
    banner_dir = os.path.join(os.path.dirname(__file__), 'assets', 'TitleBanners')
    banner_files = [f for f in os.listdir(banner_dir) if f.startswith('TitleBanner')]
    if banner_files:
        chosen_banner = random.choice(banner_files)
        return read_file_content(os.path.join(banner_dir, chosen_banner))
    return ""

def display_menu_header():
    """Display the menu header with decorative elements."""
    terminal_width = get_terminal_size().columns
    print("\n" + "=" * terminal_width)
    padding = get_center_padding(len("InteChat Menu"))
    print(" " * padding + "InteChat Menu")
    print("=" * terminal_width + "\n")


if __name__ == "__main__":
    client = ChatClient()
    client.start()