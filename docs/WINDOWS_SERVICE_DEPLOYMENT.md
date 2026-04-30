# Deploying SIEM M365 as Windows Service

This guide explains how to run the SIEM M365 application as a Windows service for production deployment.

## Overview

Running the application as a Windows service ensures:
- Automatic startup on system boot
- Automatic restart on failure
- Service management via Windows Services UI
- Centralized logging and monitoring
- Clean process isolation

## Prerequisites

- Windows Server 2016 or higher (or Windows 10/11 for development)
- Python 3.11+ installed and in PATH
- Administrative privileges
- Virtual environment configured
- All dependencies installed from `requirements.txt`

## Option 1: Using NSSM (Non-Sucking Service Manager)

NSSM is recommended for its flexibility and easy configuration.

### Installation

1. Download NSSM from: https://nssm.cc/download
2. Extract to a permanent location (e.g., `C:\nssm`)
3. Add to PATH: `setx PATH "%PATH%;C:\nssm\win64"`

### Create Service

```batch
# From backend directory
cd C:\Users\jmaal\Documents\Jim_Tool\Siem\Siem-M365-V2\backend

# Create service pointing to venv Python
nssm install SiemM365 "C:\path\to\venv\Scripts\python.exe" "-m uvicorn app.main:app --host 0.0.0.0 --port 8000"

# Optional: Set working directory
nssm set SiemM365 AppDirectory "C:\path\to\backend"

# Optional: Set environment variables
nssm set SiemM365 AppEnvironmentExtra DATABASE_URL=sqlite:///./data/db/hot.db

# Optional: Redirect logs
nssm set SiemM365 AppStdout "C:\logs\siem-m365-stdout.log"
nssm set SiemM365 AppStderr "C:\logs\siem-m365-stderr.log"

# Optional: Set service to restart on failure
nssm set SiemM365 AppRestartDelay 5000
```

### Manage Service

```batch
# Start service
nssm start SiemM365

# Stop service
nssm stop SiemM365

# Remove service
nssm remove SiemM365 confirm

# Check service status
nssm status SiemM365

# Edit service
nssm edit SiemM365
```

## Option 2: Using Windows Task Scheduler

Good for non-critical deployments or development environments.

### Create Task

1. Open Task Scheduler (`taskschd.msc`)
2. Create Basic Task: "SIEM M365 Application"
3. Trigger: "At system startup"
4. Action:
   - Program: `C:\path\to\venv\Scripts\python.exe`
   - Arguments: `-m uvicorn app.main:app --host 0.0.0.0 --port 8000`
   - Start in: `C:\path\to\backend`

### Configure Options

- Set user account (typically Local System or Network Service)
- Enable "Run with highest privileges" if needed
- Configure retry: max 3 attempts, every 5 minutes
- Set to continue on battery power

## Option 3: Using WinSW (Windows Service Wrapper)

Good for advanced configurations and logging.

### Installation

1. Download from: https://github.com/winsw/winsw/releases
2. Rename `winsw-x.x.x-net461.exe` to `SiemM365Service.exe`
3. Place in `C:\Program Files\SiemM365`

### Configuration File

Create `SiemM365Service.xml` in same directory:

```xml
<service>
  <id>SiemM365</id>
  <name>SIEM M365 Service</name>
  <description>M365 Security Event Ingestion and Management</description>
  <executable>C:\path\to\venv\Scripts\python.exe</executable>
  <arguments>-m uvicorn app.main:app --host 0.0.0.0 --port 8000</arguments>
  <workingDirectory>C:\path\to\backend</workingDirectory>
  
  <logmode>append</logmode>
  <logpath>C:\logs</logpath>
  
  <onfailure action="restart" delay="60000" />
</service>
```

### Install Service

```batch
SiemM365Service.exe install
```

## Environment Configuration

### .env File in Backend Directory

Create `.env` file for database paths and configuration:

```env
DATABASE_HOT_URL=sqlite:///./data/db/hot.db
DATABASE_ARCHIVE_URL=sqlite:///./data/db/archive.db
DATABASE_CONFIG_URL=sqlite:///./data/db/config.db

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Security
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256

# Logging
LOG_LEVEL=INFO

# Optional proxy
# HTTP_PROXY=http://proxy:8080
# HTTPS_PROXY=http://proxy:8080
```

### Database Directory

Ensure database directory exists:

```batch
mkdir C:\path\to\backend\data\db
mkdir C:\path\to\backend\logs
icacls "C:\path\to\backend\data" /grant:r "%USERNAME%:F" /t /c
```

## Service Health Monitoring

### Health Check Endpoint

Check service status:

```batch
# Using curl (if available)
curl http://localhost:8000/api/v1/health

# Using PowerShell
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health" -UseBasicParsing

# Response
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "databases": {
    "hot": {"status": "connected"},
    "archive": {"status": "connected"},
    "config": {"status": "connected"}
  }
}
```

### Log Monitoring

Location depends on setup:
- NSSM: Configured via `nssm set` commands
- Task Scheduler: Check Event Viewer > Windows Logs > Application
- WinSW: `C:\logs\` directory

### Event Viewer

1. Open Event Viewer (`eventvwr.msc`)
2. Navigate to: Windows Logs > Application
3. Filter by source "SiemM365Service"

## Troubleshooting

### Service Won't Start

1. Check logs in Event Viewer
2. Verify Python path and virtual environment
3. Test command manually:
   ```batch
   cd C:\path\to\backend
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

### Port Already in Use

```batch
# Find process on port 8000
netstat -ano | findstr :8000

# Kill process (replace PID)
taskkill /PID <PID> /F
```

### Database Errors

- Ensure data directories exist with write permissions
- Check database files aren't locked by another process
- Verify database connection string in `.env`

### Permission Issues

If running as Network Service:

```batch
# Grant permissions to service account
icacls "C:\path\to\backend\data" /grant "NT AUTHORITY\NETWORK SERVICE:F" /t /c
icacls "C:\path\to\backend\logs" /grant "NT AUTHORITY\NETWORK SERVICE:F" /t /c
```

## Uninstalling Service

### NSSM
```batch
nssm remove SiemM365 confirm
```

### Windows Task Scheduler
1. Open Task Scheduler
2. Right-click task
3. Delete

### WinSW
```batch
SiemM365Service.exe uninstall
```

## Performance Optimization

### Uvicorn Workers

For production, use multiple worker processes:

```batch
# Modify arguments
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### FastAPI Production Settings

Set environment variables:

```batch
set APP_ENV=production
set PYTHONOPTIMIZE=2
```

## Backup Strategy

### Backup Database Files

```batch
# Scheduled backup (add to Task Scheduler)
robocopy C:\path\to\backend\data C:\backup\siem-m365 /MIR /R:3
```

### Backup Configuration

Store `.env` file separately or in configuration management system.

## Monitoring and Alerting

### Windows Performance Monitor

Monitor service metrics:
1. Open Performance Monitor (`perfmon.exe`)
2. Add counters for Process performance
3. Alert if CPU or Memory exceed thresholds

### Third-party Tools

Consider:
- Grafana + Prometheus (with custom exporter)
- Datadog
- New Relic
- Elastic APM

## References

- NSSM Documentation: https://nssm.cc/
- Uvicorn Documentation: https://www.uvicorn.org/
- FastAPI Documentation: https://fastapi.tiangolo.com/
- Windows Services: https://learn.microsoft.com/en-us/windows/win32/services/services
