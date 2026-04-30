#!/usr/bin/env python3
"""
Cross-platform bootstrap script for SIEM M365.

Works on Windows, macOS, and Linux.
"""

from __future__ import annotations

import argparse
import os
import secrets
import string
import subprocess
import sys
from pathlib import Path


SPECIAL_CHARS = "!@#$%^*_+-="


def generate_secret() -> str:
    return secrets.token_urlsafe(32)


def generate_initial_password(length: int = 20) -> str:
    alphabet = string.ascii_letters + string.digits + SPECIAL_CHARS
    while True:
        password = "".join(secrets.choice(alphabet) for _ in range(length))
        if (
            any(char.islower() for char in password)
            and any(char.isupper() for char in password)
            and any(char.isdigit() for char in password)
            and any(char in SPECIAL_CHARS for char in password)
        ):
            return password


def build_default_env() -> str:
    return (
        "APP_NAME=SIEM_M365\n"
        "APP_ENV=development\n"
        "DEBUG=False\n"
        f"DB_ENCRYPTION_KEY={generate_secret()}\n"
        f"JWT_SECRET_KEY={generate_secret()}\n"
        "JWT_ALGORITHM=HS256\n"
        "JWT_EXPIRE_MINUTES=30\n"
        f"BACKUP_ENCRYPTION_KEY={generate_secret()}\n"
        f"INITIAL_ADMIN_PASSWORD={generate_initial_password()}\n"
        "DB_PATH=./data/db/siem_hot.db\n"
        "DB_ARCHIVE_PATH=./data/db/siem_archive.db\n"
        "DB_CONFIG_PATH=./data/db/siem_config.db\n"
        "BACKUP_PATH=./data/backups\n"
        "HOST=127.0.0.1\n"
        "PORT=5000\n"
        "CORS_ALLOWED_ORIGINS=http://127.0.0.1:5000,http://localhost:5000\n"
        "PASSWORD_MIN_LENGTH=12\n"
        "PASSWORD_REQUIRE_SPECIAL=True\n"
    )


def run(cmd: list[str], cwd: Path | None = None) -> None:
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True)


def get_venv_python(venv_path: Path) -> Path:
    if os.name == "nt":
        return venv_path / "Scripts" / "python.exe"
    return venv_path / "bin" / "python"


def ensure_env_file(env_path: Path) -> None:
    if env_path.exists():
        return
    env_path.write_text(build_default_env(), encoding="utf-8")
    print(f"[OK] Created default env file: {env_path}")
    print("[INFO] Generated fresh secrets and INITIAL_ADMIN_PASSWORD in backend/.env")


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
