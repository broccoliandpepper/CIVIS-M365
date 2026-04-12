param(
    [int]$Keep = 14
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
$pythonExe = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
    Write-Error "Python venv not found at $pythonExe. Run: python scripts/start_siem.py --setup-only"
}

& $pythonExe (Join-Path $scriptDir "backup_snapshot.py") --keep $Keep
