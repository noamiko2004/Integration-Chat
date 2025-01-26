"""
Encryption.py

Handles encryption and decryption to ensure secure communication between the server and clients.

Responsibilities:
1. Generate and manage the server's RSA public/private key pair.
2. Decrypt incoming messages from clients using the private key.
3. Encrypt outgoing messages to clients using their public keys.

Key Classes:
- EncryptionManager: Manages key generation, encryption, and decryption.

Key Functions:
- generate_keys(): Generate RSA public and private keys.
- get_public_key(): Return the server's public key for sharing with clients.
- encrypt_message(message, public_key): Encrypt a message using a client's public key.
- decrypt_message(encrypted_message): Decrypt a message using the server's private key.

Key Variables:
- private_key: The server's private key for decryption.
- public_key: The server's public key for sharing with clients.
"""
