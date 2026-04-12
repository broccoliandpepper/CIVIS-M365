# REDEVELOPMENT ROADMAP - SIEM M365 (Cross-Platform)

Version: 1.0  
Date: 2026-04-12

## Goal
Rebuild and stabilize SIEM M365 as a full cross-platform product (Windows, Linux, macOS) with consistent setup, runtime behavior, and secure data handling.

## Product Scope
- Backend API: FastAPI + SQLAlchemy + SQLite lifecycle (HOT/ARCHIVE/CONFIG)
- Frontend: full web app with authenticated SOC and executive views
- Ingestion: SignIns, Risky Users, Incidents, Audit Logs M365
- Security: JWT auth, role-based access, encrypted backup workflow
- Operations: reproducible setup, test automation, production runbooks

## Cross-Platform Baseline (Done)
- Remove hardcoded Windows frontend file path in API root.
- Use relative API URL in frontend to avoid hostname hardcoding.
- Add universal Python launcher for setup/start on all OS.

## Delivery Plan

### Phase 1 - Platform Foundation
1. Normalize paths and filesystem operations in backend and scripts.
2. Provide one startup command for all OS.
3. Add health checks and environment diagnostics endpoint.
4. Add CI matrix (Windows/Linux/macOS) for smoke tests.

Definition of done:
- App starts and responds on all three OS with one documented command.

### Phase 2 - Domain Core
1. Stabilize ingestion parsers for all 4 log sources.
2. Strengthen schema validation and reject malformed payloads.
3. Enforce idempotent deduplication keys per source.
4. Ensure truth list comparisons generate reliable new-user alerts.

Definition of done:
- Re-ingesting same files creates zero duplicates.

### Phase 3 - SOC Workflows
1. Build complete SOC pages (alerts, anomalies, filters, triage actions).
2. Add analyst-focused query UX (pagination, filters, exports).
3. Add role-segregated views (IT vs Direction).

Definition of done:
- End-to-end SOC review can be performed without direct DB access.

### Phase 4 - Lifecycle and Recovery
1. Complete HOT to ARCHIVE automation policy.
2. Validate backup creation before cleanup.
3. Implement restore validation scenarios.
4. Add lifecycle observability and failure notification.

Definition of done:
- Recovery test from backup passes on a fresh machine.

### Phase 5 - Hardening and Release
1. Security headers, secrets policy, auth hardening.
2. E2E tests and load tests for target scale.
3. Deployment guides for each OS.
4. Final acceptance checklist.

Definition of done:
- No critical issue in final QA and release candidate is reproducible.

## Immediate Next Build Items
1. Replace remaining OS-specific script assumptions in service scripts.
2. Add Makefile-like command wrappers for Linux/macOS and PowerShell task parity.
3. Introduce CI workflow with a minimal startup and health validation.
4. Start frontend modularization (split monolithic index.html into app modules).

## Confidential Data Policy
- Any sample/input dataset is confidential.
- Development tests should use masked/synthetic records whenever possible.
- No raw confidential files in commits, tickets, screenshots, or external tools.
