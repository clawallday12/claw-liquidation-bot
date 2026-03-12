# isolated-exec.ps1 - Run Python scripts in isolated venv

param(
    [string]$ScriptPath,
    [string]$VenvName = "isolated-env",
    [string[]]$Requirements = @()
)

# Create isolated virtual environment
$venvPath = "C:\Users\firas\.openclaw\workspace\.venv\$VenvName"

if (-not (Test-Path $venvPath)) {
    Write-Host "Creating isolated environment: $venvName"
    python -m venv $venvPath
}

# Activate venv and install requirements
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
& $activateScript

if ($Requirements.Count -gt 0) {
    Write-Host "Installing requirements: $Requirements"
    pip install @Requirements
}

# Run the script
Write-Host "Running script: $ScriptPath"
python $ScriptPath

# Note: venv remains for reuse (not destroyed after execution)
Write-Host "Isolated execution complete. Environment persists at: $venvPath"
