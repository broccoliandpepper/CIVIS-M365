#!/usr/bin/env python3
"""
Cross-platform bootstrap script for SIEM M365.

Works on Windows, macOS, and Linux.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


DEFAULT_ENV = """APP_NAME=SIEM_M365
APP_ENV=development
DEBUG=False
DB_ENCRYPTION_KEY=siem-m365-secure-32byte-key!!
JWT_SECRET_KEY=siem-m365-jwt-secret-key-2024!
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30
BACKUP_ENCRYPTION_KEY=siem-m365-backup-32byte-key!!
DB_PATH=./data/db/siem_hot.db
DB_ARCHIVE_PATH=./data/db/siem_archive.db
DB_CONFIG_PATH=./data/db/siem_config.db
BACKUP_PATH=./data/backups
HOST=127.0.0.1
PORT=5000
PASSWORD_MIN_LENGTH=12
PASSWORD_REQUIRE_SPECIAL=True
"""


def run(cmd: list[str], cwd: Path | None = None) -> None:
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True)


def get_venv_python(venv_path: Path) -> Path:
    if os.name == "nt":
        return venv_path / "Scripts" / "python.exe"
    return venv_path / "bin" / "python"


def ensure_env_file(env_path: Path) -> None:
    if env_path.exists():
        return
    env_path.write_text(DEFAULT_ENV, encoding="utf-8")
    print(f"[OK] Created default env file: {env_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="SIEM M365 cross-platform launcher")
    parser.add_argument("--host", default="127.0.0.1", help="API listen host")
    parser.add_argument("--port", default="5000", help="API listen port")
    parser.add_argument("--setup-only", action="store_true", help="Run setup only and exit")
    parser.add_argument("--skip-pip", action="store_true", help="Skip dependency installation")
    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    backend_path = project_root / "backend"
    requirements_path = backend_path / "requirements.txt"
    env_path = backend_path / ".env"
    init_db_script = project_root / "scripts" / "init_db.py"
    venv_path = project_root / ".venv"

    if not backend_path.exists():
        print(f"[ERROR] Missing backend folder: {backend_path}")
        return 1

    if not requirements_path.exists():
        print(f"[ERROR] Missing requirements file: {requirements_path}")
        return 1

    print(f"[INFO] Project root: {project_root}")

    if not venv_path.exists():
        print("[INFO] Creating virtual environment")
        run([sys.executable, "-m", "venv", str(venv_path)], cwd=project_root)

    venv_python = get_venv_python(venv_path)
    if not venv_python.exists():
        print(f"[ERROR] Virtual environment python not found: {venv_python}")
        return 1

    if not args.skip_pip:
        print("[INFO] Installing dependencies")
        run([str(venv_python), "-m", "pip", "install", "--upgrade", "pip"], cwd=project_root)
        run([str(venv_python), "-m", "pip", "install", "-r", str(requirements_path)], cwd=project_root)

    ensure_env_file(env_path)

    print("[INFO] Initializing databases")
    run([str(venv_python), str(init_db_script)], cwd=project_root)

    if args.setup_only:
        print("[OK] Setup completed")
        return 0

    print(f"[INFO] Starting API on http://{args.host}:{args.port}")
    run(
        [
            str(venv_python),
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            args.host,
            "--port",
            str(args.port),
        ],
        cwd=backend_path,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
