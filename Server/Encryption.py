"""
Encryption.py

Handles encryption and decryption to ensure secure communication between the server and clients.

Responsibilities:
1. Generate and manage the server's RSA public/private key pair.
2. Decrypt incoming session keys from clients using the private key.
3. Encrypt outgoing messages to clients using their public keys.
4. Store and manage session keys for each connected client.

Key Classes:
- EncryptionManager: Manages RSA and AES operations.

Key Functions:
- generate_keys(): Generate RSA public and private keys for the server.
- get_public_key(): Return the server's public key for sharing with clients.
- decrypt_session_key(encrypted_key): Decrypt a session key sent by a client.
- store_client_session_key(client_id, session_key): Store the session key for a specific client.
- encrypt_message(message, client_id): Encrypt a message using a client’s session key (AES).
- decrypt_message(encrypted_message, client_id): Decrypt a message using a client’s session key (AES).

Key Variables:
- private_key: The server's private RSA key for decryption.
- public_key: The server's public RSA key for sharing with clients.
- client_session_keys: Dictionary mapping client IDs to their AES session keys.
"""
