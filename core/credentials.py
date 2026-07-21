import os
import json
import base64
from cryptography.fernet import Fernet

CONFIG_FILE = os.path.expanduser("~/.aegis_config.enc")
KEY_FILE = os.path.expanduser("~/.aegis_sys.key")

class CredentialManager:
    def __init__(self):
        self.key = self._load_or_create_key()
        self.fernet = Fernet(self.key)

    def _load_or_create_key(self):
        if not os.path.exists(KEY_FILE):
            key = Fernet.generate_key()
            with open(KEY_FILE, 'wb') as f:
                f.write(key)
            os.chmod(KEY_FILE, 0o600)
            return key
        else:
            with open(KEY_FILE, 'rb') as f:
                return f.read()

    def save_credentials(self, access_key: str, secret_key: str):
        data = {
            "access_key": access_key,
            "secret_key": secret_key
        }
        json_data = json.dumps(data).encode('utf-8')
        encrypted_data = self.fernet.encrypt(json_data)
        
        with open(CONFIG_FILE, 'wb') as f:
            f.write(encrypted_data)
        os.chmod(CONFIG_FILE, 0o600)

    def load_credentials(self):
        if not os.path.exists(CONFIG_FILE):
            return None, None
            
        try:
            with open(CONFIG_FILE, 'rb') as f:
                encrypted_data = f.read()
            decrypted_data = self.fernet.decrypt(encrypted_data)
            data = json.loads(decrypted_data.decode('utf-8'))
            return data.get("access_key"), data.get("secret_key")
        except Exception:
            return None, None
            
    def clear_credentials(self):
        if os.path.exists(CONFIG_FILE):
            os.remove(CONFIG_FILE)
