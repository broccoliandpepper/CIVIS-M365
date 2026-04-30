param(
    [string]$ServiceName = "SIEM-M365",
    [switch]$RemoveWrapperFiles
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

if (-not (Test-IsAdministrator)) {
    throw "Administrator rights are required to uninstall a Windows service. Re-run PowerShell as Administrator."
}

$ScriptRoot = $PSScriptRoot
$ProjectRoot = Split-Path -Parent $ScriptRoot
$RuntimeRoot = Join-Path $ProjectRoot ".runtime\windows-service"
$WrapperExe = Join-Path $RuntimeRoot "$ServiceName.exe"
$WrapperXml = Join-Path $RuntimeRoot "$ServiceName.xml"

$service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if (-not $service) {
    Write-WarnMsg "Service '$ServiceName' not found."
}
else {
    if (Test-Path $WrapperExe) {
        Write-Info "Stopping Windows service $ServiceName"
        & $WrapperExe stop | Out-Null
        Write-Info "Uninstalling Windows service $ServiceName"
        & $WrapperExe uninstall | Out-Null
    }
    else {
        Write-WarnMsg "Wrapper executable not found. Falling back to sc.exe delete."
        sc.exe stop $ServiceName | Out-Null
        sc.exe delete $ServiceName | Out-Null
    }
}

if ($RemoveWrapperFiles) {
    Remove-Item -Path $WrapperExe -Force -ErrorAction SilentlyContinue
    Remove-Item -Path $WrapperXml -Force -ErrorAction SilentlyContinue
}

Write-Ok "Windows service removal completed"