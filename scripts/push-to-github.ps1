# push-to-github.ps1 - Push code to GitHub repo

param(
    [string]$GitHubToken = $env:GITHUB_TOKEN,
    [string]$RepoName = "claw-liquidation-bot"
)

$WorkspaceDir = "C:\Users\firas\.openclaw\workspace"
$GitHubUser = "clawallday12"

if (-not $GitHubToken) {
    Write-Host "[!] GITHUB_TOKEN environment variable not set"
    Write-Host "[!] Set it or pass --GitHubToken parameter"
    Write-Host ""
    Write-Host "To create a token:"
    Write-Host "1. Go to https://github.com/settings/tokens"
    Write-Host "2. Generate new token (repo scope)"
    Write-Host "3. Copy token and set as env var:"
    Write-Host "   `$env:GITHUB_TOKEN = 'ghp_xxxx...'"
    exit 1
}

cd $WorkspaceDir

Write-Host "[1] Configuring git..."
git config user.email "clawallday12@gmail.com"
git config user.name "clawallday12"

Write-Host "[2] Adding GitHub remote..."
$RepoUrl = "https://${GitHubUser}:${GitHubToken}@github.com/${GitHubUser}/${RepoName}.git"
git remote remove origin 2>$null
git remote add origin $RepoUrl

Write-Host "[3] Pushing to GitHub..."
git branch -M main
git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Code pushed successfully!"
    Write-Host "[OK] Repository: https://github.com/${GitHubUser}/${RepoName}"
    Write-Host ""
    Write-Host "Next step: Deploy to Railway"
    Write-Host "1. Go to https://railway.app"
    Write-Host "2. New Project → Deploy from GitHub"
    Write-Host "3. Select: ${GitHubUser}/${RepoName}"
} else {
    Write-Host "[ERROR] Push failed"
    exit 1
}
