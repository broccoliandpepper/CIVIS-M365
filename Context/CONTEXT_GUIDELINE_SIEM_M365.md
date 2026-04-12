# CONTEXT GUIDELINE - SIEM M365 (CONFIDENTIAL)

Version: 1.0  
Date: 2026-04-12  
Scope: Reinstallation, operations baseline, and secure handling of sensitive M365 exports.

## 1. Purpose
This file is the single operational guideline for this project.
It defines:
- What the SIEM does.
- How to install it on a new machine with minimal friction.
- How to handle confidential sample/input files.
- The expected SOC workflow (ingest, dedup, truth list validation, archive lifecycle).

## 2. Security and Confidentiality Rules (MANDATORY)
Data in Context/Sample and operational exports are classified CONFIDENTIAL.

Mandatory rules:
- Never share raw sample files outside approved internal scope.
- Never send sample data in chat, email, ticketing, or public tools.
- Never commit confidential data to Git.
- Keep encryption keys only in local secure environment variables or local .env (excluded from Git).
- Use encrypted storage at rest on workstation (BitLocker recommended).
- Restrict local folder access to authorized IT/SOC users only.

Safe usage pattern:
- Use samples only to understand schema/structure.
- For tests/demos, use sanitized or synthetic datasets.
- If evidence is needed, export aggregates only (counts, trends, no PII raw dump).

## 3. Project Functional Baseline
Main inputs:
- SignIns
- Risky Users
- Incidents
- Unified Audit Log (UAL)

Core logic:
- Ingestion via JSON/CSV upload.
- Strict validation + parsing.
- Deduplication at ingestion (event identifiers + timestamps).
- Truth list comparison to detect unknown/new users.
- SOC review workflow for approval/rejection.
- 90-day hot retention, then archive lifecycle.

## 4. Minimal Reinstallation Guide (New Machine, Windows)
Prerequisites:
- Windows 10/11
- Python 3.11+
- PowerShell execution allowed for project scripts

Recommended quick start:
1. Clone/copy project folder siem-m365.
2. From project root, run:
   powershell -ExecutionPolicy Bypass -File .\scripts\start_siem.ps1
3. This script should:
   - create .venv if missing,
   - install backend dependencies,
   - initialize SQLite databases,
   - start FastAPI service.

Alternative service mode:
- Start background service:
  powershell -ExecutionPolicy Bypass -File .\scripts\start_siem_service.ps1
- Stop service:
  powershell -ExecutionPolicy Bypass -File .\scripts\stop_siem_service.ps1

## 5. Required Local Configuration
Create backend/.env from backend/.env.example.
Minimum sensitive variables to set strongly:
- DB_ENCRYPTION_KEY (>= 32 chars)
- JWT_SECRET_KEY
- BACKUP_ENCRYPTION_KEY (>= 32 chars)

Default local DB paths:
- data/db/siem_hot.db
- data/db/siem_archive.db
- data/db/siem_config.db

Backup path:
- data/backups

## 6. SOC Daily Workflow
1. Export logs from M365 (manual UI export or controlled script export).
2. Upload files to SIEM ingestion.
3. Verify ingestion summary:
   - records inserted,
   - duplicates rejected,
   - validation errors.
4. Review New User alerts against truth list.
5. Approve/reject and update truth list governance.
6. Monitor KPI dashboards (IT and Direction views).

## 7. Data Lifecycle Policy
Retention model:
- HOT: 0-90 days (read/write)
- ARCHIVE: 90-180 days (read-focused)
- BACKUP: encrypted zipped JSON after archive window

Operational rule:
- Backup must be validated before cleanup.
- If backup validation fails, cleanup is blocked and rollback path must be used.

## 8. Confidential Data Handling Checklist
Before opening a sample/input file:
- Confirm business need.
- Confirm you are on approved machine.
- Confirm destination folder is protected.

Before sharing any output:
- Remove direct identifiers (UPN, email, IP when not required).
- Share only aggregated indicators when possible.
- Re-check no raw confidential payload is attached.

Before commit/publish:
- Ensure no sample/confidential file is staged.
- Ensure .env and secret files are excluded.
- Ensure generated reports do not contain raw PII unless explicitly approved.

## 9. Suggested Operational Hardening
- Schedule recurring export and ingestion windows.
- Enable failure notifications for lifecycle/backup jobs.
- Rotate encryption keys with documented procedure.
- Run periodic restore tests from backups.
- Keep troubleshooting runbook updated in docs/.

## 10. Known Constraints
- Manual export from M365 can be limited by UI constraints and human process risk.
- CSV can lose nested structure compared to JSON.
- Local-only architecture requires disciplined backup and key management.

## 11. Definition of Done for Reinstallation
A new machine installation is considered valid when:
- API starts successfully.
- Login works and admin password is changed.
- Test ingestion of each source type works.
- Dedup blocks duplicates on re-upload.
- New user detection triggers correctly from truth list comparison.
- Lifecycle move/backup flow completes without error.

## 12. Governance Note
This guideline is confidential and internal-use only.
If project structure changes, update this file first so it remains the operational source of truth.
