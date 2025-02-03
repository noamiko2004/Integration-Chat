from Encryption import EncryptionManager
from UserManager import UserManager
import sqlite3
from datetime import datetime
import json

class MessageHandler:
    def __init__(self, user_manager):
        """Initialize MessageHandler with UserManager instance."""
        self.user_manager = user_manager
        self.encryption = EncryptionManager()
        self.pending_messages = {}  # Store messages for offline users

    def create_chat(self, creator_id, participants, chat_type='private'):
        """
        Create a new chat.
        
        Args:
            creator_id: User ID of chat creator
            participants: List of user IDs to include in chat
            chat_type: Either 'private' or 'group'
            
        Returns:
            (success, result): Tuple with bool success and chat_id or error message
        """
        # Validate chat type
        if chat_type not in ['private', 'group']:
            return False, "Invalid chat type"
            
        # For private chats, ensure exactly 2 participants
        if chat_type == 'private' and len(participants) != 2:
            return False, "Private chats must have exactly 2 participants"
            
        # Ensure creator is in participants
        if creator_id not in participants:
            participants.append(creator_id)
            
        # Create chat using UserManager
        success, result = self.user_manager.create_chat(participants, chat_type)
        
        if success:
            # Initialize pending messages for this chat
            self.pending_messages[result] = []
            
        return success, result

    def save_message(self, chat_id, sender_id, content, encryption_keys=None):
        """
        Save an encrypted message to the database.
        
        Args:
            chat_id: ID of the chat
            sender_id: ID of the message sender
            content: Message content to encrypt
            encryption_keys: Dict of user_id: session_key for encryption
            
        Returns:
            (success, result): Tuple with bool success and message_id or error message
        """
        try:
            # Verify sender is in chat
            is_member = self._verify_chat_membership(chat_id, sender_id)
            if not is_member:
                return False, "Sender is not a member of this chat"

            # Get chat participants for encryption
            participants = self._get_chat_participants(chat_id)
            if not participants:
                return False, "Failed to get chat participants"

            # Store the base message
            success, message_id = self.user_manager.store_message(
                chat_id, 
                sender_id, 
                content
            )
            
            if not success:
                return False, "Failed to store message"

            # Add to pending messages if needed
            self._handle_pending_message(chat_id, message_id, sender_id, content)

            return True, message_id

        except Exception as e:
            return False, f"Error saving message: {str(e)}"

    def fetch_chat_history(self, chat_id, user_id, limit=50):
        """
        Retrieve chat history for a specific chat.
        
        Args:
            chat_id: ID of the chat
            user_id: ID of user requesting history
            limit: Maximum number of messages to retrieve
            
        Returns:
            (success, result): Tuple with bool success and list of messages or error message
        """
        try:
            # Verify user is in chat
            if not self._verify_chat_membership(chat_id, user_id):
                return False, "User is not a member of this chat"

            # Get messages using UserManager with a reasonable limit
            limit = min(50, limit)  # Cap at 50 messages
            success, messages = self.user_manager.get_chat_messages(chat_id, user_id, limit)
            
            if not success:
                return False, "Failed to fetch messages"

            # Format messages for client
            formatted_messages = []
            for msg in messages:
                formatted_messages.append({
                    'message_id': msg['message_id'],
                    'username': msg.get('username', 'Unknown'),  # Add default value
                    'content': msg['message_content'],
                    'timestamp': msg['timestamp']
                })

            return True, formatted_messages[-50:]  # Return only the last 50 messages

        except Exception as e:
            return False, f"Error fetching chat history: {str(e)}"

    def get_user_chats(self, user_id):
        """
        Get all chats for a user.
        
        Args:
            user_id: ID of user
            
        Returns:
            List of chat information dictionaries
        """
        try:
            chats = self.user_manager.get_user_chats(user_id)
            formatted_chats = []
            
            for chat in chats:
                # Get chat participants
                participants = self._get_chat_participants(chat['chat_id'])
                
                formatted_chats.append({
                    'chat_id': chat['chat_id'],
                    'chat_type': chat['chat_type'],
                    'created_at': chat['created_at'],
                    'participants': participants
                })
            
            return formatted_chats

        except Exception as e:
            print(f"Error getting user chats: {e}")
            return []

    def _verify_chat_membership(self, chat_id, user_id):
        """Verify a user is a member of a chat."""
        try:
            cursor = self.user_manager.conn.cursor()
            cursor.execute('''
                SELECT 1 FROM chat_members 
                WHERE chat_id = ? AND user_id = ?
            ''', (chat_id, user_id))
            return cursor.fetchone() is not None
        except sqlite3.Error:
            return False

    def _get_chat_participants(self, chat_id):
        """Get list of participant IDs for a chat."""
        try:
            cursor = self.user_manager.conn.cursor()
            cursor.execute('''
                SELECT user_id FROM chat_members 
                WHERE chat_id = ?
            ''', (chat_id,))
            return [row['user_id'] for row in cursor.fetchall()]
        except sqlite3.Error:
            return []

    def _handle_pending_message(self, chat_id, message_id, sender_id, content):
        """Store message for offline participants."""
        if chat_id not in self.pending_messages:
            self.pending_messages[chat_id] = []
            
        self.pending_messages[chat_id].append({
            'message_id': message_id,
            'sender_id': sender_id,
            'content': content,
            'timestamp': datetime.now().isoformat()
        })
        
        # Limit pending messages queue
        if len(self.pending_messages[chat_id]) > 100:  # Keep last 100 messages
            self.pending_messages[chat_id] = self.pending_messages[chat_id][-100:]

    def get_pending_messages(self, chat_id, user_id):
        """
        Get pending messages for a user in a chat.
        
        Args:
            chat_id: ID of the chat
            user_id: ID of user requesting messages
            
        Returns:
            List of pending messages
        """
        if not self._verify_chat_membership(chat_id, user_id):
            return []
            
        return self.pending_messages.get(chat_id, [])

    def clear_pending_messages(self, chat_id, user_id):
        """Clear pending messages for a user after they've been delivered."""
        if chat_id in self.pending_messages and self._verify_chat_membership(chat_id, user_id):
            self.pending_messages[chat_id] = []

# Example usage and testing
if __name__ == "__main__":
    user_manager = UserManager()
    message_handler = MessageHandler(user_manager)
    
    try:
        # Test user creation
        success, msg = user_manager.register_user("alice", "password123")
        print(f"Created user Alice: {msg}")
        success, msg = user_manager.register_user("bob", "password123")
        print(f"Created user Bob: {msg}")
        
        # Test authentication
        success, msg, alice_token = user_manager.authenticate_user("alice", "password123")
        print(f"Alice authentication: {msg}")
        is_valid, alice_id = user_manager.validate_session(alice_token)
        print(f"Alice session valid: {is_valid}, ID: {alice_id}")
        
        success, msg, bob_token = user_manager.authenticate_user("bob", "password123")
        print(f"Bob authentication: {msg}")
        is_valid, bob_id = user_manager.validate_session(bob_token)
        print(f"Bob session valid: {is_valid}, ID: {bob_id}")
        
        if is_valid and alice_id and bob_id:
            # Test chat creation
            success, chat_id = message_handler.create_chat(
                alice_id, 
                [alice_id, bob_id], 
                'private'
            )
            print(f"Created chat: {success}, ID: {chat_id}")
            
            # Test message sending
            if success:
                success, msg_id = message_handler.save_message(
                    chat_id,
                    alice_id,
                    "Hello Bob! This is an encrypted message."
                )
                print(f"Sent message: {success}, ID: {msg_id}")
                
                # Test message retrieval
                success, messages = message_handler.fetch_chat_history(chat_id, bob_id)
                print("Chat history:")
                if success:
                    for msg in messages:
                        print(f"- {msg['content']} (from user {msg['sender_id']})")
                else:
                    print(f"Error fetching chat history: {messages}")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()
    finally:
        user_manager.close()