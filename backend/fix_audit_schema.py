"""Add missing columns to audit_logs_m365 table - run standalone"""
import sqlite3
from pathlib import Path

from app.config import settings


def fix_schema():
    db_path = Path(settings.db_path_resolved)
    if not db_path.exists():
        print("Database not found at configured DB_PATH")
        return

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(audit_logs_m365)")
    cols = {row[1] for row in cursor.fetchall()}
    print(f"Current columns: {sorted(cols)}")

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
            print(f"Adding: {col_name}")
            cursor.execute(f"ALTER TABLE audit_logs_m365 ADD COLUMN {col_name} {col_type}")

    conn.commit()

    cursor.execute("PRAGMA table_info(audit_logs_m365)")
    cols = {row[1] for row in cursor.fetchall()}
    print(f"After fix: {sorted(cols)}")
    conn.close()
    print("Done!")


if __name__ == "__main__":
    fix_schema()