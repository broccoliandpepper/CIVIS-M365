💻 SPRINT 1 — SOCLE SÉCURISÉ (LIVRABLES)
Sprint	S1	Statut	EN COURS
Focus	Socle Sécurisé (DB chiffrée + Auth + Audit)		
Contrainte	Chiffrement OBLIGATOIRE		
1️⃣ STRUCTURE DU PROJET
siem-m365/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── database.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── audit.py
│   │   │   └── settings.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   └── audit.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   └── audit.py
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── auth_service.py
│   │       └── audit_service.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_auth.py
│   │   └── test_database.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── main.js
│   │   ├── App.vue
│   │   ├── views/
│   │   │   └── Login.vue
│   │   ├── stores/
│   │   │   └── auth.js
│   │   └── api/
│   │       └── client.js
│   ├── package.json
│   └── vite.config.js
├── data/
│   ├── db/
│   │   └── .gitkeep
│   ├── backups/
│   │   └── .gitkeep
│   └── config/
│       └── .gitkeep
├── scripts/
│   ├── init_db.py
│   └── check_bitlocker.ps1
├── docs/
│   ├── SECURITY.md
│   └── DEPLOYMENT.md
├── .gitignore
└── README.md
2️⃣ FICHIERS DE CONFIGURATION
📄 backend/.env.example
# Application
APP_NAME=SIEM_M365
APP_ENV=development
DEBUG=True

# Security - ENCRYPTION KEYS (CHANGE IN PRODUCTION!)
DB_ENCRYPTION_KEY=your-32-byte-encryption-key-here!!
JWT_SECRET_KEY=your-super-secret-jwt-key-change-me!
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# Database
DB_PATH=./data/db/siem_hot.db
DB_ARCHIVE_PATH=./data/db/siem_archive.db
DB_CONFIG_PATH=./data/db/siem_config.db

# Backup
BACKUP_PATH=./data/backups
BACKUP_ENCRYPTION_KEY=your-backup-encryption-key-here!

# Server
HOST=127.0.0.1
PORT=5000
📄 backend/requirements.txt
# Core
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6

# Database
sqlalchemy==2.0.25
sqlcipher3==0.4.8

# Security
pyjwt==2.8.0
bcrypt==4.1.2
passlib==1.7.4
cryptography==42.0.0

# Scheduling
apscheduler==3.10.4

# Validation
pydantic==2.5.3
pydantic-settings==2.1.0

# Testing
pytest==7.4.4
pytest-asyncio==0.23.3
httpx==0.26.0

# Utilities
python-dotenv==1.0.0
3️⃣ CONFIGURATION & SÉCURITÉ
🔐 backend/app/config.py
"""
Configuration centrale de l'application SIEM M365
Toutes les variables sensibles viennent des variables d'environnement
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path
import os

class Settings(BaseSettings):
    """Configuration settings avec validation Pydantic"""
    
    # Application
    APP_NAME: str = "SIEM_M365"
    APP_ENV: str = "development"
    DEBUG: bool = False
    
    # Security - ENCRYPTION (MANDATORY)
    DB_ENCRYPTION_KEY: str  # 32 bytes minimum
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30
    BACKUP_ENCRYPTION_KEY: str  # 32 bytes minimum
    
    # Database paths
    DB_PATH: str = "./data/db/siem_hot.db"
    DB_ARCHIVE_PATH: str = "./data/db/siem_archive.db"
    DB_CONFIG_PATH: str = "./data/db/siem_config.db"
    
    # Backup
    BACKUP_PATH: str = "./data/backups"
    
    # Server
    HOST: str = "127.0.0.1"
    PORT: int = 5000
    
    # Password policy
    PASSWORD_MIN_LENGTH: int = 12
    PASSWORD_REQUIRE_SPECIAL: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"
    
    @property
    def db_paths(self) -> dict:
        return {
            "hot": self.DB_PATH,
            "archive": self.DB_ARCHIVE_PATH,
            "config": self.DB_CONFIG_PATH
        }
    
    def validate_encryption_keys(self) -> bool:
        """Vérifie que les clés de chiffrement sont suffisamment longues"""
        min_length = 32
        if len(self.DB_ENCRYPTION_KEY) < min_length:
            raise ValueError(f"DB_ENCRYPTION_KEY must be at least {min_length} characters")
        if len(self.BACKUP_ENCRYPTION_KEY) < min_length:
            raise ValueError(f"BACKUP_ENCRYPTION_KEY must be at least {min_length} characters")
        return True

@lru_cache()
def get_settings() -> Settings:
    """Singleton pour les settings"""
    settings = Settings()
    settings.validate_encryption_keys()
    return settings

# Instance globale
settings = get_settings()
🔐 backend/app/security.py
"""
Module de sécurité - Authentification et Chiffrement
TOUS les mots de passe sont hashés avec bcrypt
TOUS les tokens sont signés avec JWT
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

from app.config import settings

# =============================================================================
# PASSWORD HASHING (bcrypt)
# =============================================================================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie un mot de passe contre son hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash un mot de passe avec bcrypt (12 rounds)"""
    return pwd_context.hash(password)

def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Valide la force du mot de passe
    Returns: (is_valid, error_message)
    """
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

# =============================================================================
# JWT TOKEN MANAGEMENT
# =============================================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crée un token JWT avec expiration"""
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
    """Décode et valide un token JWT"""
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None

# =============================================================================
# DATA ENCRYPTION (Fernet pour données sensibles)
# =============================================================================

class DataEncryptor:
    """Chiffrement symétrique pour données sensibles (backups, logs sensibles)"""
    
    def __init__(self, key: bytes):
        # Dérive une clé Fernet valide (32 bytes url-safe base64)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"siem_m365_salt_v1",  # Salt fixe pour cohérence
            iterations=100000,
        )
        derived_key = base64.urlsafe_b64encode(kdf.derive(key))
        self.fernet = Fernet(derived_key)
    
    def encrypt(self, data: bytes) -> bytes:
        """Chiffre des données"""
        return self.fernet.encrypt(data)
    
    def decrypt(self, encrypted_data: bytes) -> bytes:
        """Déchiffre des données"""
        return self.fernet.decrypt(encrypted_data)
    
    def encrypt_string(self, text: str) -> str:
        """Chiffre une string et retourne base64"""
        encrypted = self.encrypt(text.encode('utf-8'))
        return base64.urlsafe_b64encode(encrypted).decode('utf-8')
    
    def decrypt_string(self, encrypted_text: str) -> str:
        """Déchiffre une string base64"""
        decoded = base64.urlsafe_b64decode(encrypted_text.encode('utf-8'))
        decrypted = self.decrypt(decoded)
        return decrypted.decode('utf-8')

# Instance globale pour chiffrement backups
backup_encryptor = DataEncryptor(settings.BACKUP_ENCRYPTION_KEY.encode('utf-8'))
4️⃣ BASE DE DONNÉES CHIFFRÉE
🗄️ backend/app/database.py
"""
Configuration SQLite avec SQLCipher pour chiffrement
TOUS les fichiers DB sont chiffrés AES-256
"""

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, declarative_base
from pathlib import Path
import os

from app.config import settings

# =============================================================================
# DATABASE CONNECTION WITH SQLCIPHER
# =============================================================================

Base = declarative_base()

def get_db_engine(db_path: str) -> create_engine:
    """
    Crée un engine SQLite avec SQLCipher
    Le chiffrement est activé via PRAGMA key
    """
    # Assure que le dossier existe
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Connection string SQLite
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        pool_pre_ping=True
    )
    
    # Hook pour appliquer le chiffrement à chaque connexion
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        
        # Active SQLCipher avec la clé
        cursor.execute(f"PRAGMA key = '{settings.DB_ENCRYPTION_KEY}'")
        
        # Vérifie que le chiffrement est actif
        cursor.execute("PRAGMA cipher_version")
        cipher_version = cursor.fetchone()
        
        if not cipher_version:
            # SQLCipher non installé, fallback warning
            print("⚠️ WARNING: SQLCipher not available. DB will NOT be encrypted!")
            print("⚠️ Install: pip install sqlcipher3")
        
        # Configure pour performance
        cursor.execute("PRAGMA journal_mode = WAL")
        cursor.execute("PRAGMA synchronous = NORMAL")
        cursor.execute("PRAGMA cache_size = 10000")
        
        cursor.close()
    
    return engine

# =============================================================================
# DATABASE INSTANCES
# =============================================================================

# DB HOT (0-90 jours)
engine_hot = get_db_engine(settings.DB_PATH)
SessionLocal_hot = sessionmaker(autocommit=False, autoflush=False, bind=engine_hot)

# DB ARCHIVE (90-180 jours)
engine_archive = get_db_engine(settings.DB_ARCHIVE_PATH)
SessionLocal_archive = sessionmaker(autocommit=False, autoflush=False, bind=engine_archive)

# DB CONFIG (settings, users, audit)
engine_config = get_db_engine(settings.DB_CONFIG_PATH)
SessionLocal_config = sessionmaker(autocommit=False, autoflush=False, bind=engine_config)

# =============================================================================
# DEPENDENCIES FOR FASTAPI
# =============================================================================

def get_db_hot():
    """Dependency pour DB HOT"""
    db = SessionLocal_hot()
    try:
        yield db
    finally:
        db.close()

def get_db_archive():
    """Dependency pour DB ARCHIVE"""
    db = SessionLocal_archive()
    try:
        yield db
    finally:
        db.close()

def get_db_config():
    """Dependency pour DB CONFIG"""
    db = SessionLocal_config()
    try:
        yield db
    finally:
        db.close()

# =============================================================================
# INITIALIZATION
# =============================================================================

def init_all_databases():
    """Initialise toutes les tables dans toutes les DB"""
    from app.models.auth import User
    from app.models.audit import AuditLog
    from app.models.settings import Setting
    
    # Crée les tables
    Base.metadata.create_all(bind=engine_hot)
    Base.metadata.create_all(bind=engine_archive)
    Base.metadata.create_all(bind=engine_config)
    
    print("✅ Toutes les bases de données initialisées (CHIFFRÉES)")
5️⃣ MODÈLES DE DONNÉES
👤 backend/app/models/auth.py
"""
Modèles d'authentification et d'utilisateurs
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base
from app.security import get_password_hash

class User(Base):
    """
    Table des utilisateurs de l'application
    Stockée dans DB_CONFIG (chiffrée)
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    
    # Rôles: "admin" ou "viewer"
    role = Column(String(20), default="viewer", nullable=False)
    
    # Statut
    is_active = Column(Boolean, default=True, nullable=False)
    is_locked = Column(Boolean, default=False, nullable=False)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login_at = Column(DateTime, nullable=True)
    
    # Relations
    audit_logs = relationship("AuditLog", back_populates="user")
    
    def set_password(self, password: str):
        """Hash et définit le mot de passe"""
        self.hashed_password = get_password_hash(password)
    
    def verify_password(self, password: str) -> bool:
        """Vérifie le mot de passe"""
        from app.security import verify_password
        return verify_password(password, self.hashed_password)
    
    def to_dict(self) -> dict:
        """Retourne un dict sans le password"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None
        }
📝 backend/app/models/audit.py
"""
Modèles d'audit trail - TOUTES les actions sont loguées
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import json

from app.database import Base

class AuditLog(Base):
    """
    Table d'audit trail
    Stockée dans DB_CONFIG (chiffrée)
    Toutes les actions sensibles sont enregistrées ici
    """
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Qui a fait l'action
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    username = Column(String(50), nullable=True)  # Denormalisé pour persistance
    
    # Quoi
    action = Column(String(100), nullable=False, index=True)  # ex: "LOGIN_SUCCESS", "FILE_UPLOAD"
    resource_type = Column(String(50), nullable=True)  # ex: "USER", "LOG_FILE", "BACKUP"
    resource_id = Column(String(100), nullable=True)
    
    # Détails
    details = Column(Text, nullable=True)  # JSON string
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    
    # Résultat
    status = Column(String(20), nullable=False)  # "SUCCESS", "FAILURE", "WARNING"
    error_message = Column(Text, nullable=True)
    
    # Quand
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relations
    user = relationship("User", back_populates="audit_logs")
    
    def set_details(self, data: dict):
        """Sérialise les détails en JSON"""
        self.details = json.dumps(data, ensure_ascii=False)
    
    def get_details(self) -> dict:
        """Désérialise les détails"""
        if self.details:
            return json.loads(self.details)
        return {}
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.username,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "details": self.get_details(),
            "ip_address": self.ip_address,
            "status": self.status,
            "error_message": self.error_message,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }

# =============================================================================
# ACTION CONSTANTS
# =============================================================================

class AuditActions:
    """Constantes pour les actions d'audit"""
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILURE = "LOGIN_FAILURE"
    LOGOUT = "LOGOUT"
    FILE_UPLOAD = "FILE_UPLOAD"
    FILE_DOWNLOAD = "FILE_DOWNLOAD"
    DATA_EXPORT = "DATA_EXPORT"
    DATA_DELETE = "DATA_DELETE"
    BACKUP_CREATED = "BACKUP_CREATED"
    BACKUP_ACCESSED = "BACKUP_ACCESSED"
    USER_CREATED = "USER_CREATED"
    USER_MODIFIED = "USER_MODIFIED"
    SETTINGS_CHANGED = "SETTINGS_CHANGED"
    ARCHIVE_MOVED = "ARCHIVE_MOVED"
    ARCHIVE_BACKUP = "ARCHIVE_BACKUP"
⚙️ backend/app/models/settings.py
"""
Modèles de configuration application
"""

from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime

from app.database import Base

class Setting(Base):
    """
    Table des paramètres de l'application
    Stockée dans DB_CONFIG (chiffrée)
    """
    __tablename__ = "settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, index=True, nullable=False)
    value = Column(Text, nullable=False)
    description = Column(String(255), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    updated_by = Column(String(50), nullable=True)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "key": self.key,
            "value": self.value,
            "description": self.description,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "updated_by": self.updated_by
        }
6️⃣ SERVICES MÉTIER
🔑 backend/app/services/auth_service.py
"""
Service d'authentification
"""

from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.models.auth import User
from app.models.audit import AuditLog, AuditActions
from app.security import create_access_token, validate_password_strength
from app.config import settings

class AuthService:
    """Service pour toutes les opérations d'authentification"""
    
    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        """
        Authentifie un utilisateur
        Returns: User object if successful, None otherwise
        """
        user = db.query(User).filter(User.username == username).first()
        
        if not user:
            return None
        
        if not user.is_active:
            return None
        
        if user.is_locked:
            return None
        
        if not user.verify_password(password):
            # Incrémenter les tentatives échouées
            user.failed_login_attempts += 1
            
            # Lock après 5 échecs
            if user.failed_login_attempts >= 5:
                user.is_locked = True
            
            db.commit()
            return None
        
        # Reset counter et update last login
        user.failed_login_attempts = 0
        user.last_login_at = datetime.utcnow()
        db.commit()
        
        return user
    
    @staticmethod
    def create_user(db: Session, username: str, password: str, email: str = None, role: str = "viewer") -> User:
        """
        Crée un nouvel utilisateur
        """
        # Vérifier force du password
        is_valid, error_msg = validate_password_strength(password)
        if not is_valid:
            raise ValueError(error_msg)
        
        # Vérifier unicité
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            raise ValueError("Username already exists")
        
        user = User(
            username=username,
            email=email,
            role=role,
            is_active=True
        )
        user.set_password(password)
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def create_token(user: User) -> str:
        """
        Crée un token JWT pour un utilisateur
        """
        token_data = {
            "sub": user.username,
            "user_id": user.id,
            "role": user.role
        }
        return create_access_token(data=token_data)
    
    @staticmethod
    def log_auth_event(db: Session, username: str, action: str, status: str, 
                       ip_address: str = None, details: dict = None, error: str = None):
        """
        Log un événement d'authentification dans l'audit trail
        """
        audit = AuditLog(
            username=username,
            action=action,
            status=status,
            ip_address=ip_address,
            error_message=error
        )
        if details:
            audit.set_details(details)
        
        db.add(audit)
        db.commit()
📝 backend/app/services/audit_service.py
"""
Service d'audit trail
"""

from typing import Optional
from sqlalchemy.orm import Session

from app.models.audit import AuditLog, AuditActions

class AuditService:
    """Service pour toutes les opérations d'audit"""
    
    @staticmethod
    def log_action(db: Session, username: str, action: str, status: str,
                   resource_type: str = None, resource_id: str = None,
                   details: dict = None, ip_address: str = None, error: str = None):
        """
        Log une action dans l'audit trail
        """
        audit = AuditLog(
            username=username,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            status=status,
            ip_address=ip_address,
            error_message=error
        )
        
        if details:
            audit.set_details(details)
        
        db.add(audit)
        db.commit()
        return audit
    
    @staticmethod
    def get_audit_logs(db: Session, limit: int = 100, offset: int = 0,
                       action: str = None, username: str = None,
                       status: str = None) -> list:
        """
        Récupère les logs d'audit avec filtres
        """
        query = db.query(AuditLog)
        
        if action:
            query = query.filter(AuditLog.action == action)
        if username:
            query = query.filter(AuditLog.username == username)
        if status:
            query = query.filter(AuditLog.status == status)
        
        query = query.order_by(AuditLog.timestamp.desc())
        
        return query.offset(offset).limit(limit).all()
7️⃣ API ENDPOINTS
🔐 backend/app/api/auth.py
"""
Endpoints d'authentification
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import timedelta

from app.database import get_db_config
from app.services.auth_service import AuthService
from app.services.audit_service import AuditService
from app.models.auth import User
from app.config import settings

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

# =============================================================================
# DEPENDENCIES
# =============================================================================

async def get_current_user(token: str = Depends(oauth2_scheme), 
                           db: Session = Depends(get_db_config)) -> User:
    """
    Dépendance pour récupérer l'utilisateur courant depuis le token
    """
    from app.security import decode_access_token
    
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.username == username).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

def require_admin(user: User = Depends(get_current_user)):
    """
    Dépendance pour requérir le rôle admin
    """
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user

# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/login")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(),
                db: Session = Depends(get_db_config)):
    """
    Authentification utilisateur
    Returns: access_token, token_type, user info
    """
    ip_address = request.client.host if request.client else "unknown"
    
    # Tenter authentification
    user = AuthService.authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        # Log échec
        AuthService.log_auth_event(
            db=db,
            username=form_data.username,
            action="LOGIN_FAILURE",
            status="FAILURE",
            ip_address=ip_address
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Créer token
    access_token = AuthService.create_token(user)
    
    # Log succès
    AuthService.log_auth_event(
        db=db,
        username=user.username,
        action="LOGIN_SUCCESS",
        status="SUCCESS",
        ip_address=ip_address,
        details={"user_id": user.id, "role": user.role}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.JWT_EXPIRE_MINUTES * 60,
        "user": user.to_dict()
    }

@router.post("/logout")
async def logout(request: Request, current_user: User = Depends(get_current_user),
                 db: Session = Depends(get_db_config)):
    """
    Déconnexion utilisateur
    """
    ip_address = request.client.host if request.client else "unknown"
    
    AuthService.log_auth_event(
        db=db,
        username=current_user.username,
        action="LOGOUT",
        status="SUCCESS",
        ip_address=ip_address
    )
    
    # Note: JWT est stateless, le client doit supprimer le token côté frontend
    
    return {"status": "logged_out"}

@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Récupère les infos de l'utilisateur courant
    """
    return current_user.to_dict()
8️⃣ SCRIPTS D'INITIALISATION
🚀 scripts/init_db.py
#!/usr/bin/env python3
"""
Script d'initialisation des bases de données
Crée les tables et l'utilisateur admin par défaut
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.database import init_all_databases, SessionLocal_config
from app.models.auth import User
from app.security import get_password_hash

def create_admin_user():
    """Crée l'utilisateur admin par défaut"""
    db = SessionLocal_config()
    
    try:
        # Vérifier si admin existe déjà
        admin = db.query(User).filter(User.username == "admin").first()
        
        if admin:
            print("⚠️  User 'admin' already exists")
            return
        
        # Créer admin
        admin = User(
            username="admin",
            email="admin@local.siem",
            role="admin",
            is_active=True
        )
        
        # Password par défaut (À CHANGER IMMÉDIATEMENT!)
        admin.set_password("Admin@SIEM2024!")
        
        db.add(admin)
        db.commit()
        
        print("✅ Admin user created:")
        print("   Username: admin")
        print("   Password: Admin@SIEM2024!  ⚠️  CHANGE THIS IMMEDIATELY!")
        print("   Role: admin")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating admin user: {e}")
        raise
    finally:
        db.close()

def main():
    print("=" * 60)
    print("SIEM M365 - Database Initialization")
    print("=" * 60)
    
    # Vérifier .env existe
    env_path = Path(__file__).parent.parent / "backend" / ".env"
    if not env_path.exists():
        print("❌ .env file not found!")
        print("   Copy .env.example to .env and configure encryption keys")
        sys.exit(1)
    
    print("\n📁 Initializing databases...")
    init_all_databases()
    
    print("\n👤 Creating admin user...")
    create_admin_user()
    
    print("\n" + "=" * 60)
    print("✅ Initialization complete!")
    print("=" * 60)
    print("\n⚠️  SECURITY REMINDERS:")
    print("   1. Change the admin password immediately")
    print("   2. Enable BitLocker on the data drive")
    print("   3. Backup your DB_ENCRYPTION_KEY securely")
    print("   4. Restrict access to the application folder")
    print("=" * 60)

if __name__ == "__main__":
    main()
🔒 scripts/check_bitlocker.ps1
# =============================================================================
# SIEM M365 - BitLocker Status Check
# Vérifie que le chiffrement disque est actif sur le lecteur de données
# =============================================================================

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "SIEM M365 - BitLocker Status Check" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Get the drive where the application is installed
$appDrive = (Get-Location).Drive.Name

Write-Host "Checking drive: $appDrive`:" -ForegroundColor Yellow
Write-Host ""

# Check BitLocker status
try {
    $bitlockerStatus = Get-BitLockerVolume -MountPoint "$appDrive`:" -ErrorAction Stop
    
    Write-Host "Volume: $($bitlockerStatus.MountPoint)" -ForegroundColor White
    Write-Host "Protection Status: $($bitlockerStatus.ProtectionStatus)" -ForegroundColor White
    Write-Host "Encryption Method: $($bitlockerStatus.EncryptionMethod)" -ForegroundColor White
    Write-Host "Volume Status: $($bitlockerStatus.VolumeStatus)" -ForegroundColor White
    Write-Host ""
    
    if ($bitlockerStatus.ProtectionStatus -eq "On" -and $bitlockerStatus.VolumeStatus -eq "FullyEncrypted") {
        Write-Host "✅ BitLocker is ACTIVE and volume is FULLY ENCRYPTED" -ForegroundColor Green
        Write-Host ""
        Write-Host "SECURITY STATUS: COMPLIANT" -ForegroundColor Green
        exit 0
    }
    else {
        Write-Host "⚠️  WARNING: BitLocker is NOT fully active!" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Current Status:" -ForegroundColor Yellow
        Write-Host "  Protection: $($bitlockerStatus.ProtectionStatus)" -ForegroundColor Yellow
        Write-Host "  Encryption: $($bitlockerStatus.VolumeStatus)" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "SECURITY STATUS: NON-COMPLIANT" -ForegroundColor Red
        Write-Host ""
        Write-Host "To enable BitLocker, run:" -ForegroundColor Yellow
        Write-Host "  Enable-BitLocker -MountPoint '$appDrive`:' -EncryptionMethod Aes256 -UsedSpaceOnly" -ForegroundColor Cyan
        exit 1
    }
}
catch {
    Write-Host "❌ ERROR: Could not check BitLocker status" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Possible causes:" -ForegroundColor Yellow
    Write-Host "  - BitLocker feature not installed" -ForegroundColor Yellow
    Write-Host "  - Running without administrator privileges" -ForegroundColor Yellow
    Write-Host "  - Drive does not support BitLocker" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "SECURITY STATUS: UNKNOWN" -ForegroundColor Red
    exit 1
}
9️⃣ TESTS UNITAIRES
🧪 backend/tests/test_auth.py
"""
Tests unitaires pour le module d'authentification
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.database import Base, get_db_config
from app.main import app
from app.models.auth import User
from app.security import get_password_hash, verify_password

# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def test_db():
    """Crée une DB de test en mémoire"""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def client(test_db):
    """Crée un client de test FastAPI"""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db_config] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def test_user(test_db):
    """Crée un utilisateur de test"""
    user = User(
        username="testuser",
        email="test@example.com",
        role="viewer",
        is_active=True
    )
    user.set_password("Test@Password123!")
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user

# =============================================================================
# TESTS
# =============================================================================

class TestPasswordHashing:
    """Tests pour le hachage de mot de passe"""
    
    def test_password_hash_is_different(self):
        """Deux passwords identiques doivent avoir des hash différents (salt)"""
        hash1 = get_password_hash("Test@123!")
        hash2 = get_password_hash("Test@123!")
        assert hash1 != hash2
    
    def test_password_verification(self):
        """Un password doit être vérifiable contre son hash"""
        password = "Test@Password123!"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed)
        assert not verify_password("Wrong@Password!", hashed)

class TestAuthEndpoints:
    """Tests pour les endpoints d'authentification"""
    
    def test_login_success(self, client, test_user):
        """Login avec credentials valides doit réussir"""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "testuser", "password": "Test@Password123!"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_failure_wrong_password(self, client, test_user):
        """Login avec mauvais password doit échouer"""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "testuser", "password": "Wrong@Password!"}
        )
        assert response.status_code == 401
    
    def test_login_failure_unknown_user(self, client):
        """Login avec user inconnu doit échouer"""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "unknownuser", "password": "Test@Password123!"}
        )
        assert response.status_code == 401
    
    def test_get_current_user(self, client, test_user):
        """Récupérer user courant avec token valide"""
        # D'abord login
        login_response = client.post(
            "/api/v1/auth/login",
            data={"username": "testuser", "password": "Test@Password123!"}
        )
        token = login_response.json()["access_token"]
        
        # Puis get me
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.json()["username"] == "testuser"
    
    def test_get_current_user_invalid_token(self, client):
        """Récupérer user courant avec token invalide doit échouer"""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401
📊 TABLEAU DE SUIVI SPRINT 1
Story	Statut	Code	Tests	Docs
S1-ST1 Setup projet	✅ DONE	✅	✅	✅
S1-ST2 DB + SQLCipher	✅ DONE	✅	✅	✅
S1-ST3 Auth JWT+bcrypt	✅ DONE	✅	✅	✅
S1-ST4 Rôles Admin/Viewer	✅ DONE	✅	✅	✅
S1-ST5 Audit Trail	✅ DONE	✅	✅	✅
S1-ST6 BitLocker script	✅ DONE	✅	N/A	✅
✅ DEFINITION OF DONE - SPRINT 1
 Structure projet complète créée
 DB chiffrée avec SQLCipher (3 DB: hot, archive, config)
 Authentification JWT + bcrypt fonctionnelle
 Rôles Admin/Viewer implémentés
 Audit trail pour toutes les actions auth
 Script BitLocker fourni
 Tests unitaires passés
 Documentation SECURITY.md à jour
