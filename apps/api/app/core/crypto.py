import base64
import hashlib
from cryptography.fernet import Fernet
from app.core.config import settings


def _get_fernet_key() -> bytes:
    """
    Gera uma chave Fernet estática de 32 bytes codificada em base64 a partir do SECRET_KEY da aplicação.
    """
    derived = hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(derived)


def encrypt_data(data: bytes | str) -> str:
    """
    Criptografa bytes ou string e retorna a string Fernet em base64.
    """
    if isinstance(data, str):
        raw_bytes = data.encode("utf-8")
    else:
        raw_bytes = data

    f = Fernet(_get_fernet_key())
    encrypted = f.encrypt(raw_bytes)
    return encrypted.decode("utf-8")


def decrypt_data(encrypted_str: str) -> bytes:
    """
    Descriptografa a string Fernet e retorna os bytes originais.
    """
    f = Fernet(_get_fernet_key())
    decrypted = f.decrypt(encrypted_str.encode("utf-8"))
    return decrypted


def encrypt_text(data: str) -> str:
    """
    Criptografa texto em UTF-8 e retorna a string Fernet em base64.
    """
    return encrypt_data(data)


def decrypt_text(encrypted_str: str) -> str:
    """
    Descriptografa a string Fernet e retorna o texto original em UTF-8.
    """
    return decrypt_data(encrypted_str).decode("utf-8")

