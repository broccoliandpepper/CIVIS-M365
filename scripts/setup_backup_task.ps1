param(
    [string]$TaskName = "SIEM-M365-V2-SourceBackup",
    [string]$DailyAt = "20:00",
    [int]$Keep = 14
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
$backupScript = Join-Path $scriptDir "backup_snapshot.ps1"

if (-not (Test-Path $backupScript)) {
    throw "Missing script: $backupScript"
}

$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -File `"$backupScript`" -Keep $Keep"
$trigger = New-ScheduledTaskTrigger -Daily -At $DailyAt
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Description "Daily SIEM V2 source snapshot" -Force
Write-Host "Scheduled task created: $TaskName at $DailyAt"
