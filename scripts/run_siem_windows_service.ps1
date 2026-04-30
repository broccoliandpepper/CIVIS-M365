param(
    [string]$ListenHost = "127.0.0.1",
    [int]$Port = 5000
)

$ErrorActionPreference = "Stop"

function Write-Info($Message) {
    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

$ScriptRoot = $PSScriptRoot
$ProjectRoot = Split-Path -Parent $ScriptRoot
$BackendPath = Join-Path $ProjectRoot "backend"
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $BackendPath)) {
    throw "Backend folder not found: $BackendPath"
}

if (-not (Test-Path $VenvPython)) {
    throw "Virtual environment Python not found: $VenvPython. Run scripts/install_siem_windows_service.ps1 first."
}

$previous = Get-Location
try {
    Set-Location $BackendPath
    Write-Info "Starting uvicorn on http://$ListenHost`:$Port"
    & $VenvPython -m uvicorn app.main:app --host $ListenHost --port $Port
}
finally {
    Set-Location $previous
}