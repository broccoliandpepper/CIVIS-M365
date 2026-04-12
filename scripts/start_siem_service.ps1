param(
    [string]$ListenHost = "127.0.0.1",
    [int]$Port = 5000,
    [string]$ServiceName = "SIEM-M365",
    [int]$RestartDelaySeconds = 5,
    [switch]$SkipPythonInstall,
    [switch]$RunLoop
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
$BackendPath = Join-Path $ProjectRoot "backend"
$StarterPath = Join-Path $ScriptRoot "start_siem.ps1"
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$RuntimeDir = Join-Path $ProjectRoot ".runtime"
$LogsDir = Join-Path $ProjectRoot "logs"
$PidFile = Join-Path $RuntimeDir "$ServiceName.pid"
$StopFlag = Join-Path $RuntimeDir "$ServiceName.stop"
$LogFile = Join-Path $LogsDir "$ServiceName.log"

if (-not (Test-Path $RuntimeDir)) {
    New-Item -ItemType Directory -Path $RuntimeDir | Out-Null
}
if (-not (Test-Path $LogsDir)) {
    New-Item -ItemType Directory -Path $LogsDir | Out-Null
}

if ($RunLoop) {
    Write-Info "Starting service loop: $ServiceName"
    Write-Info "Logs: $LogFile"

    while ($true) {
        if (Test-Path $StopFlag) {
            Remove-Item $StopFlag -Force
            Add-Content -Path $LogFile -Value "[$(Get-Date -Format o)] Stop flag detected before launch. Exiting loop."
            break
        }

        Add-Content -Path $LogFile -Value "[$(Get-Date -Format o)] Launching uvicorn on http://$ListenHost`:$Port"

        $previous = Get-Location
        try {
            Set-Location $BackendPath
            & $VenvPython -m uvicorn app.main:app --host $ListenHost --port $Port *>> $LogFile
            $exitCode = $LASTEXITCODE
        }
        finally {
            Set-Location $previous
        }

        Add-Content -Path $LogFile -Value "[$(Get-Date -Format o)] Uvicorn exited with code $exitCode"

        if (Test-Path $StopFlag) {
            Remove-Item $StopFlag -Force
            Add-Content -Path $LogFile -Value "[$(Get-Date -Format o)] Stop requested. Service loop terminated."
            break
        }

        Add-Content -Path $LogFile -Value "[$(Get-Date -Format o)] Restart in $RestartDelaySeconds second(s)"
        Start-Sleep -Seconds $RestartDelaySeconds
    }

    exit 0
}

if (Test-Path $PidFile) {
    $existingPid = (Get-Content $PidFile -ErrorAction SilentlyContinue | Select-Object -First 1)
    if ($existingPid) {
        $existingProcess = Get-Process -Id $existingPid -ErrorAction SilentlyContinue
        if ($existingProcess) {
            Write-WarnMsg "$ServiceName already running with PID $existingPid"
            exit 0
        }
    }
    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
}

Write-Info "Running setup phase"
$setupArgs = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", $StarterPath,
    "-ListenHost", $ListenHost,
    "-Port", $Port,
    "-SetupOnly"
)
if ($SkipPythonInstall) {
    $setupArgs += "-SkipPythonInstall"
}

& powershell @setupArgs
if ($LASTEXITCODE -ne 0) {
    throw "Setup phase failed. Service not started."
}

if (-not (Test-Path $VenvPython)) {
    throw "Virtual environment Python not found at $VenvPython"
}

Write-Info "Starting $ServiceName in background"
$loopArgs = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", $PSCommandPath,
    "-RunLoop",
    "-ListenHost", $ListenHost,
    "-Port", $Port,
    "-ServiceName", $ServiceName,
    "-RestartDelaySeconds", $RestartDelaySeconds
)
if ($SkipPythonInstall) {
    $loopArgs += "-SkipPythonInstall"
}

$process = Start-Process -FilePath "powershell" -ArgumentList $loopArgs -WindowStyle Hidden -PassThru
$process.Id | Set-Content -Path $PidFile -Encoding ASCII

Write-Ok "$ServiceName started"
Write-Host "      PID: $($process.Id)"
Write-Host "      URL: http://$ListenHost`:$Port"
Write-Host "      Log: $LogFile"
Write-Host "      Stop: powershell -ExecutionPolicy Bypass -File .\scripts\stop_siem_service.ps1 -ServiceName $ServiceName"
