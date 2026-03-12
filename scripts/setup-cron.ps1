# Setup Claw 30-min check-in scheduled task

$taskName = 'Claw-Checkin-30min'
$scriptPath = 'C:\Users\firas\.openclaw\workspace\scripts\checkin.ps1'

# Create trigger for every 30 minutes
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 30) -RepetitionDuration (New-TimeSpan -Days 365)

# Create action to run the check-in script
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -ExecutionPolicy Bypass -File $scriptPath"

# Create settings
$settings = New-ScheduledTaskSettingsSet -RunOnlyIfNetworkAvailable -StartWhenAvailable

# Register the scheduled task
Register-ScheduledTask -TaskName $taskName -Trigger $trigger -Action $action -Settings $settings -Force | Out-Null

# Verify it was created
Get-ScheduledTask -TaskName $taskName | Select-Object TaskName, State
Write-Host "Scheduled task '$taskName' created successfully."
