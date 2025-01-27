"""
Encryption.py

Handles encryption and decryption to ensure secure communication with the server.

Responsibilities:
1. Generate the client's RSA public/private key pair.
2. Receive and store the server's public key.
3. Generate a session key and encrypt it using the server's public key.
4. Encrypt and decrypt messages using AES for secure communication.

Key Classes:
- EncryptionManager: Manages RSA and AES operations.

Key Functions:
- generate_keys(): Generate RSA public and private keys for the client.
- get_public_key(): Return the client's public key for optional use.
- set_server_public_key(server_public_key_pem): Store the server's public key.
- generate_session_key(): Generate a random session key for AES encryption.
- encrypt_session_key(): Encrypt the session key with the server's public key.
- encrypt_message(message): Encrypt a message using the session key (AES).
- decrypt_message(encrypted_message): Decrypt a message using the session key (AES).

Key Variables:
- private_key: The client's private RSA key for optional decryption.
- public_key: The client's public RSA key for sharing with the server.
- server_public_key: The server's public key for encrypting the session key.
- session_key: The AES session key used for encrypting/decrypting chat messages.
"""
