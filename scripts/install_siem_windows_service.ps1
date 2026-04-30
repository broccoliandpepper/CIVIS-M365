param(
    [string]$ServiceName = "SIEM-M365",
    [string]$DisplayName = "SIEM M365",
    [string]$Description = "SIEM M365 FastAPI service managed by WinSW",
    [string]$ListenHost = "127.0.0.1",
    [int]$Port = 5000,
    [string]$WinSWVersion = "v2.12.0",
    [string]$WinSWDownloadUrl,
    [switch]$SkipPythonInstall,
    [switch]$StartAfterInstall
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

function Test-IsAdministrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Escape-Xml([string]$Value) {
    return [System.Security.SecurityElement]::Escape($Value)
}

if (-not (Test-IsAdministrator)) {
    throw "Administrator rights are required to install a Windows service. Re-run PowerShell as Administrator."
}

$ScriptRoot = $PSScriptRoot
$ProjectRoot = Split-Path -Parent $ScriptRoot
$RuntimeRoot = Join-Path $ProjectRoot ".runtime\windows-service"
$LogsRoot = Join-Path $ProjectRoot "logs\windows-service"
$BootstrapScript = Join-Path $ScriptRoot "start_siem.ps1"
$RunnerScript = Join-Path $ScriptRoot "run_siem_windows_service.ps1"
$ServiceBaseName = $ServiceName
$WrapperExe = Join-Path $RuntimeRoot "$ServiceBaseName.exe"
$WrapperXml = Join-Path $RuntimeRoot "$ServiceBaseName.xml"
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $BootstrapScript)) {
    throw "Bootstrap script not found: $BootstrapScript"
}

if (-not (Test-Path $RunnerScript)) {
    throw "Service runner script not found: $RunnerScript"
}

if (Get-Service -Name $ServiceName -ErrorAction SilentlyContinue) {
    throw "Service '$ServiceName' already exists. Uninstall it first or choose another name."
}

New-Item -ItemType Directory -Path $RuntimeRoot -Force | Out-Null
New-Item -ItemType Directory -Path $LogsRoot -Force | Out-Null

Write-Info "Running setup phase before service installation"
$setupArgs = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", $BootstrapScript,
    "-ListenHost", $ListenHost,
    "-Port", $Port,
    "-SetupOnly"
)
if ($SkipPythonInstall) {
    $setupArgs += "-SkipPythonInstall"
}

& powershell @setupArgs
if ($LASTEXITCODE -ne 0) {
    throw "Setup phase failed. Service installation aborted."
}

if (-not (Test-Path $VenvPython)) {
    throw "Virtual environment Python not found after setup: $VenvPython"
}

if (-not $WinSWDownloadUrl) {
    $WinSWDownloadUrl = "https://github.com/winsw/winsw/releases/download/$WinSWVersion/WinSW-x64.exe"
}

if (Test-Path $WrapperExe) {
    Write-Ok "Using existing WinSW wrapper: $WrapperExe"
}
else {
    Write-Info "Downloading WinSW wrapper from $WinSWDownloadUrl"
    Invoke-WebRequest -Uri $WinSWDownloadUrl -OutFile $WrapperExe
}

$xmlContent = @"
<service>
  <id>$(Escape-Xml $ServiceName)</id>
  <name>$(Escape-Xml $DisplayName)</name>
  <description>$(Escape-Xml $Description)</description>
  <executable>powershell.exe</executable>
  <arguments>-NoProfile -ExecutionPolicy Bypass -File &quot;$(Escape-Xml $RunnerScript)&quot; -ListenHost $(Escape-Xml $ListenHost) -Port $Port</arguments>
  <workingdirectory>$(Escape-Xml $ProjectRoot)</workingdirectory>
  <logpath>$(Escape-Xml $LogsRoot)</logpath>
  <log mode="roll-by-size">
    <sizeThreshold>10240</sizeThreshold>
    <keepFiles>8</keepFiles>
  </log>
  <startmode>Automatic</startmode>
  <stoptimeout>15000</stoptimeout>
  <onfailure action="restart" delay="10 sec" />
  <onfailure action="restart" delay="20 sec" />
  <onfailure action="none" />
</service>
"@
Set-Content -Path $WrapperXml -Value $xmlContent -Encoding UTF8

Write-Info "Installing Windows service $ServiceName"
& $WrapperExe install
if ($LASTEXITCODE -ne 0) {
    throw "WinSW install command failed."
}

if ($StartAfterInstall) {
    Write-Info "Starting Windows service $ServiceName"
    & $WrapperExe start
    if ($LASTEXITCODE -ne 0) {
        throw "WinSW start command failed."
    }
}
else {
    Write-WarnMsg "Service installed but not started. Use Services.msc or the wrapper executable to start it."
}

Write-Ok "Windows service ready"
Write-Host "      Name: $ServiceName"
Write-Host "      URL: http://$ListenHost`:$Port"
Write-Host "      Wrapper: $WrapperExe"
Write-Host "      Config: $WrapperXml"
Write-Host "      Logs: $LogsRoot"