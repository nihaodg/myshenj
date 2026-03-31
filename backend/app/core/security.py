from cryptography.fernet import Fernet
from app.core.config import settings
import base64
import hashlib

_cipher = None


def get_cipher() -> Fernet:
    global _cipher
    if _cipher is None:
        key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
        _cipher = Fernet(base64.urlsafe_b64encode(key))
    return _cipher


def encrypt_value(value: str) -> str:
    return get_cipher().encrypt(value.encode()).decode()


def decrypt_value(encrypted: str) -> str:
    return get_cipher().decrypt(encrypted.encode()).decode()
