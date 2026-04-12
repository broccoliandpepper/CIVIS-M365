param(
    [string]$ServiceName = "SIEM-M365"
)

$ErrorActionPreference = "Stop"

function Write-Info($Message) {
    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

function Write-WarnMsg($Message) {
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Write-Ok($Message) {
    Write-Host "[OK]   $Message" -ForegroundColor Green
}

$ScriptRoot = $PSScriptRoot
$ProjectRoot = Split-Path -Parent $ScriptRoot
$RuntimeDir = Join-Path $ProjectRoot ".runtime"
$PidFile = Join-Path $RuntimeDir "$ServiceName.pid"
$StopFlag = Join-Path $RuntimeDir "$ServiceName.stop"

if (-not (Test-Path $PidFile)) {
    Write-WarnMsg "PID file not found. Service may already be stopped."
    exit 0
}

$pidValue = (Get-Content $PidFile -ErrorAction SilentlyContinue | Select-Object -First 1)
if (-not $pidValue) {
    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
    Write-WarnMsg "PID file is empty. Cleaned up."
    exit 0
}

$process = Get-Process -Id $pidValue -ErrorAction SilentlyContinue
if (-not $process) {
    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
    Write-WarnMsg "Process $pidValue is not running. Cleaned stale PID file."
    exit 0
}

New-Item -ItemType File -Path $StopFlag -Force | Out-Null
Write-Info "Stop requested for $ServiceName (PID $pidValue)"

$process.WaitForExit(8000) | Out-Null
if (-not $process.HasExited) {
    Write-WarnMsg "Graceful stop timed out. Terminating process."
    Stop-Process -Id $pidValue -Force -ErrorAction SilentlyContinue
}

Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
Write-Ok "$ServiceName stopped"
