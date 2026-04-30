# PowerShell Script to Install SIEM M365 as Windows Service
# Run with: powershell -ExecutionPolicy Bypass -File install_service.ps1

param(
    [string]$AppPath = $null,
    [string]$VenvPath = $null,
    [string]$Port = "8000",
    [string]$ServiceName = "SiemM365",
    [string]$LogPath = $null,
    [string]$Method = "nssm"  # Options: nssm, winsw, scheduler
)

function Write-Header {
    param([string]$Message)
    Write-Host "`n================================" -ForegroundColor Cyan
    Write-Host $Message -ForegroundColor Cyan
    Write-Host "================================`n" -ForegroundColor Cyan
}

function Write-Error-Message {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Red
}

function Write-Success {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Green
}

# Check if running as Administrator
if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Error-Message "ERROR: This script must be run as Administrator"
    exit 1
}

# Prompt for paths if not provided
if (-not $AppPath) {
    Write-Host "Enter the path to SIEM M365 backend directory: " -NoNewline
    $AppPath = Read-Host
}

if (-not $VenvPath) {
    Write-Host "Enter the path to Python virtual environment: " -NoNewline
    $VenvPath = Read-Host
}

if (-not $LogPath) {
    $LogPath = Join-Path $AppPath "logs"
}

# Verify paths exist
if (-not (Test-Path $AppPath)) {
    Write-Error-Message "ERROR: App path does not exist: $AppPath"
    exit 1
}

if (-not (Test-Path $VenvPath)) {
    Write-Error-Message "ERROR: Venv path does not exist: $VenvPath"
    exit 1
}

$PythonExe = Join-Path $VenvPath "Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    Write-Error-Message "ERROR: Python executable not found: $PythonExe"
    exit 1
}

# Create logs directory
if (-not (Test-Path $LogPath)) {
    New-Item -ItemType Directory -Path $LogPath -Force | Out-Null
    Write-Success "Created logs directory: $LogPath"
}

Write-Header "SIEM M365 Service Installation"
Write-Host "Configuration:"
Write-Host "  App Path: $AppPath"
Write-Host "  Venv Path: $VenvPath"
Write-Host "  Python: $PythonExe"
Write-Host "  Port: $Port"
Write-Host "  Service Name: $ServiceName"
Write-Host "  Log Path: $LogPath"
Write-Host "  Method: $Method"

# Method 1: NSSM Installation
if ($Method -eq "nssm") {
    Write-Header "Installing service using NSSM"
    
    # Check if NSSM is installed
    $nssmPath = Get-Command nssm -ErrorAction SilentlyContinue
    if (-not $nssmPath) {
        Write-Error-Message "ERROR: NSSM not found in PATH"
        Write-Host "Download from: https://nssm.cc/download" -ForegroundColor Yellow
        exit 1
    }
    
    # Check if service already exists
    $existingService = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($existingService) {
        Write-Host "Service $ServiceName already exists. Removing..." -ForegroundColor Yellow
        nssm remove $ServiceName confirm
        Start-Sleep -Seconds 2
    }
    
    # Build command
    $uvicornArgs = "-m uvicorn app.main:app --host 0.0.0.0 --port $Port"
    
    # Install service
    Write-Host "Installing service..." -ForegroundColor Cyan
    nssm install $ServiceName "`"$PythonExe`"" "$uvicornArgs"
    if ($LASTEXITCODE -ne 0) {
        Write-Error-Message "ERROR: Failed to install service"
        exit 1
    }
    
    # Configure service
    Write-Host "Configuring service..." -ForegroundColor Cyan
    nssm set $ServiceName AppDirectory "$AppPath"
    nssm set $ServiceName AppStdout "$LogPath\${ServiceName}_stdout.log"
    nssm set $ServiceName AppStderr "$LogPath\${ServiceName}_stderr.log"
    nssm set $ServiceName AppRestartDelay 5000
    nssm set $ServiceName AppRotateFiles 1
    nssm set $ServiceName AppRotateOnline 1
    nssm set $ServiceName AppRotateSeconds 3600
    nssm set $ServiceName AppRotateBytes 10485760  # 10 MB
    
    Write-Success "Service installed successfully"
    Write-Host "`nTo start the service, run:"
    Write-Host "  nssm start $ServiceName" -ForegroundColor Yellow
}

# Method 2: WinSW Installation
elseif ($Method -eq "winsw") {
    Write-Header "Installing service using WinSW"
    
    $winsw = "$AppPath\..\..\bin\SiemM365Service.exe"
    if (-not (Test-Path $winsw)) {
        Write-Error-Message "ERROR: WinSW executable not found: $winsw"
        Write-Host "Download from: https://github.com/winsw/winsw/releases" -ForegroundColor Yellow
        exit 1
    }
    
    # Create configuration file
    $configPath = "$AppPath\..\..\bin\SiemM365Service.xml"
    $uvicornArgs = "-m uvicorn app.main:app --host 0.0.0.0 --port $Port"
    
    $configContent = @"
<?xml version="1.0" encoding="UTF-8"?>
<service>
  <id>$ServiceName</id>
  <name>SIEM M365 Service</name>
  <description>M365 Security Event Ingestion and Management</description>
  <executable>`"$PythonExe`"</executable>
  <arguments>$uvicornArgs</arguments>
  <workingDirectory>$AppPath</workingDirectory>
  
  <logmode>append</logmode>
  <logpath>$LogPath</logpath>
  <loglevel>Info</loglevel>
  
  <onfailure action="restart" delay="60000" />
  
  <env name="APP_ENV" value="production" />
</service>
"@
    
    Set-Content -Path $configPath -Value $configContent -Encoding UTF8
    Write-Success "Created configuration file: $configPath"
    
    # Install service
    Write-Host "Installing service..." -ForegroundColor Cyan
    & $winsw install
    
    Write-Success "Service installed successfully"
    Write-Host "`nTo start the service, run:"
    Write-Host "  $winsw start" -ForegroundColor Yellow
}

# Method 3: Task Scheduler Installation
elseif ($Method -eq "scheduler") {
    Write-Header "Installing service using Windows Task Scheduler"
    
    $taskName = $ServiceName
    $action = New-ScheduledTaskAction -Execute $PythonExe `
        -Argument "-m uvicorn app.main:app --host 0.0.0.0 --port $Port" `
        -WorkingDirectory $AppPath
    
    $trigger = New-ScheduledTaskTrigger -AtStartup
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries -RunOnlyIfNetworkAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 5)
    
    $principal = New-ScheduledTaskPrincipal -UserId "NT AUTHORITY\SYSTEM" -RunLevel Highest
    
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger `
        -Settings $settings -Principal $principal -Force | Out-Null
    
    Write-Success "Task Scheduler entry created: $taskName"
}

else {
    Write-Error-Message "ERROR: Unknown installation method: $Method"
    exit 1
}

Write-Header "Installation Complete"
Write-Host "Next steps:"
Write-Host "1. Review service configuration"
Write-Host "2. Set startup user if needed (use Services.msc)"
Write-Host "3. Start the service"
Write-Host "4. Verify with: curl http://localhost:$Port/api/v1/health"
Write-Host "`nFor logs, check: $LogPath"

# Grant permissions to NETWORK SERVICE if needed
Write-Host "`nGranting permissions to data directory..." -ForegroundColor Cyan
$currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().User
$acl = Get-Acl $AppPath
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule("NT AUTHORITY\NETWORK SERVICE", "Modify", "ContainerInherit,ObjectInherit", "None", "Allow")
$acl.SetAccessRule($rule)
Set-Acl -Path $AppPath -AclObject $acl
Write-Success "Permissions updated"
