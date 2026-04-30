# 🏗️ SIEM M365 v1.0 — Technical Architecture & Implementation Guide

**Version**: 1.0.0  
**Last Updated**: April 30, 2026  
**Status**: PRODUCTION READY  

---

## 📑 Table of Contents

1. [System Architecture](#system-architecture)
2. [Database Design](#database-design)
3. [API Design Patterns](#api-design-patterns)
4. [Security Architecture](#security-architecture)
5. [Implementation Details](#implementation-details)
6. [Code Organization](#code-organization)
7. [Deployment Architecture](#deployment-architecture)
8. [Troubleshooting Guide](#troubleshooting-guide)

---

## 🏗️ System Architecture

### High-Level Architecture

```
┌──────────────────────────────────────────────────────────┐
│                   CLIENT LAYER                            │
│  (Web Browser / Frontend / JavaScript)                   │
└─────────────────────┬──────────────────────────────────────┘
                      │ HTTPS
                      ▼
┌──────────────────────────────────────────────────────────┐
│              API GATEWAY LAYER                            │
│  (FastAPI / Uvicorn / Security Headers)                  │
├──────────────────────────────────────────────────────────┤
│  - CORS Middleware      - Rate Limiting                  │
│  - Security Headers     - Request Validation             │
│  - JWT Authentication   - Response Compression           │
└─────────────────────┬──────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Auth Routes  │ │ API Routes   │ │ Mgmt Routes  │
│              │ │              │ │              │
│ - Login      │ │ - Query      │ │ - Health     │
│ - Logout     │ │ - Dashboard  │ │ - Status     │
│ - Me         │ │ - Export     │ │ - Lifecycle  │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                │
       └────────────────┼────────────────┘
                        ▼
┌──────────────────────────────────────────────────────────┐
│           SERVICE LAYER (Business Logic)                  │
├──────────────────────────────────────────────────────────┤
│  AuthService      │  QueryService      │  LifecycleService │
│  IngestionService │  DashboardService  │  AlertService     │
└─────────────────────┬──────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   HOT DB     │ │ ARCHIVE DB   │ │ CONFIG DB    │
│              │ │              │ │              │
│ - Current    │ │ - Historical │ │ - Secrets    │
│ - Live data  │ │ - Archived   │ │ - Settings   │
│ - 90 days    │ │ - Compressed │ │ - Backups    │
└──────────────┘ └──────────────┘ └──────────────┘
```

### Component Interaction Pattern

```
Request → Middleware → Routes → Services → Models → Database
   ↓         ↓          ↓         ↓        ↓         ↓
Validate  Headers    Validate  Business  ORM      SQL Query
  Auth    Logging    Params    Logic    Objects   Execute
          CORS       Types     Cache    Relations Result
```

---

## 🗄️ Database Design

### Data Model Architecture

#### Entity Relationship Diagram

```
┌─────────────────────────┐
│    User (CONFIG DB)     │
├─────────────────────────┤
│ id (PK)                 │
│ username                │
│ email                   │
│ password_hash (bcrypt)  │
│ role (Admin/Analyst)    │
│ is_active               │
│ created_at              │
│ last_login              │
└────────────┬────────────┘
             │ owns
             ▼
┌─────────────────────────┐
│   Session (CONFIG DB)   │
├─────────────────────────┤
│ id (PK)                 │
│ user_id (FK)            │
│ token                   │
│ created_at              │
│ expires_at              │
│ is_active               │
└─────────────────────────┘

┌──────────────────────────────┐
│  SignIn (HOT DB)             │
├──────────────────────────────┤
│ id (PK)                      │
│ event_id (UK)                │ ← Dedup key
│ user_id                      │
│ app_id                       │
│ status                       │
│ client_app_name              │
│ country                      │
│ created_at (indexed)         │
│ ingested_at                  │
└──────────────┬───────────────┘
               │ has
               ▼
┌──────────────────────────────┐
│  AnomalousSignIn (HOT DB)    │
├──────────────────────────────┤
│ id (PK)                      │
│ signin_id (FK)               │
│ anomaly_type                 │
│ risk_score (0-100)           │
│ detected_at                  │
└──────────────────────────────┘

┌──────────────────────────────┐
│  RiskyUser (HOT DB)          │
├──────────────────────────────┤
│ id (PK)                      │
│ user_id (UK)                 │
│ risk_level (Low/Med/High)    │
│ risk_factors                 │
│ last_activity_at             │
│ is_flagged                   │
│ flagged_reason               │
│ created_at                   │
└──────────────────────────────┘

┌──────────────────────────────┐
│  ArchiveManifest (ARCHIVE DB)│
├──────────────────────────────┤
│ id (PK)                      │
│ backup_id (UK)               │
│ created_at                   │
│ record_count                 │
│ compressed_size              │
│ original_size                │
│ md5_hash                     │
│ is_verified                  │
└──────────────────────────────┘
```

### Database Configuration

```python
# Three-tier database architecture
databases = {
    'HOT': {
        'url': 'sqlite:///data/siem_hot.db',
        'description': 'Current events (live, 90 days)',
        'models': ['SignIn', 'RiskyUser', 'Incident', 'IngestionLog'],
        'retention': '90 days',
        'backup': 'Daily'
    },
    'ARCHIVE': {
        'url': 'sqlite:///data/siem_archive.db',
        'description': 'Historical data (archived, compressed)',
        'models': ['ArchiveManifest', 'ArchivedSignIn'],
        'retention': '7 years',
        'backup': 'Weekly'
    },
    'CONFIG': {
        'url': 'sqlite:///data/siem_config.db',
        'description': 'Configuration & secrets',
        'models': ['User', 'Session', 'Setting', 'TruthList'],
        'retention': 'Indefinite',
        'backup': 'Daily + Replication'
    }
}
```

### Indexing Strategy

```python
# Critical indexes for performance
indexes = {
    'hot_db': {
        'SignIn': {
            'created_at': 'Range queries for date filtering',
            'user_id': 'User-centric analytics',
            'event_id': 'Deduplication',
            'status': 'Quick filtering'
        },
        'RiskyUser': {
            'user_id': 'User lookup',
            'risk_level': 'Risk filtering',
            'is_flagged': 'Alert retrieval'
        }
    },
    'archive_db': {
        'ArchiveManifest': {
            'created_at': 'Archive timeline',
            'backup_id': 'Backup lookup'
        }
    }
}
```

---

## 🔌 API Design Patterns

### RESTful Endpoint Pattern

```python
# Resource-oriented design
GET    /api/v1/{resource}              # List (paginated)
GET    /api/v1/{resource}/{id}         # Get single
POST   /api/v1/{resource}              # Create
PUT    /api/v1/{resource}/{id}         # Replace
PATCH  /api/v1/{resource}/{id}         # Partial update
DELETE /api/v1/{resource}/{id}         # Delete

# Example endpoints
GET    /api/v1/query/signins?page=1&page_size=50&status=success
GET    /api/v1/dashboard/kpis?period=7&format=json
GET    /api/v1/lifecycle/backups?sort=-created_at&limit=10
```

### Response Format Pattern

```json
{
  "status": "success",
  "code": 200,
  "message": "Operation completed",
  "data": {
    "items": [...],
    "pagination": {
      "page": 1,
      "page_size": 50,
      "total": 1000,
      "has_next": true,
      "has_prev": false
    }
  },
  "timestamp": "2026-04-30T12:00:00Z",
  "request_id": "req-12345"
}
```

### Error Response Pattern

```json
{
  "status": "error",
  "code": 400,
  "error": "VALIDATION_ERROR",
  "message": "Invalid input parameters",
  "details": {
    "field": "status",
    "issue": "Invalid enum value"
  },
  "timestamp": "2026-04-30T12:00:00Z",
  "request_id": "req-12345"
}
```

### Pagination Pattern

```python
# Query string parameters
page: int = Query(1, ge=1)                    # Page number (1-indexed)
page_size: int = Query(50, ge=1, le=500)      # Items per page
sort: str = Query('created_at', regex='.*')   # Sort field (±prefix)
filter: dict = Query(...)                     # Field filters

# Response includes pagination metadata
{
  "data": {
    "items": [...],
    "pagination": {
      "page": 1,
      "page_size": 50,
      "total": 1000,
      "pages": 20,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

---

## 🔒 Security Architecture

### Authentication Flow

```
1. User submits credentials
   ├─ POST /api/v1/auth/login
   └─ { "username": "...", "password": "..." }
                      ↓
2. Server validates
   ├─ Hash password with bcrypt
   ├─ Compare with stored hash
   ├─ Check user is active
   └─ Check role permissions
                      ↓
3. Generate JWT token
   ├─ Payload: { sub: user_id, role: role, iat: now, exp: now+24h }
   ├─ Sign with SECRET_KEY (HS256)
   └─ Return token + metadata
                      ↓
4. Client stores token (httpOnly cookie or localStorage)
                      ↓
5. Subsequent requests include token
   └─ Authorization: Bearer {token}
                      ↓
6. Server validates token
   ├─ Check signature
   ├─ Check expiry
   ├─ Extract claims
   └─ Verify permissions
```

### Authorization Rules (RBAC)

```python
# Role-based access control matrix
rbac_matrix = {
    'admin': {
        'auth': ['login', 'logout'],
        'ingest': ['create_all', 'delete_all'],
        'query': ['read_all'],
        'dashboard': ['read_all'],
        'lifecycle': ['backup_all', 'restore_all'],
        'config': ['read_all', 'update_all']
    },
    'analyst': {
        'auth': ['login', 'logout'],
        'ingest': [],
        'query': ['read_own'],
        'dashboard': ['read_own'],
        'lifecycle': [],
        'config': ['read_own']
    },
    'director': {
        'auth': ['login', 'logout'],
        'ingest': [],
        'query': ['read_all'],
        'dashboard': ['read_all', 'export_pdf'],
        'lifecycle': ['read_all'],
        'config': ['read_all']
    }
}
```

### Encryption Strategy

```python
# AES-256-GCM encryption for sensitive data
encryption_config = {
    'algorithm': 'AES-256-GCM',
    'key_size': 256,  # bits
    'iv_size': 96,    # bits (12 bytes)
    'auth_tag_size': 128,  # bits (16 bytes)
    'salt_size': 16,  # bytes
    'iterations': 100000,  # PBKDF2 iterations
    'use_case': 'Backup file encryption'
}

# Encryption flow for backup files
data → compress (gzip) → encrypt (AES-256-GCM) → compute MD5 → store
data ← decompress ← decrypt ← verify MD5 ← retrieve
```

### Security Headers

```python
security_headers = {
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Content-Security-Policy': "default-src 'self'",
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Permissions-Policy': 'geolocation=(), microphone=(), camera=()'
}
```

---

## 💻 Implementation Details

### Service Layer Implementation

```python
# Example: QueryService implementation pattern
class QueryService:
    def __init__(self, db_session):
        self.session = db_session
    
    def query_signins(self, filters: Dict, pagination: Pagination):
        """
        Execute SignIn query with filters and pagination.
        
        Flow:
        1. Build base query
        2. Apply filters
        3. Apply sorting
        4. Get total count
        5. Apply pagination
        6. Execute query
        7. Process results
        8. Return paginated response
        """
        query = self.session.query(SignIn)
        
        # Apply filters
        if filters.get('status'):
            query = query.filter(SignIn.status == filters['status'])
        if filters.get('user_id'):
            query = query.filter(SignIn.user_id == filters['user_id'])
        if filters.get('date_from'):
            query = query.filter(SignIn.created_at >= filters['date_from'])
        
        # Get total before pagination
        total = query.count()
        
        # Apply pagination
        offset = (pagination.page - 1) * pagination.page_size
        query = query.offset(offset).limit(pagination.page_size)
        
        # Execute and return
        return {
            'items': query.all(),
            'pagination': {
                'page': pagination.page,
                'page_size': pagination.page_size,
                'total': total,
                'has_next': (offset + pagination.page_size) < total
            }
        }
```

### Middleware Pattern

```python
# Example: Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    
    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000"
    
    return response

# Example: Logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing."""
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    logger.info(
        f"{request.method} {request.url.path}",
        extra={
            'status': response.status_code,
            'duration': duration,
            'user': getattr(request, 'user', 'anonymous')
        }
    )
    
    return response
```

### Error Handling Pattern

```python
# Example: Unified error handling
from fastapi import HTTPException
from typing import Any

class APIError(HTTPException):
    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        details: Any = None
    ):
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.details = details
        super().__init__(
            status_code=status_code,
            detail={"error": error_code, "message": message}
        )

# Usage in routes
@router.get("/signins")
async def get_signins(filters: SignInFilters) -> Response:
    try:
        result = query_service.query_signins(filters)
        return Response(status_code=200, data=result)
    except ValueError as e:
        raise APIError(400, "VALIDATION_ERROR", str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise APIError(500, "INTERNAL_ERROR", "An error occurred")
```

---

## 📂 Code Organization

### Directory Structure

```
siem-m365/
├── backend/
│   ├── app/
│   │   ├── __init__.py          # FastAPI app initialization
│   │   ├── main.py              # Main entry point
│   │   ├── config.py            # Configuration management
│   │   ├── database.py          # Database connection
│   │   ├── security.py          # Security utilities
│   │   │
│   │   ├── api/                 # Route handlers
│   │   │   ├── auth.py          # /auth/login, /auth/logout
│   │   │   ├── ingest.py        # /ingest/* endpoints
│   │   │   ├── query.py         # /query/* endpoints
│   │   │   ├── dashboard.py     # /dashboard/* endpoints
│   │   │   ├── lifecycle.py     # /lifecycle/* endpoints
│   │   │   ├── export.py        # /export/* endpoints
│   │   │   └── health.py        # /health endpoint
│   │   │
│   │   ├── models/              # SQLAlchemy models
│   │   │   ├── auth.py          # User, Session
│   │   │   ├── signins.py       # SignIn, RiskySignIn
│   │   │   ├── audit.py         # AuditLog
│   │   │   ├── incidents.py     # Incident
│   │   │   └── ...
│   │   │
│   │   ├── services/            # Business logic
│   │   │   ├── auth_service.py
│   │   │   ├── query_service.py
│   │   │   ├── dashboard_service.py
│   │   │   └── ...
│   │   │
│   │   ├── schemas/             # Pydantic request/response models
│   │   │   ├── auth.py
│   │   │   ├── query.py
│   │   │   └── ...
│   │   │
│   │   └── middleware/          # ASGI middleware
│   │       └── security_headers.py
│   │
│   ├── tests/                   # Test files
│   │   ├── test_sprint2.py
│   │   ├── test_sprint3.py
│   │   ├── test_sprint4.py
│   │   ├── test_sprint5.py
│   │   └── test_sprint6_final.py
│   │
│   ├── scripts/                 # Utility scripts
│   │   ├── init_db.py
│   │   ├── start_siem.py
│   │   └── ...
│   │
│   ├── requirements.txt         # Dependencies
│   ├── .env.example             # Environment template
│   └── config.yaml              # Configuration
│
├── frontend/
│   └── index.html               # Single-page application
│
├── data/                        # Data directory
│   ├── db/                      # Databases (created at runtime)
│   ├── backups/                 # Backup files
│   └── config/                  # Configuration files
│
└── docs/                        # Documentation
    ├── README.md
    ├── ARCHITECTURE.md
    └── ...
```

---

## 🚀 Deployment Architecture

### Development Environment

```bash
# Local development setup
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Environment

```bash
# Production setup with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 \
  --timeout 120 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log \
  --log-level info \
  app.main:app
```

### Docker Deployment

```dockerfile
# Multi-stage build
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
EXPOSE 5000
CMD ["python", "scripts/start_siem.py"]
```

### Kubernetes Deployment (Future)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: siem-api
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: api
        image: siem-m365:1.0.0
        ports:
        - containerPort: 5000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: siem-secrets
              key: db-url
        livenessProbe:
          httpGet:
            path: /api/v1/health
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
```

---

## 🔧 Troubleshooting Guide

### Common Issues & Solutions

#### Issue 1: Database Connection Error
```
Error: sqlite3.OperationalError: unable to open database file
```
**Solution**:
```bash
# Ensure data directory exists
mkdir -p data/db

# Initialize database
python scripts/init_db.py

# Check permissions
ls -la data/db/
```

#### Issue 2: Authentication Token Invalid
```
Error: 401 Unauthorized - Invalid token
```
**Solution**:
```bash
# Check token expiry in JWT
# Default: 24 hours

# Regenerate token
POST /api/v1/auth/login

# Verify SECRET_KEY is configured
echo $SECRET_KEY
```

#### Issue 3: Slow Query Performance
```
Problem: Query endpoint takes > 2 seconds
```
**Solution**:
```python
# Check indexes are created
SELECT sql FROM sqlite_master WHERE type='index';

# Analyze query plan
EXPLAIN QUERY PLAN SELECT * FROM signin WHERE user_id = ?;

# Add missing index if needed
CREATE INDEX idx_signin_user_id ON signin(user_id);
```

#### Issue 4: Backup Verification Failing
```
Error: Backup verification failed - MD5 mismatch
```
**Solution**:
```bash
# Check backup file integrity
md5sum data/backups/backup_*.db.gz

# Verify encryption
file data/backups/backup_*.db.gz

# Restore from previous backup
POST /api/v1/lifecycle/backup/{id}/restore
```

#### Issue 5: Memory Usage Growing
```
Problem: Memory usage increasing over time
```
**Solution**:
```python
# Check for connection leaks
import gc
gc.collect()

# Monitor database connections
SELECT count(*) FROM sqlite_master;

# Restart application
systemctl restart siem-api
```

---

## 📊 Monitoring & Observability

### Key Metrics to Monitor

```python
metrics = {
    'availability': {
        'target': 99.9,
        'measure': 'Uptime percentage'
    },
    'performance': {
        'p50': '100ms',
        'p95': '500ms',
        'p99': '2000ms'
    },
    'errors': {
        'rate': '< 0.1%',
        'types': ['4xx', '5xx']
    },
    'database': {
        'connections': 'Pool size',
        'latency': 'Query time',
        'size': 'DB file size'
    }
}
```

### Health Check Endpoint

```
GET /api/v1/health
Response: {
  "status": "healthy",
  "database": "connected",
  "timestamp": "2026-04-30T12:00:00Z",
  "version": "1.0.0"
}
```

---

## 🎓 Best Practices

### API Design
- ✅ Use RESTful conventions
- ✅ Version your API (/api/v1/)
- ✅ Use consistent response formats
- ✅ Implement proper pagination
- ✅ Document with OpenAPI/Swagger

### Database
- ✅ Use connection pooling
- ✅ Create appropriate indexes
- ✅ Implement soft deletes
- ✅ Audit sensitive changes
- ✅ Regular backups & tests

### Security
- ✅ Always use HTTPS
- ✅ Validate all inputs
- ✅ Sanitize outputs
- ✅ Use secure hashing (bcrypt)
- ✅ Rotate secrets regularly

### Performance
- ✅ Implement caching
- ✅ Use database indexes
- ✅ Paginate large results
- ✅ Monitor slow queries
- ✅ Profile code regularly

### Operations
- ✅ Comprehensive logging
- ✅ Health monitoring
- ✅ Automated backups
- ✅ Disaster recovery plan
- ✅ Runbook documentation

---

## 📞 Support & Resources

### Documentation
- API Reference: [API.md](API.md)
- Deployment Guide: [DEPLOYMENT.md](DEPLOYMENT.md)
- Security Guidelines: [SECURITY.md](SECURITY.md)

### Getting Help
1. Check documentation
2. Review logs: `tail -f logs/app.log`
3. Run diagnostics: `python scripts/diagnose.py`
4. Contact support with logs and reproduction steps

---

**SIEM M365 v1.0 Technical Architecture**  
*Comprehensive, production-ready security event management platform*  
*Built on FastAPI, SQLAlchemy, and modern best practices*
