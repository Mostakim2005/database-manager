# Live Tri-Source AI Model Synchronizer Wrapper (OpenRouter + Models.dev + Artificial Analysis)
# Usage: powershell -ExecutionPolicy Bypass -File .\src\update_models.ps1
$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir
Push-Location $repoRoot
try {
    python src/scrapers/multi_site_ai.py --live --apply
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally {
    Pop-Location
}
