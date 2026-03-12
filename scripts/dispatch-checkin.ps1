# dispatch-checkin.ps1 - Generate check-in and send to Firas via Discord
# Called by Windows Task Scheduler every 30 minutes

$pythonScript = "C:\Users\firas\.openclaw\workspace\scripts\discord-checkin.py"
$logFile = "C:\Users\firas\.openclaw\workspace\logs\checkin-dispatch.log"

# Ensure logs directory exists
$logDir = Split-Path $logFile
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Force $logDir | Out-Null
}

# Generate check-in message JSON
$messageJson = python $pythonScript

if ($LASTEXITCODE -ne 0) {
    "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ERROR: Failed to generate check-in" | Add-Content $logFile
    exit 1
}

# Log successful generation
"$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') Generated check-in message ($(($messageJson | Measure-Object -Character).Characters) bytes)" | Add-Content $logFile

# Save message JSON for manual dispatch or debugging
$messageJson | Out-File -FilePath "C:\Users\firas\.openclaw\workspace\logs\latest-checkin.json"

# NOTE: To actually send to Discord, you would call OpenClaw's message tool here
# For now, this generates the message payload that can be dispatched manually or via sessions_send
