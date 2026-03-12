# Claw 30-min check-in script
# Runs during 8am-11pm ET (7am-10pm CDT)

$currentHour = (Get-Date).Hour
$currentMinute = (Get-Date).Minute

# CDT is UTC-5, so 7am-10pm = 12-4 (UTC) or check local
# For simplicity: skip if before 7am or after 10pm CDT
if ($currentHour -lt 7 -or $currentHour -ge 22) {
    exit 0
}

# Read last state
$stateFile = "C:\Users\firas\.openclaw\workspace\memory\checkin-state.json"
$state = @{
    lastCheck = $null
    tasksCompleted = @()
    skillsInstalled = @()
} | ConvertTo-Json

if (Test-Path $stateFile) {
    $state = Get-Content $stateFile | ConvertFrom-Json
}

# This is a placeholder - actual check-in logic will be implemented
# For now, just update the timestamp
$state | Add-Member -NotePropertyName lastCheck -NotePropertyValue (Get-Date -AsUTC) -Force
$state | ConvertTo-Json | Out-File $stateFile

# Message Firas via Discord (will be integrated with sessions_send)
Write-Host "30-min check-in: Ready to report progress to Firas"
