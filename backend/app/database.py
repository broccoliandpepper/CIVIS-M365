"""
Configuration SQLite - Base de données locale chiffrée au niveau données sensibles
"""

import sqlite3
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from pathlib import Path

from app.config import settings


Base = declarative_base()


def get_db_engine(db_path: str):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        pool_pre_ping=True
    )
    
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode = WAL")
        cursor.execute("PRAGMA synchronous = NORMAL")
        cursor.execute("PRAGMA cache_size = 10000")
        cursor.close()
    
    return engine


engine_hot = get_db_engine(settings.DB_PATH)
SessionLocal_hot = sessionmaker(autocommit=False, autoflush=False, bind=engine_hot)

engine_archive = get_db_engine(settings.DB_ARCHIVE_PATH)
SessionLocal_archive = sessionmaker(autocommit=False, autoflush=False, bind=engine_archive)

engine_config = get_db_engine(settings.DB_CONFIG_PATH)
SessionLocal_config = sessionmaker(autocommit=False, autoflush=False, bind=engine_config)


def get_db_hot():
    db = SessionLocal_hot()
    try:
        yield db
    finally:
        db.close()


def get_db_archive():
    db = SessionLocal_archive()
    try:
        yield db
    finally:
        db.close()


def get_db_config():
    db = SessionLocal_config()
    try:
        yield db
    finally:
        db.close()


def apply_audit_logs_schema_fixes(db_path: str):
    db_file = Path(db_path)
    if not db_file.exists():
        return

    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(audit_logs_m365)")
    cols = {row[1] for row in cursor.fetchall()}

    new_cols = [
        ('record_type', 'VARCHAR(50)'),
        ('category', 'VARCHAR(100)'),
        ('operation', 'VARCHAR(100)'),
        ('result', 'VARCHAR(50)'),
        ('result_reason', 'VARCHAR(255)'),
        ('user_id', 'VARCHAR(255)'),
        ('user_principal', 'VARCHAR(255)'),
        ('user_type', 'VARCHAR(50)'),
        ('ip_address', 'VARCHAR(45)'),
        ('client_ip', 'VARCHAR(45)'),
        ('client_info', 'VARCHAR(255)'),
        ('city', 'VARCHAR(100)'),
        ('country_or_region', 'VARCHAR(10)'),
        ('workload', 'VARCHAR(100)'),
        ('target_id', 'VARCHAR(255)'),
        ('target_type', 'VARCHAR(50)'),
        ('target_display_name', 'VARCHAR(255)'),
        ('target_resource', 'VARCHAR(255)'),
        ('raw_json', 'TEXT'),
        ('user_agent', 'VARCHAR(255)'),
        ('initiated_by', 'VARCHAR(255)'),
        ('correlation_id', 'VARCHAR(100)'),
    ]

    for col_name, col_type in new_cols:
        if col_name not in cols:
            cursor.execute(f"ALTER TABLE audit_logs_m365 ADD COLUMN {col_name} {col_type}")

    conn.commit()
    conn.close()


def apply_signins_schema_fixes(db_path: str):
    db_file = Path(db_path)
    if not db_file.exists():
        return

    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(signins)")
    cols = {row[1] for row in cursor.fetchall()}

    new_cols = [
        ('user_id', 'VARCHAR(100)'),
        ('user_type', 'VARCHAR(50)'),
        ('error_code', 'VARCHAR(50)'),
        ('correlation_id', 'VARCHAR(100)'),
        ('conditional_access_status', 'VARCHAR(50)'),
        ('auth_requirement', 'VARCHAR(100)'),
        ('app_id', 'VARCHAR(100)'),
        ('device_os', 'VARCHAR(100)'),
        ('device_browser', 'VARCHAR(100)'),
        ('device_is_compliant', 'VARCHAR(10)'),
        ('device_is_managed', 'VARCHAR(10)'),
        ('risk_detail', 'VARCHAR(50)'),
        ('risk_state', 'VARCHAR(50)'),
        ('risk_level', 'VARCHAR(50)'),
        ('flagged_for_review', 'VARCHAR(10)'),
    ]

    for col_name, col_type in new_cols:
        if col_name not in cols:
            cursor.execute(f"ALTER TABLE signins ADD COLUMN {col_name} {col_type}")

    conn.commit()
    conn.close()


def apply_risky_users_schema_fixes(db_path: str):
    db_file = Path(db_path)
    if not db_file.exists():
        return

    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(risky_users)")
    cols = {row[1] for row in cursor.fetchall()}

    new_cols = [
        ('user_display_name', 'VARCHAR(255)'),
        ('risk_last_updated', 'DATETIME'),
        ('is_deleted', 'VARCHAR(10)'),
        ('is_processing', 'VARCHAR(10)'),
    ]

    for col_name, col_type in new_cols:
        if col_name not in cols:
            cursor.execute(f"ALTER TABLE risky_users ADD COLUMN {col_name} {col_type}")

    conn.commit()
    conn.close()


def apply_incident_schema_fixes(db_path: str):
    db_file = Path(db_path)
    if not db_file.exists():
        return

    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(incidents)")
    cols = {row[1] for row in cursor.fetchall()}

    new_cols = [
        ('priority_score', 'VARCHAR(50)'),
        ('tags', 'VARCHAR(255)'),
        ('investigation_state', 'VARCHAR(100)'),
        ('impacted_assets', 'VARCHAR(255)'),
        ('active_alerts', 'VARCHAR(50)'),
        ('service_sources', 'VARCHAR(255)'),
        ('detection_sources', 'VARCHAR(255)'),
        ('last_update_time', 'VARCHAR(100)'),
        ('last_activity', 'VARCHAR(100)'),
        ('policy_name', 'VARCHAR(255)'),
        ('data_sensitivity', 'VARCHAR(100)'),
        ('classification', 'VARCHAR(100)'),
        ('determination', 'VARCHAR(100)'),
        ('device_groups', 'VARCHAR(255)'),
        ('creation_time', 'VARCHAR(100)'),
        ('workspaces', 'VARCHAR(255)'),
        ('cloud_scopes', 'VARCHAR(255)'),
    ]

    for col_name, col_type in new_cols:
        if col_name not in cols:
            cursor.execute(f"ALTER TABLE incidents ADD COLUMN {col_name} {col_type}")

    conn.commit()
    conn.close()


def apply_archive_manifest_schema_fixes(db_path: str):
    db_file = Path(db_path)
    if not db_file.exists():
        return

    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(archive_manifest)")
    cols = {row[1] for row in cursor.fetchall()}

    new_cols = [
        ('sha256_checksum', 'VARCHAR(64)'),
    ]

    for col_name, col_type in new_cols:
        if col_name not in cols:
            cursor.execute(f"ALTER TABLE archive_manifest ADD COLUMN {col_name} {col_type}")

    conn.commit()
    conn.close()


def init_all_databases():
    Base.metadata.create_all(bind=engine_hot)
    Base.metadata.create_all(bind=engine_archive)
    Base.metadata.create_all(bind=engine_config)
    apply_archive_manifest_schema_fixes(settings.DB_CONFIG_PATH)
    apply_signins_schema_fixes(settings.DB_PATH)
    apply_audit_logs_schema_fixes(settings.DB_PATH)
    apply_risky_users_schema_fixes(settings.DB_PATH)
    apply_incident_schema_fixes(settings.DB_PATH)
    print("Databases initialisees avec succes")


def init_db_on_startup():
    """Crée les tables au démarrage de l'app"""
    Base.metadata.create_all(bind=engine_config)
    Base.metadata.create_all(bind=engine_hot)
    Base.metadata.create_all(bind=engine_archive)
    apply_archive_manifest_schema_fixes(settings.DB_CONFIG_PATH)
    apply_signins_schema_fixes(settings.DB_PATH)
    apply_audit_logs_schema_fixes(settings.DB_PATH)
    apply_risky_users_schema_fixes(settings.DB_PATH)
    apply_incident_schema_fixes(settings.DB_PATH)