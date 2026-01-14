"""Encryption utilities for sensitive data"""
from cryptography.fernet import Fernet
from app.config import settings
import base64
import hashlib


def get_encryption_key() -> bytes:
    """
    Derive encryption key from secret_key in config.
    Uses SHA256 to create a valid 32-byte Fernet key.
    """
    key = hashlib.sha256(settings.secret_key.encode()).digest()
    return base64.urlsafe_b64encode(key)


def encrypt_value(value: str) -> str:
    """Encrypt a string value"""
    if not value:
        return ""
    
    try:
        fernet = Fernet(get_encryption_key())
        encrypted = fernet.encrypt(value.encode())
        return encrypted.decode()
    except Exception as e:
        print(f"❌ Encryption error: {e}")
        return value  # Fallback to plaintext if encryption fails


def decrypt_value(encrypted_value: str) -> str:
    """Decrypt an encrypted string value"""
    if not encrypted_value:
        return ""
    
    try:
        fernet = Fernet(get_encryption_key())
        decrypted = fernet.decrypt(encrypted_value.encode())
        return decrypted.decode()
    except Exception as e:
        # If decryption fails, assume it's plaintext (for backwards compatibility)
        print(f"⚠️ Decryption failed, using value as-is: {e}")
        return encrypted_value
