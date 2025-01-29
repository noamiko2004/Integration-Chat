from ClientComm import ClientComm
import threading
import time
import json
import os
import sys

class ChatClient:
   def __init__(self):
      """Initialize the chat client."""
      self.client = ClientComm()
      self.session_token = None
      self.current_chat = None
      self.running = True
      self.user_id = None
      
   def display_menu(self):
      """Display the main menu options."""
      print("\n=== InteChat Menu ===")
      if not self.session_token:
         print("1. Register")
         print("2. Login")
         print("3. Exit")
      else:
         print("1. Create new chat")
         print("2. List chats")
         print("3. Join chat")
         print("4. Logout")
         print("5. Exit")
      return input("Choose an option: ")

   def start(self):
      """Start the chat client."""
      try:
         if not self.client.connect():
               print("Failed to connect to server.")
               return

         print("Connected to chat server!")
         
         while self.running:
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
                     print("Invalid choice!")
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
                  else:
                     print("Invalid choice!")
                     
      except KeyboardInterrupt:
         print("\nShutting down...")
      finally:
         self.cleanup()

   def handle_registration(self):
      """Handle user registration."""
      try:
         username = input("Enter username: ")
         password = input("Enter password: ")
         
         self.client.send_register_request(username, password)
         response = self.client.get_next_response()
         
         if response:
               if response.get('success'):
                  print("Registration successful!")
               else:
                  print(f"Registration failed: {response.get('message', 'Unknown error')}")
         else:
               print("No response received from server")
               
      except Exception as e:
         print(f"Error during registration: {e}")

   def handle_login(self):
      """Handle user login."""
      try:
         username = input("Enter username: ")
         password = input("Enter password: ")
         
         # Send login request
         self.client.send_login_request(username, password)
         
         # Wait for and process response
         response = self.client.get_next_response()
         print(f"Debug: Received login response: {response}")  # Debug print
         
         if response:
               if response.get('success'):
                  self.session_token = response.get('token')
                  print("Login successful!")
               else:
                  print(f"Login failed: {response.get('message', 'Unknown error')}")
         else:
               print("No response received from server")
               
      except Exception as e:
         print(f"Error during login: {e}")
         
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
      """Handle user logout."""
      if self.session_token:
         self.client.send_request("disconnect", {
               "token": self.session_token
         })
         self.session_token = None
         self.current_chat = None
         print("Logged out successfully!")

   def cleanup(self):
      """Clean up resources."""
      if self.session_token:
         self.handle_logout()
      if hasattr(self, 'client'):
         self.client.disconnect()

if __name__ == "__main__":
    client = ChatClient()
    client.start()