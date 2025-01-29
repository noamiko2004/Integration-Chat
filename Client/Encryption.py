from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import os

class EncryptionManager:
    def __init__(self):
        self.private_key = None
        self.public_key = None
        self.server_public_key = None
        self.session_key = None

    def generate_keys(self):
        """Generate RSA public and private keys for the client."""
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        self.public_key = self.private_key.public_key()

    def get_public_key(self):
        """Return the client's public key in PEM format."""
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

    def set_server_public_key(self, server_public_key_pem):
        """Store the server's public key from a PEM format."""
        self.server_public_key = serialization.load_pem_public_key(server_public_key_pem)

    def generate_session_key(self):
        """Generate a random 32-byte session key for AES encryption."""
        self.session_key = os.urandom(32)
        return self.session_key

    def encrypt_session_key(self):
        """Encrypt the session key using the server's public key."""
        if not self.server_public_key:
            raise ValueError("Server public key is not set.")

        return self.server_public_key.encrypt(
            self.session_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

    def encrypt_message(self, message):
        """Encrypt a message using AES with the session key."""
        if not self.session_key:
            raise ValueError("Session key is not set.")

        iv = os.urandom(16)  # Initialization vector
        cipher = Cipher(algorithms.AES(self.session_key), modes.CFB(iv))
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(message.encode()) + encryptor.finalize()
        return iv + ciphertext

    def decrypt_message(self, encrypted_message):
        """Decrypt a message using AES with the session key."""
        if not self.session_key:
            raise ValueError("Session key is not set.")

        iv = encrypted_message[:16]  # Extract the IV from the beginning
        ciphertext = encrypted_message[16:]  # Extract the actual ciphertext

        cipher = Cipher(algorithms.AES(self.session_key), modes.CFB(iv))
        decryptor = cipher.decryptor()
        return decryptor.update(ciphertext) + decryptor.finalize().decode()

# Example Usage:
encryption_manager = EncryptionManager()
encryption_manager.generate_keys()
print(encryption_manager.get_public_key())
