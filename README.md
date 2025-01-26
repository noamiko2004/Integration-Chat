![InteChat Logo](client/assets/InteChatLogo.png)

# **Integration-Chat: InteChat**

Welcome to **InteChat**, a secure, fast, and reliable multi-user chat system! With InteChat, users can seamlessly connect with others in private chats or groups, enjoying end-to-end encryption and robust features.

---

## **Features**

- **Multi-User Chat**: Chat with other users or join groups to collaborate.
- **Secure Communication**: Messages are encrypted for your privacy.
- **User Authentication**: Register with a unique username and safely stored password.
- **Chat History**: Messages are logged with timestamps and usernames, retrievable on demand.
- **CLI-Based Interface**: A lightweight and intuitive command-line interface.

---

## **System Overview**

InteChat is designed with a clear separation between the **Client** and **Server** to ensure scalability and modularity.

### **Client Side**

- Simple CLI for user interactions (register, login, chat).
- Encrypts messages before sending them to the server.
- Displays chat history loaded dynamically from the server.

### **Server Side**

- Manages user registration and authentication.
- Handles chat message storage and retrieval.
- Ensures real-time communication between clients.

---

## **How It Works**

1. **Register**: Users create an account with a unique username.
2. **Login**: Authenticate with secure credentials.
3. **Start Chatting**:
   - Private Chats: Send direct messages to another user.
   - Group Chats: Create or join groups for collaborative discussions.
4. **Message Handling**:
   - Messages include the date, time, sender's username, and content.
   - Chat history is stored and managed by the server.

---

## **Security Features**

- **Encryption**: All messages are encrypted using RSA.
- **Hashed Passwords**: User passwords are hashed with bcrypt for secure storage.
- **Session Management**: Session tokens ensure secure and authenticated communication.

---

## **Directory Structure**

```
project/
├── config.json                # Global configuration settings
├── client/                    # Client-side code
│   ├── assets/                # Visual and branding assets
│   ├── main.py                # Entry point for the client
│   ├── ClientComm.py          # Handles client-server communication
│   ├── Encryption.py          # Manages encryption for secure messaging
├── server/                    # Server-side code
│   ├── storage/               # Persistent storage for chats and users
│   │   ├── messages/          # Chat logs
│   │   ├── chat_database.db   # SQLite database
│   ├── logs/                  # Server logs
│   ├── main.py                # Entry point for the server
│   ├── ServerComm.py          # Manages client connections
│   ├── UserManager.py         # Handles user authentication
│   ├── MessageHandler.py      # Manages chat history
│   ├── Encryption.py          # Manages encryption on the server
```

---

## **Setup and Usage**

### **1. Prerequisites**

- Python 3.10+
- Required Python libraries (install via `requirements.txt`):
  ```bash
  pip install -r requirements.txt
  ```

### **2. Run the Server**

1. Navigate to the `server/` directory.
2. Start the server:
   ```bash
   python main.py
   ```

### **3. Run the Client**

1. Navigate to the `client/` directory.
2. Start the client:
   ```bash
   python main.py
   ```

### **4. Begin Chatting**

Follow the menu prompts in the client CLI to register, log in, and chat!

---

## **Future Enhancements**

- File sharing between users.
- Emoji support and text formatting in chats.
- Mobile-friendly GUI for enhanced usability.
- Cloud-based deployment for scalability.

---

## **Contributing**

Contributions are welcome! Feel free to open issues or submit pull requests. Let’s make InteChat even better together!

---

## **License**

This project is licensed under the [MIT License](LICENSE).

