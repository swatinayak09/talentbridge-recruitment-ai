# Push TalentBridge capstone to GitHub
# Requires Git: https://git-scm.com/download/win

$ErrorActionPreference = "Stop"
$RepoUrl = "https://github.com/swatinayak09/talentbridge-recruitment-ai.git"
$Root = $PSScriptRoot

Set-Location $Root

function Find-Git {
    $cmd = Get-Command git -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $paths = @(
        "${env:ProgramFiles}\Git\bin\git.exe",
        "${env:ProgramFiles}\Git\cmd\git.exe",
        "${env:ProgramFiles(x86)}\Git\bin\git.exe"
    )
    foreach ($p in $paths) {
        if (Test-Path $p) { return $p }
    }
    return $null
}

$git = Find-Git
if (-not $git) {
    Write-Host "Git not found. Install from https://git-scm.com/download/win" -ForegroundColor Red
    Write-Host "Or follow manual steps in docs/GIT_SETUP.md"
    exit 1
}

Write-Host "Using: $git"

if (-not (Test-Path ".git")) {
    & $git init
}

& $git add .
$status = & $git status --porcelain
if ($status) {
    & $git commit -m "Add Pipeline Insights and Escalation/Compliance agents with dashboard"
} else {
    Write-Host "Nothing new to commit."
}

& $git branch -M main

$remotes = & $git remote 2>$null
if ($remotes -notcontains "origin") {
    & $git remote add origin $RepoUrl
} else {
    & $git remote set-url origin $RepoUrl
}

Write-Host "`nPulling remote main (merge existing README)..."
& $git pull origin main --allow-unrelated-histories --no-edit 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Pull had conflicts or failed — resolve manually, then run: git push -u origin main"
    exit $LASTEXITCODE
}

Write-Host "`nPushing to $RepoUrl ..."
& $git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nDone! View at: https://github.com/swatinayak09/talentbridge-recruitment-ai" -ForegroundColor Green
} else {
    Write-Host "`nPush failed. Sign in with GitHub CLI (gh auth login) or a Personal Access Token." -ForegroundColor Yellow
    Write-Host "See docs/GIT_SETUP.md"
}
