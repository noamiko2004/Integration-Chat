# **InteChat** - Secure Private Messaging

![InteChat Logo](Client/Assets/InteChatLogo.png)

Welcome to **InteChat**, a lightweight and secure private messaging system built with Python. InteChat offers end-to-end encrypted communication in a clean, terminal-based interface.

## **✨ Key Features**

- **🔒 End-to-End Encryption**: All messages are secured using RSA encryption
- **👥 Private Messaging**: Direct, secure communication between users
- **📜 Message History**: Access your chat history anytime
- **⚡ Real-time Updates**: Instant message delivery
- **🎯 Clean Interface**: Intuitive terminal-based UI with visual indicators
- **🛡️ Secure Authentication**: bcrypt-hashed passwords and session tokens

## **🚀 Quick Start**

### Prerequisites
- Python 3.10 or higher
- pip package manager

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/noamiko2004/Integration-Chat.git
   cd Integration-Chat
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv .venv
   # On Windows:
   .venv\Scripts\activate
   # On Unix or MacOS:
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

1. Start the server:
   ```bash
   cd server
   python main.py
   ```

2. In a new terminal, start the client:
   ```bash
   cd client
   python main.py
   ```

## **💡 Usage Guide**

### First Time Setup
1. Choose "Register" from the main menu
2. Create your account with a username (4-20 characters) and password (8+ characters)
3. Log in with your credentials

### Starting a Chat
1. Select "Start Chat" from the menu
2. Enter the username of the person you want to chat with
3. Start messaging!

### Navigation
- Type `/exit` to leave a chat
- Arrow keys to navigate input
- Messages from you appear with "→"
- Messages from others appear with "←"

## **🏗️ Project Structure**

```
Integration-Chat/
├── config.json              # Server configuration
├── requirements.txt         # Project dependencies
├── client/
│   ├── assets/             # Logos and banners
│   ├── main.py             # Client entry point
│   ├── ClientComm.py       # Client networking
│   ├── chat_input.py       # Input handling
│   └── Encryption.py       # Client-side encryption
└── server/
    ├── main.py             # Server entry point
    ├── ServerComm.py       # Connection handling
    ├── MessageHandler.py   # Chat management
    ├── UserManager.py      # User authentication
    ├── Encryption.py       # Server-side encryption
    └── storage/            # Database storage
```

## **🔐 Security Features**

- **Password Security**: 
  - Passwords are hashed using bcrypt
  - Never stored in plaintext
  - Client-side length and complexity validation

- **Communication Security**:
  - RSA encryption for key exchange
  - Session-based encryption
  - Secure message framing

- **Session Management**:
  - Unique session tokens for each login
  - Automatic session cleanup
  - Protected against session hijacking

## **🌟 Feature Highlights**

### Real-time Chat Display
```
=== Chat with alice ===
[2025-02-04 15:30:22] → bob: Hey Alice!
[2025-02-04 15:30:25] ← alice: Hi Bob, how are you?
[2025-02-04 15:30:30] → bob: I'm good, thanks!
==================================================
```

### Active Chats View
```
┌───────────────────────────────────┐
│ Chat ID: 1                        │
│ Participants: alice, bob          │
│ Last Message: [15:30:30] bob: I'm good, thanks! │
└───────────────────────────────────┘
```

## **🛠️ Technical Details**

- **Network Protocol**: TCP with custom message framing
- **Database**: SQLite3 for persistent storage
- **Encryption**: RSA + Session-based encryption
- **Interface**: Pure Python terminal UI
- **Message Format**: JSON-based protocol

## **📄 License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
