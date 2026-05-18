# CIVIS M365

![Platform](https://img.shields.io/badge/platform-Microsoft%20365-blue)
![Backend](https://img.shields.io/badge/backend-FastAPI-009688)
![Frontend](https://img.shields.io/badge/frontend-JavaScript-F7DF1E)
![Database](https://img.shields.io/badge/database-SQLite-003B57)
![Status](https://img.shields.io/badge/status-active%20development-orange)
![Scope](https://img.shields.io/badge/scope-civic--oriented%20security-success)
![License](https://img.shields.io/badge/license-MIT-green)

**A civic-oriented Microsoft 365 security visibility platform.**

CIVIS M365 is a lightweight, self-hosted platform designed to improve Microsoft 365 security visibility in organizations that need practical monitoring capabilities without the cost and operational overhead of enterprise SIEM adoption.

---

## Why This Project Exists

This project was born from a simple observation:

**small organizations, especially NGOs, associations, and resource-constrained teams, are increasingly exposed to cyber risk but often lack the means to deploy dedicated security monitoring tooling.**

Many of these organizations already depend on Microsoft 365 for identity, messaging, and collaboration. As a result, they already generate security-relevant events such as:

- sign-in activity,
- risky user signals,
- incidents,
- audit logs,
- abnormal access patterns.

The problem is not that security data does not exist.  
The problem is that the organizations most exposed to operational fragility often **cannot afford the tooling, integration effort, or security staffing required to operationalize that data effectively**.

This creates a structural gap:

- the need for visibility is real;
- the signals are already there;
- but the financial and technical barriers remain too high.

CIVIS M365 is an attempt to respond to that gap.

---

## Problem Statement

> **How can an organization improve security visibility on a Microsoft 365 environment when it does not have the budget to deploy a commercial SIEM?**

This question is particularly relevant for small organizations, NGOs, associations, and other mission-driven teams operating in increasingly hostile digital contexts.

In many such environments:

- cybersecurity remains underfunded;
- event analysis is still largely manual;
- useful Microsoft 365 signals remain underexploited;
- and anomaly detection depends too heavily on time, experience, and human availability.

The issue is therefore not only technical.  
It is also economic, organizational, and social.

---

## Proposed Approach

This project does not aim to reproduce the full scope of an enterprise SIEM.

Instead, it should be understood as a **focused, civic-oriented, low-complexity response to a concrete security visibility gap** affecting organizations that are underserved by traditional enterprise security tooling.

The approach is pragmatic:

- use security-relevant data already available in Microsoft 365;
- centralize and normalize it in a lightweight self-hosted platform;
- surface first-level anomalies more quickly;
- reduce dependence on fully manual review;
- and provide a base that can evolve toward more continuous and automated monitoring over time.

In that sense, CIVIS M365 is less a finished SIEM product than a **practical proposal for improving security visibility where funding constraints make enterprise solutions unrealistic**.

---

## Overview

CIVIS M365 centralizes, normalizes, and analyzes Microsoft 365 security data in a pragmatic, maintainable architecture designed for organizations that need an accessible alternative to enterprise SIEM tooling.

Typical target contexts include:

- small organizations with limited cybersecurity resources;
- NGOs and associations operating in constrained environments;
- internal Microsoft 365 security monitoring initiatives;
- educational, lab, or demonstration environments;
- teams that need first-level visibility before investing in larger platforms.

The name **CIVIS** reflects the project’s orientation toward civic, social, and resource-constrained organizations that need better access to practical cybersecurity capabilities.

---

## Project Positioning

This repository is intentionally scoped.

### What it is

- a focused Microsoft 365 monitoring platform;
- a civic-oriented response to a real security funding gap;
- a low-complexity foundation for first-level SOC workflows;
- an evolving base toward more automated Microsoft 365 security ingestion.

### What it is not

- a full enterprise SIEM replacement;
- a universal telemetry platform for all infrastructure sources;
- a finished real-time SOC product;
- a claim that small organizations can replace mature security operations with a single lightweight tool.

---

## Current Capabilities

### Data Ingestion

Supported Microsoft 365-oriented sources:

- **SignIns**
- **Risky Users**
- **Incidents**
- **Audit Logs**
- **Truth List / allow-list**

### Detection and Analysis

Implemented first-level detections include:

- sign-ins from non-allowed countries;
- sign-ins by high-risk users;
- authentication failure spikes;
- near-concurrent access from different IP addresses;
- suspicious access without explicit VPN context;
- atypical access hours.

### Investigation and Reporting

Available features include:

- dashboard and KPI views;
- filtered queries and event search;
- anomaly review workflows;
- SOC summary reporting;
- HTML and data export;
- local retention, backup, and restore operations.

### Administration and Operations

Operational features include:

- local authentication and user management;
- startup and maintenance scripts;
- Windows service support;
- local self-hosted deployment.

---

## Why the Project Can Still Be Useful in Its Current State

CIVIS M365 is still evolving, but it already provides value in one important area:

**helping administrators surface suspicious activity faster from Microsoft 365 data that would otherwise remain dispersed, manually reviewed, or operationally underused.**

In practice, this means the platform can already help:

- centralize useful security signals;
- reduce friction in first-level review workflows;
- highlight anomalous access patterns more quickly;
- and support a more structured security posture in environments that cannot adopt a full SIEM stack.

---

## Architecture

The stack is intentionally lightweight:

- **Backend:** Python / FastAPI
- **Frontend:** HTML / CSS / JavaScript
- **Storage:** SQLite
- **Operations:** Python and PowerShell scripts

This architecture prioritizes:

- low deployment cost;
- ease of setup;
- maintainability;
- practical self-hosting;
- incremental evolution over time.

---

## Getting Started

### Requirements

- Python 3.11+
- Git
- Windows, Linux, or macOS
- a modern web browser

### Installation

```bash
git clone <repository-url>
cd Siem-M365-V2
python -m venv .venv
```

Activate the virtual environment:

```bash
# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate
```

Install backend dependencies:

```bash
cd backend
pip install -r requirements.txt
cd ..
```

Initialize the databases:

```bash
python scripts/init_db.py
```

---

## Configuration

Copy:

```text
backend/.env.example
```

to:

```text
backend/.env
```

Then set your own environment values and secrets.

Example categories:

```env
APP_NAME=CIVIS_M365
APP_ENV=production
DEBUG=False

JWT_SECRET_KEY=change-this-secret
BACKUP_ENCRYPTION_KEY=change-this-backup-key
DB_ENCRYPTION_KEY=change-this-db-key

DB_PATH=./data/db/siem_hot.db
DB_ARCHIVE_PATH=./data/db/siem_archive.db
DB_CONFIG_PATH=./data/db/siem_config.db
```

Never commit populated `.env` files.

---

## Run the Application

Recommended startup:

```bash
python scripts/start_siem.py
```

Setup only:

```bash
python scripts/start_siem.py --setup-only
```

Custom port:

```bash
python scripts/start_siem.py --port 5050
```

Windows PowerShell startup:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_siem.ps1
```

Default local URL:

```text
http://127.0.0.1:5000
```

---

## Main Modules

- **Dashboard**
- **Ingestion**
- **SignIns**
- **Risky Users**
- **Incidents**
- **Audit Logs**
- **SOC Report**
- **Truth List**
- **Alerts**
- **Admin**

---

## Repository Layout

- `backend/`: API, services, models, schemas
- `frontend/`: web interface
- `scripts/`: active operational scripts (setup/start/maintenance)
- `docs/`: technical and product documentation

Additional documentation folders preserve historical and supporting materials for traceability.

---

## Current Security Controls

The project currently includes:

- password hashing with bcrypt via Passlib;
- JWT-based authentication;
- password strength validation;
- security headers middleware;
- local audit logging for authentication events;
- encrypted backup support;
- basic account lockout behavior after repeated failed logins.

These controls are useful, but they remain part of an evolving platform rather than a fully hardened enterprise security product.

---

## Current Limitations

Known and intentional limits include:

- ingestion is still mostly based on exported Microsoft 365 data imported into the platform;
- scope is intentionally focused on Microsoft 365;
- detection logic is first-level and intentionally simple;
- SQLite is a low-cost trade-off and not designed for enterprise-scale throughput;
- schema evolution is currently managed with manual compatibility fixes;
- lockout and token/session management remain intentionally simple compared to mature enterprise IAM patterns.

These limitations are acknowledged by design.  
They reflect the project’s role as a practical and evolvable response to constrained security environments, not as a complete replacement for enterprise security platforms.

---

## Roadmap

Priority milestone: **continuous Microsoft Graph ingestion**.

Planned directions include:

1. Microsoft Graph connector via Entra App Registration
2. rule configuration externalization (thresholds, allowed countries, access windows)
3. improved schema migration strategy
4. deployment and operational hardening
5. expanded testing and observability
6. more mature configuration and security workflows

---

## Use Cases

This project is a strong fit for:

- small organizations, NGOs, and associations with constrained cybersecurity budgets;
- Microsoft 365 environments without enterprise SIEM budget;
- low-cost internal security monitoring initiatives;
- prototype or proof-of-concept SOC tooling;
- academic, demonstration, or lab environments;
- teams that want a lightweight monitoring base before investing in larger security platforms.

---

## Project Status

**Current status:** active development.

CIVIS M365 already provides a usable foundation for Microsoft 365 security ingestion, analysis, and reporting in constrained environments.

It should currently be understood as:

- a functional and evolving platform;
- a practical proposal for accessible security visibility;
- and a base that can mature over time.

---

## Contributing

Contributions are welcome, especially around:

- Microsoft Graph integration;
- detection rule improvements;
- schema migration strategy;
- deployment hardening;
- testing and observability;
- UI/UX improvements.

See `docs/policies/CONTRIBUTING.md` for contribution workflow, quality checks, and pull request expectations.

---

## Security

See `docs/policies/SECURITY.md` for vulnerability reporting, supported scope, and hardening guidance.

Do **not** commit:

- populated `.env` files,
- production credentials,
- real Microsoft 365 sensitive exports,
- or non-anonymized operational data.

---

## Historical Documentation Note

The repository contains archived and historical project documents under `docs/`.

Some of those files may still reference earlier internal naming or previous documentation states.  
The current repository root `README.md` is the main public reference for project positioning.

---

## License

This project is licensed under the MIT License. See `LICENSE`.