"""Service pour Archive & Lifecycle."""

import base64
import json
import os
import sqlite3
import struct
import tempfile
import zipfile
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.database import engine_archive, engine_config, engine_hot
from app.models.archive_manifest import ArchiveManifest
from app.models.lifecycle_logs import LifecycleLog


class LifecycleService:
    """Service pour le lifecycle des données."""

    BACKUP_FORMAT_VERSION = "3"
    CONTAINER_MAGIC = "SIEMBKP"
    CONTAINER_VERSION = 1
    ENCRYPTION_METHOD = "AES-256-GCM"
    ENCRYPTION_KDF = "PBKDF2-HMAC-SHA256"
    PBKDF2_ITERATIONS = 390000
    ACTIVE_RESTORE_CONFIRM_PREFIX = "RESTORE "
    ROLLBACK_CONFIRM_PREFIX = "ROLLBACK "

    @staticmethod
    def _rollback_root() -> Path:
        return LifecycleService._resolve_project_root() / "data" / "db" / "rollback"

    @staticmethod
    def _retention_cutoff(days: int) -> datetime:
        return datetime.utcnow() - timedelta(days=max(days, 0))

    @staticmethod
    def _resolve_project_root() -> Path:
        return Path(__file__).resolve().parents[3]

    @staticmethod
    def _resolve_runtime_path(path_value: str) -> Path:
        candidate = Path(path_value)
        if candidate.is_absolute():
            return candidate
        return (LifecycleService._resolve_project_root() / candidate).resolve()

    @staticmethod
    def _hash_file(file_path: Path, algorithm: str = "sha256") -> str:
        digest = hashlib.new(algorithm)
        with open(file_path, "rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def _count_rows(engine, table_name: str) -> int:
        with engine.connect() as conn:
            return conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar() or 0

    @staticmethod
    def _copy_sqlite_database(source_path: Path, target_path: Path) -> None:
        source_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.parent.mkdir(parents=True, exist_ok=True)

        if not source_path.exists():
            sqlite3.connect(str(source_path)).close()

        source_conn = sqlite3.connect(str(source_path))
        target_conn = sqlite3.connect(str(target_path))

        try:
            source_conn.backup(target_conn)
        finally:
            target_conn.close()
            source_conn.close()

    @staticmethod
    def _build_backup_sources() -> list[dict]:
        return [
            {
                "name": "hot",
                "source_path": LifecycleService._resolve_runtime_path(settings.DB_PATH),
                "archive_name": "hot.db",
                "engine": engine_hot,
            },
            {
                "name": "archive",
                "source_path": LifecycleService._resolve_runtime_path(settings.DB_ARCHIVE_PATH),
                "archive_name": "archive.db",
                "engine": engine_archive,
            },
            {
                "name": "config",
                "source_path": LifecycleService._resolve_runtime_path(settings.DB_CONFIG_PATH),
                "archive_name": "config.db",
                "engine": engine_config,
            },
        ]

    @staticmethod
    def _build_restore_targets(include_config: bool = False) -> list[dict]:
        sources = LifecycleService._build_backup_sources()
        if include_config:
            return sources
        return [source for source in sources if source["name"] != "config"]

    @staticmethod
    def _build_embedded_manifest(backup_id: str, created_by: str, staged_files: list[dict], record_counts: dict) -> dict:
        timestamp = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        return {
            "backup_id": backup_id,
            "format_version": LifecycleService.BACKUP_FORMAT_VERSION,
            "backup_scope": "full-local",
            "created_at": timestamp,
            "created_by": created_by,
            "encryption": {
                "enabled": True,
                "method": LifecycleService.ENCRYPTION_METHOD,
                "kdf": LifecycleService.ENCRYPTION_KDF,
            },
            "record_counts": record_counts,
            "files": staged_files,
        }

    @staticmethod
    def _derive_encryption_key(salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=LifecycleService.PBKDF2_ITERATIONS,
        )
        return kdf.derive(settings.BACKUP_ENCRYPTION_KEY.encode("utf-8"))

    @staticmethod
    def _build_container_header(backup_id: str, salt: bytes, nonce: bytes) -> dict:
        return {
            "magic": LifecycleService.CONTAINER_MAGIC,
            "container_version": LifecycleService.CONTAINER_VERSION,
            "backup_id": backup_id,
            "encryption": {
                "enabled": True,
                "method": LifecycleService.ENCRYPTION_METHOD,
                "kdf": LifecycleService.ENCRYPTION_KDF,
                "iterations": LifecycleService.PBKDF2_ITERATIONS,
                "salt_b64": base64.b64encode(salt).decode("ascii"),
                "nonce_b64": base64.b64encode(nonce).decode("ascii"),
            },
        }

    @staticmethod
    def _encrypt_archive(plaintext_zip: Path, encrypted_output: Path, backup_id: str) -> dict:
        plaintext = plaintext_zip.read_bytes()
        salt = os.urandom(16)
        nonce = os.urandom(12)
        key = LifecycleService._derive_encryption_key(salt)
        ciphertext = AESGCM(key).encrypt(nonce, plaintext, backup_id.encode("utf-8"))

        header = LifecycleService._build_container_header(backup_id, salt, nonce)
        header_bytes = json.dumps(header).encode("utf-8")

        with open(encrypted_output, "wb") as handle:
            handle.write(struct.pack(">I", len(header_bytes)))
            handle.write(header_bytes)
            handle.write(ciphertext)

        return header

    @staticmethod
    def _decrypt_archive(encrypted_archive: Path, temp_dir: Path) -> tuple[Path, dict]:
        with open(encrypted_archive, "rb") as handle:
            raw_length = handle.read(4)
            if len(raw_length) != 4:
                raise ValueError("Encrypted archive header is incomplete")

            header_length = struct.unpack(">I", raw_length)[0]
            header_bytes = handle.read(header_length)
            header = json.loads(header_bytes.decode("utf-8"))
            ciphertext = handle.read()

        if header.get("magic") != LifecycleService.CONTAINER_MAGIC:
            raise ValueError("Backup container magic is invalid")

        encryption = header.get("encryption", {})
        salt = base64.b64decode(encryption.get("salt_b64", ""))
        nonce = base64.b64decode(encryption.get("nonce_b64", ""))
        backup_id = header.get("backup_id", "")
        key = LifecycleService._derive_encryption_key(salt)
        plaintext = AESGCM(key).decrypt(nonce, ciphertext, backup_id.encode("utf-8"))

        zip_path = temp_dir / "payload.zip"
        zip_path.write_bytes(plaintext)
        return zip_path, header

    @staticmethod
    def _materialize_archive_payload(manifest: ArchiveManifest, temp_dir: Path) -> tuple[Path, dict]:
        archive_path = Path(manifest.backup_filepath)
        if manifest.is_encrypted:
            return LifecycleService._decrypt_archive(archive_path, temp_dir)

        zip_path = temp_dir / archive_path.name
        zip_path.write_bytes(archive_path.read_bytes())
        return zip_path, {
            "magic": "legacy-plain-zip",
            "backup_id": manifest.backup_id,
            "encryption": {"enabled": False, "method": manifest.encryption_method},
        }

    @staticmethod
    def _verify_embedded_manifest(zip_path: Path, extract_dir: Path) -> tuple[dict, list[str]]:
        with zipfile.ZipFile(zip_path, "r") as archive:
            names = archive.namelist()
            if "manifest.json" not in names:
                raise ValueError("manifest.json is missing from backup archive")

            archive.extractall(extract_dir)

        manifest_path = extract_dir / "manifest.json"
        with open(manifest_path, "r", encoding="utf-8") as handle:
            manifest = json.load(handle)

        missing_files = []
        for file_info in manifest.get("files", []):
            relative_name = file_info.get("name")
            expected_sha256 = file_info.get("sha256")
            if not relative_name:
                continue

            candidate = extract_dir / relative_name
            if not candidate.exists():
                missing_files.append(relative_name)
                continue

            actual_sha256 = LifecycleService._hash_file(candidate, "sha256")
            if expected_sha256 and actual_sha256 != expected_sha256:
                raise ValueError(f"Integrity check failed for {relative_name}")

        return manifest, missing_files

    @staticmethod
    def _check_sqlite_integrity(db_path: Path) -> None:
        conn = sqlite3.connect(str(db_path))
        try:
            result = conn.execute("PRAGMA integrity_check").fetchone()
            if not result or result[0] != "ok":
                raise ValueError(f"SQLite integrity check failed for {db_path.name}")
        finally:
            conn.close()

    @staticmethod
    def _create_rollback_snapshot(rollback_id: str, created_by: str, targets: list[dict]) -> dict:
        rollback_root = LifecycleService._rollback_root()
        rollback_dir = rollback_root / rollback_id
        rollback_dir.mkdir(parents=True, exist_ok=True)

        files = []
        for target in targets:
            rollback_path = rollback_dir / target["archive_name"]
            LifecycleService._copy_sqlite_database(target["source_path"], rollback_path)
            LifecycleService._check_sqlite_integrity(rollback_path)
            files.append({
                "name": target["archive_name"],
                "sha256": LifecycleService._hash_file(rollback_path, "sha256"),
            })

        metadata = {
            "rollback_id": rollback_id,
            "created_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
            "created_by": created_by,
            "files": files,
            "scope": [target["name"] for target in targets],
        }
        with open(rollback_dir / "metadata.json", "w", encoding="utf-8") as handle:
            json.dump(metadata, handle, indent=2)

        return {
            "rollback_id": rollback_id,
            "rollback_path": str(rollback_dir),
            "metadata": metadata,
        }

    @staticmethod
    def _load_rollback_snapshot(rollback_id: str) -> tuple[Path, dict]:
        rollback_dir = LifecycleService._rollback_root() / rollback_id
        metadata_path = rollback_dir / "metadata.json"
        if not metadata_path.exists():
            raise FileNotFoundError(f"Rollback snapshot {rollback_id} not found")

        with open(metadata_path, "r", encoding="utf-8") as handle:
            metadata = json.load(handle)

        return rollback_dir, metadata

    @staticmethod
    def _apply_runtime_restore(extracted_dir: Path, targets: list[dict]) -> None:
        for target in targets:
            source_file = extracted_dir / target["archive_name"]
            if not source_file.exists():
                raise ValueError(f"Backup payload missing {target['archive_name']}")

            LifecycleService._copy_sqlite_database(source_file, target["source_path"])
            LifecycleService._check_sqlite_integrity(target["source_path"])

    @staticmethod
    def _dispose_runtime_engines(include_config: bool = False) -> None:
        engine_hot.dispose()
        engine_archive.dispose()
        if include_config:
            engine_config.dispose()

    @staticmethod
    def _cleanup_backup_retention(db: Session) -> dict:
        backup_dir = LifecycleService._resolve_runtime_path(settings.BACKUP_PATH) / "archives"
        backup_dir.mkdir(parents=True, exist_ok=True)

        removed_files = []
        removed_manifests = []
        cutoff = LifecycleService._retention_cutoff(settings.BACKUP_RETENTION_DAYS)
        max_files = max(settings.BACKUP_RETENTION_MAX_FILES, 1)

        manifests = db.query(ArchiveManifest).order_by(ArchiveManifest.created_at.desc()).all()

        for index, manifest in enumerate(manifests):
            file_path = Path(manifest.backup_filepath)
            created_at = manifest.created_at or datetime.utcnow()
            should_remove = created_at < cutoff or index >= max_files
            if should_remove:
                if file_path.exists():
                    file_path.unlink()
                    removed_files.append(file_path.name)
                removed_manifests.append(manifest.backup_id)
                db.delete(manifest)

        known_files = {Path(m.backup_filepath).name for m in db.query(ArchiveManifest).all()}
        for file_path in backup_dir.glob("*.sbk"):
            if file_path.name not in known_files:
                file_path.unlink()
                removed_files.append(file_path.name)

        return {
            "removed_backup_files": removed_files,
            "removed_backup_ids": removed_manifests,
        }

    @staticmethod
    def _cleanup_rollback_retention() -> dict:
        rollback_root = LifecycleService._rollback_root()
        rollback_root.mkdir(parents=True, exist_ok=True)

        removed_snapshots = []
        cutoff = LifecycleService._retention_cutoff(settings.ROLLBACK_RETENTION_DAYS)
        max_snapshots = max(settings.ROLLBACK_RETENTION_MAX_SNAPSHOTS, 1)

        snapshot_dirs = sorted(
            [path for path in rollback_root.iterdir() if path.is_dir()],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        for index, snapshot_dir in enumerate(snapshot_dirs):
            modified_at = datetime.utcfromtimestamp(snapshot_dir.stat().st_mtime)
            should_remove = modified_at < cutoff or index >= max_snapshots
            if should_remove:
                for file_path in sorted(snapshot_dir.rglob("*"), reverse=True):
                    if file_path.is_file():
                        file_path.unlink()
                    elif file_path.is_dir():
                        file_path.rmdir()
                snapshot_dir.rmdir()
                removed_snapshots.append(snapshot_dir.name)

        return {
            "removed_rollback_snapshots": removed_snapshots,
        }

    @staticmethod
    def enforce_retention(db: Session, triggered_by: str = "system") -> dict:
        lifecycle_log = LifecycleLog(
            operation="RETENTION_ROTATION",
            status="started",
            created_by=triggered_by,
        )
        db.add(lifecycle_log)
        db.commit()
        db.refresh(lifecycle_log)

        try:
            backups_info = LifecycleService._cleanup_backup_retention(db)
            rollback_info = LifecycleService._cleanup_rollback_retention()
            db.commit()

            removed_count = len(backups_info["removed_backup_files"]) + len(backups_info["removed_backup_ids"]) + len(rollback_info["removed_rollback_snapshots"])
            lifecycle_log.status = "completed"
            lifecycle_log.records_processed = removed_count
            lifecycle_log.completed_at = datetime.utcnow()
            lifecycle_log.details = json.dumps({
                "backup_retention_days": settings.BACKUP_RETENTION_DAYS,
                "backup_retention_max_files": settings.BACKUP_RETENTION_MAX_FILES,
                "rollback_retention_days": settings.ROLLBACK_RETENTION_DAYS,
                "rollback_retention_max_snapshots": settings.ROLLBACK_RETENTION_MAX_SNAPSHOTS,
                **backups_info,
                **rollback_info,
            })
            db.commit()

            return {
                "status": "success",
                "policy": {
                    "backup_retention_days": settings.BACKUP_RETENTION_DAYS,
                    "backup_retention_max_files": settings.BACKUP_RETENTION_MAX_FILES,
                    "rollback_retention_days": settings.ROLLBACK_RETENTION_DAYS,
                    "rollback_retention_max_snapshots": settings.ROLLBACK_RETENTION_MAX_SNAPSHOTS,
                },
                **backups_info,
                **rollback_info,
            }
        except Exception as exc:
            db.rollback()
            lifecycle_log.status = "failed"
            lifecycle_log.error_message = str(exc)
            lifecycle_log.completed_at = datetime.utcnow()
            db.commit()
            return {"status": "error", "error": str(exc)}

    @staticmethod
    def get_archive_status(db: Session) -> dict:
        """Retourne le statut des bases de données."""
        with engine_hot.connect() as conn:
            signins_count = conn.execute(text("SELECT COUNT(*) FROM signins")).scalar()
            risky_count = conn.execute(text("SELECT COUNT(*) FROM risky_users")).scalar()
            incidents_count = conn.execute(text("SELECT COUNT(*) FROM incidents")).scalar()

        with engine_archive.connect() as conn:
            archive_signins = conn.execute(text("SELECT COUNT(*) FROM signins")).scalar()

        age_days = (datetime.utcnow() - datetime(2026, 1, 1)).days
        archive_threshold = 90

        backup_dir = LifecycleService._resolve_runtime_path(settings.BACKUP_PATH) / "archives"
        rollback_root = LifecycleService._rollback_root()
        archive_count = len(list(backup_dir.glob("*.sbk"))) if backup_dir.exists() else 0
        rollback_count = len([path for path in rollback_root.iterdir() if path.is_dir()]) if rollback_root.exists() else 0

        return {
            "hot": {
                "records": signins_count,
                "risky_users": risky_count,
                "incidents": incidents_count,
                "age_days": age_days,
                "should_archive": age_days >= archive_threshold,
            },
            "archive": {
                "records": archive_signins,
                "age_days": age_days - 90 if age_days > 90 else 0,
            },
            "rotation": {
                "backup_archives_count": archive_count,
                "rollback_snapshots_count": rollback_count,
                "backup_retention_days": settings.BACKUP_RETENTION_DAYS,
                "backup_retention_max_files": settings.BACKUP_RETENTION_MAX_FILES,
                "rollback_retention_days": settings.ROLLBACK_RETENTION_DAYS,
                "rollback_retention_max_snapshots": settings.ROLLBACK_RETENTION_MAX_SNAPSHOTS,
            },
        }

    @staticmethod
    def create_backup(db: Session, created_by: str = "admin") -> dict:
        """Crée un backup cohérent multi-bases chiffré AES-256-GCM."""
        backup_id = f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        lifecycle_log = LifecycleLog(
            operation="CREATE_BACKUP",
            status="started",
            created_by=created_by,
        )
        db.add(lifecycle_log)
        db.commit()
        db.refresh(lifecycle_log)

        try:
            backup_dir = LifecycleService._resolve_runtime_path(settings.BACKUP_PATH) / "archives"
            backup_dir.mkdir(parents=True, exist_ok=True)

            backup_file = backup_dir / f"{backup_id}.sbk"
            sources = LifecycleService._build_backup_sources()

            record_counts = {
                "signins": LifecycleService._count_rows(engine_hot, "signins") + LifecycleService._count_rows(engine_archive, "signins"),
                "risky_users": LifecycleService._count_rows(engine_hot, "risky_users") + LifecycleService._count_rows(engine_archive, "risky_users"),
                "incidents": LifecycleService._count_rows(engine_hot, "incidents") + LifecycleService._count_rows(engine_archive, "incidents"),
                "audit_logs": LifecycleService._count_rows(engine_hot, "audit_logs_m365") + LifecycleService._count_rows(engine_archive, "audit_logs_m365"),
            }

            period_to = datetime.utcnow()
            period_from = period_to - timedelta(days=90)

            with tempfile.TemporaryDirectory(prefix=f"{backup_id}_") as temp_dir_str:
                temp_dir = Path(temp_dir_str)
                staged_files = []

                for source in sources:
                    staged_path = temp_dir / source["archive_name"]
                    LifecycleService._copy_sqlite_database(source["source_path"], staged_path)
                    LifecycleService._check_sqlite_integrity(staged_path)
                    staged_files.append({
                        "name": source["archive_name"],
                        "source": source["name"],
                        "size_bytes": staged_path.stat().st_size,
                        "sha256": LifecycleService._hash_file(staged_path, "sha256"),
                    })

                manifest_payload = LifecycleService._build_embedded_manifest(
                    backup_id=backup_id,
                    created_by=created_by,
                    staged_files=staged_files,
                    record_counts=record_counts,
                )
                manifest_path = temp_dir / "manifest.json"
                with open(manifest_path, "w", encoding="utf-8") as handle:
                    json.dump(manifest_payload, handle, indent=2)

                plaintext_zip = temp_dir / f"{backup_id}.zip"
                with zipfile.ZipFile(plaintext_zip, "w", zipfile.ZIP_DEFLATED) as archive:
                    for file_path in sorted(temp_dir.iterdir()):
                        if file_path == plaintext_zip:
                            continue
                        archive.write(file_path, file_path.name)

                container_header = LifecycleService._encrypt_archive(plaintext_zip, backup_file, backup_id)

            file_size = backup_file.stat().st_size
            md5 = LifecycleService._hash_file(backup_file, "md5")
            sha256 = LifecycleService._hash_file(backup_file, "sha256")

            manifest = ArchiveManifest(
                backup_id=backup_id,
                backup_filename=backup_file.name,
                backup_filepath=str(backup_file),
                period_from=period_from,
                period_to=period_to,
                record_count_signins=record_counts["signins"],
                record_count_risky=record_counts["risky_users"],
                record_count_incidents=record_counts["incidents"],
                record_count_audit=record_counts["audit_logs"],
                total_records=0,
                file_size_bytes=file_size,
                md5_checksum=md5,
                sha256_checksum=sha256,
                is_encrypted=True,
                encryption_method=LifecycleService.ENCRYPTION_METHOD,
                status="created",
                created_by=created_by,
                notes=json.dumps({
                    "backup_scope": "full-local",
                    "format_version": LifecycleService.BACKUP_FORMAT_VERSION,
                    "included_databases": [source["name"] for source in sources],
                    "container": container_header,
                }),
            )
            manifest.total_records = (
                manifest.record_count_signins +
                manifest.record_count_risky +
                manifest.record_count_incidents +
                manifest.record_count_audit
            )

            db.add(manifest)

            lifecycle_log.status = "completed"
            lifecycle_log.records_processed = manifest.total_records
            lifecycle_log.completed_at = datetime.utcnow()
            db.commit()

            retention = LifecycleService.enforce_retention(db, triggered_by=created_by)

            return {
                "status": "success",
                "backup_id": backup_id,
                "records": manifest.total_records,
                "size_bytes": file_size,
                "manifest_id": manifest.id,
                "sha256_checksum": sha256,
                "included_databases": [source["name"] for source in sources],
                "encryption_method": LifecycleService.ENCRYPTION_METHOD,
                "retention": retention,
            }
        except Exception as exc:
            lifecycle_log.status = "failed"
            lifecycle_log.error_message = str(exc)
            lifecycle_log.completed_at = datetime.utcnow()
            db.commit()
            return {
                "status": "failed",
                "error": str(exc),
            }

    @staticmethod
    def list_backups(db: Session, limit: int = 20) -> list:
        backups = db.query(ArchiveManifest).order_by(
            ArchiveManifest.created_at.desc()
        ).limit(limit).all()
        return [backup.to_dict() for backup in backups]

    @staticmethod
    def list_lifecycle_logs(db: Session, limit: int = 50) -> list:
        logs = db.query(LifecycleLog).order_by(
            LifecycleLog.started_at.desc()
        ).limit(limit).all()
        return [entry.to_dict() for entry in logs]

    @staticmethod
    def inspect_backup(db: Session, backup_id: str) -> dict:
        manifest = db.query(ArchiveManifest).filter(
            ArchiveManifest.backup_id == backup_id
        ).first()
        if not manifest:
            return {"status": "not_found"}

        backup_path = Path(manifest.backup_filepath)
        if not backup_path.exists():
            return {"status": "missing_file", "backup_id": backup_id}

        try:
            with tempfile.TemporaryDirectory(prefix=f"inspect_{backup_id}_") as temp_dir_str:
                temp_dir = Path(temp_dir_str)
                zip_path, container_header = LifecycleService._materialize_archive_payload(manifest, temp_dir)
                with zipfile.ZipFile(zip_path, "r") as archive:
                    entries = [
                        {
                            "name": info.filename,
                            "size": info.file_size,
                            "compressed_size": info.compress_size,
                        }
                        for info in archive.infolist()
                    ]
                    embedded_manifest = None
                    if "manifest.json" in archive.namelist():
                        with archive.open("manifest.json") as handle:
                            embedded_manifest = json.load(handle)

            return {
                "status": "success",
                "backup_id": backup_id,
                "entries": entries,
                "entry_count": len(entries),
                "manifest": embedded_manifest,
                "container": container_header,
            }
        except Exception as exc:
            return {"status": "error", "backup_id": backup_id, "error": str(exc)}

    @staticmethod
    def restore_backup(db: Session, backup_id: str, restored_by: str = "admin") -> dict:
        """Effectue un restore dry-run dans un dossier isolé sans toucher à la DB active."""
        manifest = db.query(ArchiveManifest).filter(
            ArchiveManifest.backup_id == backup_id
        ).first()
        if not manifest:
            return {"status": "not_found"}

        backup_path = Path(manifest.backup_filepath)
        if not backup_path.exists():
            return {"status": "missing_file", "backup_id": backup_id}

        lifecycle_log = LifecycleLog(
            operation="RESTORE_BACKUP",
            status="started",
            created_by=restored_by,
        )
        db.add(lifecycle_log)
        db.commit()
        db.refresh(lifecycle_log)

        restore_root = LifecycleService._resolve_project_root() / "data" / "db" / "restored"
        restore_dir = restore_root / f"{backup_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        restore_dir.mkdir(parents=True, exist_ok=True)

        try:
            current_sha256 = LifecycleService._hash_file(backup_path, "sha256")
            if manifest.sha256_checksum and current_sha256 != manifest.sha256_checksum:
                raise ValueError("Archive SHA-256 mismatch")

            with tempfile.TemporaryDirectory(prefix=f"restore_{backup_id}_") as temp_dir_str:
                temp_dir = Path(temp_dir_str)
                zip_path, container_header = LifecycleService._materialize_archive_payload(manifest, temp_dir)
                embedded_manifest, missing_files = LifecycleService._verify_embedded_manifest(zip_path, restore_dir)

            extracted = sorted(path.name for path in restore_dir.iterdir())
            if missing_files:
                raise ValueError(f"Backup archive is incomplete: {', '.join(missing_files)}")

            lifecycle_log.status = "completed"
            lifecycle_log.records_processed = len(extracted)
            lifecycle_log.completed_at = datetime.utcnow()
            db.commit()

            return {
                "status": "success",
                "backup_id": backup_id,
                "restore_path": str(restore_dir),
                "files": extracted,
                "file_count": len(extracted),
                "validation": {
                    "archive_sha256": current_sha256,
                    "manifest_present": True,
                    "format_version": embedded_manifest.get("format_version"),
                    "container": container_header,
                },
            }
        except Exception as exc:
            lifecycle_log.status = "failed"
            lifecycle_log.error_message = str(exc)
            lifecycle_log.completed_at = datetime.utcnow()
            db.commit()
            return {"status": "error", "backup_id": backup_id, "error": str(exc)}

    @staticmethod
    def verify_backup(db: Session, backup_id: str) -> dict:
        manifest = db.query(ArchiveManifest).filter(
            ArchiveManifest.backup_id == backup_id
        ).first()
        if not manifest:
            return {"status": "not_found"}

        try:
            backup_path = Path(manifest.backup_filepath)
            current_md5 = LifecycleService._hash_file(backup_path, "md5")
            current_sha256 = LifecycleService._hash_file(backup_path, "sha256")
            with tempfile.TemporaryDirectory(prefix=f"verify_{backup_id}_") as temp_dir_str:
                temp_dir = Path(temp_dir_str)
                zip_path, container_header = LifecycleService._materialize_archive_payload(manifest, temp_dir)
                embedded_manifest, missing_files = LifecycleService._verify_embedded_manifest(zip_path, temp_dir / "contents")

            verified = (
                current_md5 == manifest.md5_checksum and
                (not manifest.sha256_checksum or current_sha256 == manifest.sha256_checksum) and
                not missing_files and
                embedded_manifest.get("backup_id") == backup_id
            )

            manifest.status = "verified" if verified else "corrupted"
            if verified:
                manifest.verified_at = datetime.utcnow()
            db.commit()

            return {
                "status": "verified" if verified else "corrupted",
                "backup_id": backup_id,
                "expected_md5": manifest.md5_checksum,
                "actual_md5": current_md5,
                "expected_sha256": manifest.sha256_checksum,
                "actual_sha256": current_sha256,
                "manifest_present": True,
                "missing_files": missing_files,
                "container": container_header,
            }
        except Exception as exc:
            return {
                "status": "error",
                "error": str(exc),
            }

    @staticmethod
    def restore_backup_active(db: Session, backup_id: str, restored_by: str, confirm_phrase: str) -> dict:
        """Restaure activement HOT et ARCHIVE avec rollback opérateur."""
        expected_phrase = f"{LifecycleService.ACTIVE_RESTORE_CONFIRM_PREFIX}{backup_id}"
        if confirm_phrase != expected_phrase:
            return {"status": "confirmation_required", "expected": expected_phrase}

        manifest = db.query(ArchiveManifest).filter(
            ArchiveManifest.backup_id == backup_id
        ).first()
        if not manifest:
            return {"status": "not_found"}

        lifecycle_log = LifecycleLog(
            operation="RESTORE_ACTIVE",
            status="started",
            created_by=restored_by,
            source_db=backup_id,
            target_db="hot,archive",
        )
        db.add(lifecycle_log)
        db.commit()
        db.refresh(lifecycle_log)

        restore_targets = LifecycleService._build_restore_targets(include_config=False)
        rollback_id = f"rollback_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        try:
            with tempfile.TemporaryDirectory(prefix=f"active_restore_{backup_id}_") as temp_dir_str:
                temp_dir = Path(temp_dir_str)
                zip_path, container_header = LifecycleService._materialize_archive_payload(manifest, temp_dir)
                extracted_dir = temp_dir / "contents"
                extracted_dir.mkdir(parents=True, exist_ok=True)
                _, missing_files = LifecycleService._verify_embedded_manifest(zip_path, extracted_dir)
                if missing_files:
                    raise ValueError(f"Backup archive is incomplete: {', '.join(missing_files)}")

                rollback_snapshot = LifecycleService._create_rollback_snapshot(rollback_id, restored_by, restore_targets)

                LifecycleService._dispose_runtime_engines(include_config=False)
                try:
                    LifecycleService._apply_runtime_restore(extracted_dir, restore_targets)
                except Exception:
                    lifecycle_log.rollback_performed = True
                    rollback_dir = Path(rollback_snapshot["rollback_path"])
                    LifecycleService._apply_runtime_restore(rollback_dir, restore_targets)
                    raise

            lifecycle_log.status = "completed"
            lifecycle_log.records_processed = len(restore_targets)
            lifecycle_log.completed_at = datetime.utcnow()
            db.commit()

            retention = LifecycleService.enforce_retention(db, triggered_by=restored_by)

            return {
                "status": "success",
                "backup_id": backup_id,
                "rollback_id": rollback_id,
                "rollback_path": rollback_snapshot["rollback_path"],
                "restored_databases": [target["name"] for target in restore_targets],
                "container": container_header,
                "retention": retention,
                "message": "Active restore applied to HOT and ARCHIVE. CONFIG remains excluded from live restore.",
            }
        except Exception as exc:
            lifecycle_log.status = "failed"
            lifecycle_log.error_message = str(exc)
            lifecycle_log.completed_at = datetime.utcnow()
            db.commit()
            return {
                "status": "error",
                "backup_id": backup_id,
                "rollback_id": rollback_id,
                "error": str(exc),
            }
        finally:
            LifecycleService._dispose_runtime_engines(include_config=False)

    @staticmethod
    def rollback_active_restore(db: Session, rollback_id: str, restored_by: str, confirm_phrase: str) -> dict:
        """Permet à l'opérateur de réappliquer un snapshot de rollback."""
        expected_phrase = f"{LifecycleService.ROLLBACK_CONFIRM_PREFIX}{rollback_id}"
        if confirm_phrase != expected_phrase:
            return {"status": "confirmation_required", "expected": expected_phrase}

        lifecycle_log = LifecycleLog(
            operation="ROLLBACK_ACTIVE_RESTORE",
            status="started",
            created_by=restored_by,
            source_db=rollback_id,
            target_db="hot,archive",
        )
        db.add(lifecycle_log)
        db.commit()
        db.refresh(lifecycle_log)

        try:
            rollback_dir, metadata = LifecycleService._load_rollback_snapshot(rollback_id)
            restore_targets = LifecycleService._build_restore_targets(include_config=False)

            LifecycleService._dispose_runtime_engines(include_config=False)
            LifecycleService._apply_runtime_restore(rollback_dir, restore_targets)

            lifecycle_log.status = "completed"
            lifecycle_log.records_processed = len(restore_targets)
            lifecycle_log.completed_at = datetime.utcnow()
            db.commit()

            return {
                "status": "success",
                "rollback_id": rollback_id,
                "restored_databases": [target["name"] for target in restore_targets],
                "metadata": metadata,
            }
        except Exception as exc:
            lifecycle_log.status = "failed"
            lifecycle_log.error_message = str(exc)
            lifecycle_log.completed_at = datetime.utcnow()
            db.commit()
            return {
                "status": "error",
                "rollback_id": rollback_id,
                "error": str(exc),
            }
        finally:
            LifecycleService._dispose_runtime_engines(include_config=False)
