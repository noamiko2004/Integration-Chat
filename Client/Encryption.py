"""
Encryption.py

Handles all encryption and decryption tasks to ensure secure communication.

Responsibilities:
1. Generate and manage public/private key pairs for encryption.
2. Encrypt outgoing messages before sending them to the server.
3. Decrypt incoming messages received from the server.

Key Classes:
- EncryptionManager: Manages keys and provides encryption and decryption functions.

Key Functions:
- generate_keys(): Generate RSA public/private key pairs.
- get_public_key(): Return the client's public key for sharing with the server.
- encrypt_message(message, public_key): Encrypt a message using the server's or recipient's public key.
- decrypt_message(encrypted_message): Decrypt a received message using the private key.

Key Variables:
- private_key: The client's private key used for decryption.
- public_key: The client's public key shared with the server for encryption.
- server_public_key: The server's public key, used to encrypt sensitive data sent to the server.
"""
