param(
    [string]$ListenHost = "127.0.0.1",
    [int]$Port = 5000,
    [switch]$SkipPythonInstall,
    [switch]$SetupOnly
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

function Test-CommandExists($Name) {
    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

# Returns hashtable { Exe; Args; Version } for a compatible Python (3.12/3.11 preferred).
# Python 3.14+ lacks pre-built wheels for several packages and requires MSVC to compile.
function Find-CompatiblePython {
    # Try py launcher with preferred versions in order
    if (Test-CommandExists "py") {
        foreach ($ver in @("3.12", "3.11", "3.13")) {
            try {
                & py "-$ver" -c "import sys" *> $null
                if ($LASTEXITCODE -eq 0) {
                    Write-Ok "Found Python $ver via py launcher"
                    return @{ Exe = "py"; Args = @("-$ver"); Version = $ver }
                }
            }
            catch {
                continue
            }
        }
    }

    # Fallback: check 'python' command version
    if (Test-CommandExists "python") {
        try {
            $verInfo = & python -c "import sys; print(sys.version_info.major, sys.version_info.minor)" 2>$null
            if ($LASTEXITCODE -eq 0) {
                $parts = $verInfo.Trim().Split(' ')
                $major = [int]$parts[0]; $minor = [int]$parts[1]
                if ($major -eq 3 -and $minor -le 13) {
                    Write-Ok "Found system Python $major.$minor"
                    return @{ Exe = "python"; Args = @(); Version = "$major.$minor" }
                }
                # 3.14+: warn but allow continuation; script will try anyway
                Write-WarnMsg "System Python is $major.$minor. Some packages lack pre-built wheels for this version."
                Write-WarnMsg "Install Python 3.12 to avoid compilation errors: winget install Python.Python.3.12"
                return @{ Exe = "python"; Args = @(); Version = "$major.$minor" }
            }
        }
        catch {
            Write-WarnMsg "System Python command exists but could not be queried."
        }
    }

    # No Python found – install 3.12
    if ($SkipPythonInstall) {
        throw "Python not found and -SkipPythonInstall was specified. Install Python 3.12 from https://python.org"
    }
    if (-not (Test-CommandExists "winget")) {
        throw "winget not available. Install Python 3.12 from https://python.org"
    }
    Write-Info "Installing Python 3.12 via winget..."
    winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements
    if (Test-CommandExists "py") {
        $null = & py -3.12 -c "import sys" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Ok "Python 3.12 installed"
            return @{ Exe = "py"; Args = @("-3.12"); Version = "3.12" }
        }
    }
    throw "Python 3.12 installed but not yet accessible. Open a new terminal and re-run the script."
}

function Invoke-PythonJson([string]$PythonExe, [string]$Code, [string]$WorkingDirectory) {
    $previous = Get-Location
    try {
        Set-Location $WorkingDirectory
        $output = & $PythonExe -c $Code
        if ($LASTEXITCODE -ne 0) {
            throw "Python command failed"
        }
        return $output | ConvertFrom-Json
    }
    finally {
        Set-Location $previous
    }
}

$ScriptRoot = $PSScriptRoot
$ProjectRoot = Split-Path -Parent $ScriptRoot
$BackendPath = Join-Path $ProjectRoot "backend"
$RequirementsPath = Join-Path $BackendPath "requirements.txt"
$EnvPath = Join-Path $BackendPath ".env"
$VenvPath = Join-Path $ProjectRoot ".venv"
$VenvPython = Join-Path $VenvPath "Scripts\python.exe"
$InitDbScript = Join-Path $ProjectRoot "scripts\init_db.py"

Write-Info "Project root: $ProjectRoot"

if (-not (Test-Path $BackendPath)) {
    throw "Backend folder not found: $BackendPath"
}

if (-not (Test-Path $RequirementsPath)) {
    throw "requirements.txt not found: $RequirementsPath"
}

$PyInfo = Find-CompatiblePython

# If an existing venv was built with a different Python version, delete and recreate it
if (Test-Path $VenvPython) {
    $venvVerInfo = & $VenvPython -c "import sys; print(sys.version_info.major, sys.version_info.minor)" 2>&1
    if ($LASTEXITCODE -eq 0) {
        $vp = $venvVerInfo.Trim().Split(' ')
        $venvVerStr = "$($vp[0]).$($vp[1])"
        if ($venvVerStr -ne $PyInfo.Version) {
            Write-WarnMsg "Existing venv uses Python $venvVerStr but $($PyInfo.Version) is selected. Recreating..."
            Remove-Item -Recurse -Force $VenvPath
        }
    }
}

if (-not (Test-Path $VenvPython)) {
    Write-Info "Creating virtual environment (Python $($PyInfo.Version)) at $VenvPath"
    & $PyInfo.Exe @($PyInfo.Args + @("-m", "venv", $VenvPath))
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create virtual environment"
    }
    Write-Ok "Virtual environment created"
}
else {
    Write-Ok "Virtual environment already exists (Python $($PyInfo.Version))"
}

Write-Info "Installing/updating Python dependencies"
& $VenvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    throw "Failed to upgrade pip"
}

& $VenvPython -m pip install -r $RequirementsPath
if ($LASTEXITCODE -ne 0) {
    throw "Failed to install requirements"
}
Write-Ok "Dependencies ready"

if (-not (Test-Path $EnvPath)) {
    Write-WarnMsg ".env not found in backend. Creating default .env file."
    @"
APP_NAME=SIEM_M365
APP_ENV=development
DEBUG=False
DB_ENCRYPTION_KEY=siem-m365-secure-32byte-key!!
JWT_SECRET_KEY=siem-m365-jwt-secret-key-2024!
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30
BACKUP_ENCRYPTION_KEY=siem-m365-backup-32byte-key!!
DB_PATH=./data/db/siem_hot.db
DB_ARCHIVE_PATH=./data/db/siem_archive.db
DB_CONFIG_PATH=./data/db/siem_config.db
BACKUP_PATH=./data/backups
HOST=127.0.0.1
PORT=5000
PASSWORD_MIN_LENGTH=12
PASSWORD_REQUIRE_SPECIAL=True
"@ | Set-Content -Path $EnvPath -Encoding UTF8
    Write-Ok "Default .env created"
}
else {
    Write-Ok ".env already exists"
}

Write-Info "Checking database files"
$dbPaths = Invoke-PythonJson -PythonExe $VenvPython -WorkingDirectory $BackendPath -Code "import json; from app.config import settings; print(json.dumps(settings.db_paths))"

$missingDb = @()
$resolvedDb = @{}
foreach ($name in $dbPaths.PSObject.Properties.Name) {
    $dbPath = [string]$dbPaths.$name
    $resolved = if ([System.IO.Path]::IsPathRooted($dbPath)) { $dbPath } else { Join-Path $BackendPath $dbPath }
    $resolvedDb[$name] = $resolved
    if (-not (Test-Path $resolved)) {
        $missingDb += $resolved
    }
}

if ($missingDb.Count -gt 0) {
    Write-WarnMsg "Database files missing. Initializing databases and admin account..."
    & $VenvPython $InitDbScript
    if ($LASTEXITCODE -ne 0) {
        throw "Database initialization failed"
    }
    Write-Ok "Databases initialized"
}
else {
    Write-Ok "Database files already exist"
    foreach ($name in $resolvedDb.Keys) {
        Write-Host "       ${name}: $($resolvedDb[$name])"
    }

    Write-Info "Applying schema updates/checks"
    $previous = Get-Location
    try {
        Set-Location $BackendPath
        & $VenvPython -c "from app.database import init_db_on_startup; init_db_on_startup(); print('DB_SCHEMA_OK')"
        if ($LASTEXITCODE -ne 0) {
            throw "Database schema check failed"
        }
    }
    finally {
        Set-Location $previous
    }
    Write-Ok "Database schema is ready"
}

Write-Info "Launching SIEM API at http://$ListenHost`:$Port"
Write-Info "Press Ctrl+C to stop"

if ($SetupOnly) {
    Write-Ok "Setup completed (SetupOnly mode)."
    exit 0
}

$previous = Get-Location
try {
    Set-Location $BackendPath
    & $VenvPython -m uvicorn app.main:app --host $ListenHost --port $Port
}
finally {
    Set-Location $previous
}
