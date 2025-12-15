"""Secure credential storage with encryption."""
import json
import base64
import hashlib
from pathlib import Path
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class CredentialManager:
    """Manages encrypted storage of API credentials."""

    def __init__(self, config_path: Path):
        self.config_path = config_path
        self._fernet: Optional[Fernet] = None
        self._credentials: dict = {}
        self._salt: Optional[bytes] = None

    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password using PBKDF2."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    def is_configured(self) -> bool:
        """Check if credentials file exists."""
        return self.config_path.exists()

    def create_new(self, master_password: str) -> bool:
        """Create new encrypted credentials file."""
        import os
        self._salt = os.urandom(16)
        key = self._derive_key(master_password, self._salt)
        self._fernet = Fernet(key)
        self._credentials = {
            "cloudflare_api_token": "",
            "anthropic_api_key": "",
            "accounts": []
        }
        return self._save()

    def unlock(self, master_password: str) -> bool:
        """Unlock credentials with master password."""
        if not self.config_path.exists():
            return False

        try:
            with open(self.config_path, 'rb') as f:
                data = f.read()

            # First 16 bytes are salt
            self._salt = data[:16]
            encrypted_data = data[16:]

            key = self._derive_key(master_password, self._salt)
            self._fernet = Fernet(key)

            decrypted = self._fernet.decrypt(encrypted_data)
            self._credentials = json.loads(decrypted.decode())
            return True
        except (InvalidToken, json.JSONDecodeError):
            self._fernet = None
            self._credentials = {}
            return False

    def lock(self):
        """Lock credentials and clear from memory."""
        self._fernet = None
        self._credentials = {}

    def is_unlocked(self) -> bool:
        """Check if credentials are currently unlocked."""
        return self._fernet is not None

    def _save(self) -> bool:
        """Save encrypted credentials to file."""
        if not self._fernet or not self._salt:
            return False

        try:
            data = json.dumps(self._credentials).encode()
            encrypted = self._fernet.encrypt(data)

            with open(self.config_path, 'wb') as f:
                f.write(self._salt + encrypted)
            return True
        except Exception:
            return False

    def get_cloudflare_token(self) -> str:
        """Get Cloudflare API token."""
        return self._credentials.get("cloudflare_api_token", "")

    def set_cloudflare_token(self, token: str) -> bool:
        """Set Cloudflare API token."""
        self._credentials["cloudflare_api_token"] = token
        return self._save()

    def get_anthropic_key(self) -> str:
        """Get Anthropic API key."""
        return self._credentials.get("anthropic_api_key", "")

    def set_anthropic_key(self, key: str) -> bool:
        """Set Anthropic API key."""
        self._credentials["anthropic_api_key"] = key
        return self._save()

    def get_accounts(self) -> list:
        """Get list of Cloudflare accounts."""
        return self._credentials.get("accounts", [])

    def add_account(self, name: str, token: str) -> bool:
        """Add a Cloudflare account."""
        accounts = self._credentials.get("accounts", [])
        accounts.append({"name": name, "token": token})
        self._credentials["accounts"] = accounts
        return self._save()

    def remove_account(self, name: str) -> bool:
        """Remove a Cloudflare account by name."""
        accounts = self._credentials.get("accounts", [])
        self._credentials["accounts"] = [a for a in accounts if a["name"] != name]
        return self._save()

    def change_master_password(self, old_password: str, new_password: str) -> bool:
        """Change the master password."""
        # Verify old password
        if not self.unlock(old_password):
            return False

        # Re-encrypt with new password
        import os
        self._salt = os.urandom(16)
        key = self._derive_key(new_password, self._salt)
        self._fernet = Fernet(key)
        return self._save()
