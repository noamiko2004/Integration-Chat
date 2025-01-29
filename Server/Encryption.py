from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import os

class EncryptionManager:
    def __init__(self):
        self.private_key = None
        self.public_key = None
        self.client_session_keys = {}  # Maps client IDs to their AES session keys

    def generate_keys(self):
        """Generate RSA public and private keys for the server."""
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        self.public_key = self.private_key.public_key()

    def get_public_key(self):
        """Return the server's public key in PEM format."""
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

    def decrypt_session_key(self, encrypted_key):
        """Decrypt a session key sent by a client."""
        return self.private_key.decrypt(
            encrypted_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

    def store_client_session_key(self, client_id, session_key):
        """Store the session key for a specific client."""
        self.client_session_keys[client_id] = session_key

    def encrypt_message(self, message, client_id):
        """Encrypt a message using a client’s session key (AES)."""
        session_key = self.client_session_keys.get(client_id)
        if not session_key:
            raise ValueError(f"No session key found for client ID: {client_id}")

        iv = os.urandom(16)  # Initialization vector
        cipher = Cipher(algorithms.AES(session_key), modes.CFB(iv))
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(message.encode()) + encryptor.finalize()
        return iv + ciphertext

    def decrypt_message(self, encrypted_message, client_id):
        """Decrypt a message using a client’s session key (AES)."""
        session_key = self.client_session_keys.get(client_id)
        if not session_key:
            raise ValueError(f"No session key found for client ID: {client_id}")

        iv = encrypted_message[:16]  # Extract the IV from the beginning
        ciphertext = encrypted_message[16:]  # Extract the actual ciphertext

        cipher = Cipher(algorithms.AES(session_key), modes.CFB(iv))
        decryptor = cipher.decryptor()
        return decryptor.update(ciphertext) + decryptor.finalize().decode()

# Example Usage:
# encryption_manager = EncryptionManager()
# encryption_manager.generate_keys()
# print(encryption_manager.get_public_key())
