"""
Module de sécurité - Authentification et Chiffrement
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

from app.config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def validate_password_strength(password: str) -> tuple[bool, str]:
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        return False, f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters"
    
    if settings.PASSWORD_REQUIRE_SPECIAL:
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(char in special_chars for char in password):
            return False, "Password must contain at least one special character"
    
    if not any(char.isdigit() for char in password):
        return False, "Password must contain at least one digit"
    
    if not any(char.isupper() for char in password):
        return False, "Password must contain at least one uppercase letter"
    
    return True, ""


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None


class DataEncryptor:
    def __init__(self, key: bytes):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"siem_m365_salt_v1",
            iterations=100000,
        )
        derived_key = base64.urlsafe_b64encode(kdf.derive(key))
        self.fernet = Fernet(derived_key)
    
    def encrypt(self, data: bytes) -> bytes:
        return self.fernet.encrypt(data)
    
    def decrypt(self, encrypted_data: bytes) -> bytes:
        return self.fernet.decrypt(encrypted_data)


backup_encryptor = DataEncryptor(settings.BACKUP_ENCRYPTION_KEY.encode('utf-8'))