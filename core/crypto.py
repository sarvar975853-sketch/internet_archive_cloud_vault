import os
import base64
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class CryptoEngine:
    def __init__(self):
        pass

    def _derive_key(self, password: str, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    def calculate_sha256(self, file_path: str) -> str:
        """Calculate the SHA256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def encrypt_file(self, file_path: str, password: str, output_path: str) -> str:
        """Encrypts a file and prepends salt + original sha256 checksum."""
        original_hash = self.calculate_sha256(file_path)
        salt = os.urandom(16)
        key = self._derive_key(password, salt)
        fernet = Fernet(key)
        
        with open(file_path, 'rb') as f:
            original_data = f.read()
            
        encrypted_data = fernet.encrypt(original_data)
        
        # Structure: 16 bytes salt | 64 bytes hex hash | encrypted payload
        with open(output_path, 'wb') as f:
            f.write(salt + original_hash.encode('utf-8') + encrypted_data)
            
        return original_hash

    def decrypt_file(self, encrypted_file_path: str, password: str, output_path: str) -> bool:
        """Decrypts a file and verifies integrity. Returns True if hash matches."""
        with open(encrypted_file_path, 'rb') as f:
            encrypted_payload = f.read()
            
        salt = encrypted_payload[:16]
        expected_hash = encrypted_payload[16:80].decode('utf-8')
        actual_encrypted_data = encrypted_payload[80:]
        
        key = self._derive_key(password, salt)
        fernet = Fernet(key)
        
        try:
            decrypted_data = fernet.decrypt(actual_encrypted_data)
        except Exception as e:
            raise ValueError("Decryption Failed! Your passphrase is incorrect.")
            
        with open(output_path, 'wb') as f:
            f.write(decrypted_data)
            
        # Verify Integrity
        actual_hash = self.calculate_sha256(output_path)
        if actual_hash != expected_hash:
            os.remove(output_path)
            raise ValueError("Integrity check failed! The file may be corrupted.")
            
        return True
