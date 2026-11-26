<#
.SYNOPSIS
  Local CI verification runner for Database Manager.

.DESCRIPTION
  Runs modular verification stages locally on Windows without requiring heavy tooling.
  On any failure, writes a git-patch-compatible Title Case Markdown report directly into
  %USERPROFILE%\Downloads\<Repo Title Case> - Local CI Failure Report.md.
#>
[CmdletBinding()]
param(
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
$env:GIT_TERMINAL_PROMPT = '0'
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)

$repoRoot = (Get-Location).Path
$folderName = Split-Path -Leaf $repoRoot

function ConvertTo-TitleCaseName {
    param([string]$RawName)
    $parts = ($RawName -split '[-_\s]+') | Where-Object { $_ -ne '' }
    $titled = foreach ($p in $parts) {
        if ($p.Length -gt 1) {
            $p.Substring(0, 1).ToUpperInvariant() + $p.Substring(1)
        } else {
            $p.ToUpperInvariant()
        }
    }
    return ($titled -join ' ')
}

function Invoke-GitCapture {
    param([string[]]$GitArgs)
    $prevEAP = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $out = & git @GitArgs 2>&1
        if ($LASTEXITCODE -ne 0) {
            return ""
        }
        return (($out -join "`n").Trim())
    } catch {
        return ""
    } finally {
        $ErrorActionPreference = $prevEAP
    }
}

$repoTitle = ConvertTo-TitleCaseName $folderName

# Modular verification stages for Database Manager
$stages = @(
    [ordered]@{ Name = '01 Python Syntax Check';       Command = 'python -m py_compile src/server.py src/agent_proxy.py src/book_sync.py src/db_export.py src/db_hub.py src/db_verify.py src/scrapers/base.py src/scrapers/adapters.py src/scrapers/test_stack.py src/scrapers/bd_hardware.py src/scrapers/benchmark_ingest.py src/scrapers/multi_site_components.py src/scrapers/multi_site_games.py src/scrapers/multi_site_ai.py src/compatibility_engine.py src/catalog_classifier.py src/media/__init__.py src/media/fetch_helper.py src/media/crawler.py src/media/indexer.py src/media/matcher.py src/media/adaptation_refresh.py src/media/link_health.py src/media/poster_cache.py src/media/franchise_builder.py src/media/cli.py src/github/__init__.py src/github/local_sync.py src/github/scanner.py src/github/exporter.py src/github/cli.py' }
    [ordered]@{ Name = '02 JSON Schema Validation';    Command = 'python -c "import json; json.load(open(''data/registry.json'', encoding=''utf-8'')); json.load(open(''data/pc/pc.json'', encoding=''utf-8'')); json.load(open(''data/games/games.json'', encoding=''utf-8'')); json.load(open(''data/ai/models_master.json'', encoding=''utf-8'')); json.load(open(''data/media/media_catalog.json'', encoding=''utf-8'')); json.load(open(''data/book/books.json'', encoding=''utf-8'')); json.load(open(''data/phone/phones.json'', encoding=''utf-8'')); json.load(open(''data/github/repos_public.json'', encoding=''utf-8'')); json.load(open(''data/ai/taxonomy.json'', encoding=''utf-8'')); json.load(open(''data/games/taxonomy.json'', encoding=''utf-8''))"' }
    [ordered]@{ Name = '03 SQLite Compilation';        Command = 'python src/db_export.py' }
    [ordered]@{ Name = '04 SQLite Verification';       Command = 'python src/db_export.py --verify' }
    [ordered]@{ Name = '05 CLI Search Smoke Test';     Command = 'python src/server.py --cli && python src/compatibility_engine.py --demo && python src/compatibility_engine.py --demo --json && python src/catalog_classifier.py --games && python src/catalog_classifier.py --ai --chinese-oss && python src/catalog_classifier.py --media && python src/catalog_classifier.py --github && python src/media/cli.py --verify --json && python src/media/cli.py --doctor --json && python src/media/cli.py --check-links && python src/github/cli.py --verify --json && python src/github/cli.py --doctor --json && python src/scrapers/benchmark_ingest.py --verify && python src/db_verify.py --domain learning' }
    [ordered]@{ Name = '06 Documentation Parity Check';Command = 'python -c "import pathlib, re; docs=[p.read_text(encoding=''utf-8'') for p in pathlib.Path(''docs'').glob(''*.md'')]; assert all(re.search(r''^### \['', d, re.M) for d in docs)"' }
    [ordered]@{ Name = '06b Multi-Domain Schema Verify';Command = 'python src/db_verify.py' }
    [ordered]@{ Name = '07 Unit & Regression Tests';   Command = 'python -m unittest discover -s tests -v' }
)

$results = New-Object System.Collections.Generic.List[object]
$failedStage = $null

foreach ($stage in $stages) {
    $stageName = $stage.Name
    $cmd = $stage.Command
    if (-not $cmd) {
        Write-Host "[SKIP] $stageName (no command configured)" -ForegroundColor DarkGray
        $results.Add([pscustomobject]@{ Stage = $stageName; Status = 'SKIPPED'; Command = '(none)'; Output = '' })
        continue
    }

    Write-Host "[RUN]  $stageName -> $cmd" -ForegroundColor Cyan
    $prevEAP = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $outputLines = & cmd.exe /c $cmd 2>&1
        $exitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $prevEAP
    }

    $outputText = ($outputLines -join "`n").Trim()

    if ($exitCode -ne 0) {
        Write-Host "[FAIL] $stageName (exit $exitCode)" -ForegroundColor Red
        $failedStage = [pscustomobject]@{
            Stage    = $stageName
            Status   = "FAILED (exit $exitCode)"
            Command  = $cmd
            Output   = $outputText
        }
        $results.Add($failedStage)
        break
    }

    Write-Host "[PASS] $stageName" -ForegroundColor Green
    $results.Add([pscustomobject]@{ Stage = $stageName; Status = 'PASSED'; Command = $cmd; Output = $outputText })
}

if ($failedStage) {
    $branch = Invoke-GitCapture @('rev-parse', '--abbrev-ref', 'HEAD')
    $sha = Invoke-GitCapture @('rev-parse', 'HEAD')
    $shortSha = if ($sha.Length -ge 8) { $sha.Substring(0, 8) } else { $sha }
    $diffStat = Invoke-GitCapture @('diff', '--stat', '--no-color')
    $diffPatch = Invoke-GitCapture @('diff', '--no-color')
    if ($diffPatch.Length -gt 12000) {
        $diffPatch = $diffPatch.Substring(0, 12000) + "`n... [diff truncated for size; inspect full diff in repo] ..."
    }

    $timestamp = (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd HH:mm:ss UTC')
    $downloadsDir = Join-Path $env:USERPROFILE 'Downloads'
    $reportFileName = "$repoTitle - Local CI Failure Report.md"
    $reportPath = Join-Path $downloadsDir $reportFileName

    $md = New-Object System.Collections.Generic.List[string]
    $md.Add("# $repoTitle - Local CI Failure Report")
    $md.Add('')
    $md.Add('## Metadata')
    $md.Add('| Field | Value |')
    $md.Add('| :--- | :--- |')
    $md.Add("| **Repository** | ``$repoRoot`` (``$repoTitle``) |")
    $md.Add("| **Branch** | ``$branch`` |")
    $md.Add("| **Head Commit** | ``$shortSha`` (``$sha``) |")
    $md.Add("| **Failed Stage** | ``$($failedStage.Stage)`` |")
    $md.Add("| **Generated** | $timestamp |")
    $md.Add('')
    $md.Add('## Stage Ledger')
    $md.Add('| Stage | Status | Command |')
    $md.Add('| :--- | :--- | :--- |')
    foreach ($r in $results) {
        $md.Add("| $($r.Stage) | $($r.Status) | ``$($r.Command)`` |")
    }
    $md.Add('')
    $md.Add('## Failing Stage Output')
    $md.Add('```text')
    $md.Add($(if ($failedStage.Output) { $failedStage.Output } else { '(no output captured)' }))
    $md.Add('```')
    $md.Add('')
    $md.Add('## Working Tree Diff Summary (`git diff --stat`)')
    $md.Add('```text')
    $md.Add($(if ($diffStat) { $diffStat } else { '(working tree clean; inspect HEAD commit)' }))
    $md.Add('```')
    $md.Add('')
    $md.Add('## Full Git Diff (`git diff`)')
    $md.Add('```diff')
    $md.Add($(if ($diffPatch) { $diffPatch } else { '# Working tree clean; no unstaged changes' }))
    $md.Add('```')
    $md.Add('')
    $md.Add('## Actionable Next Steps')
    $md.Add("1. Inspect the failing command output under ``$($failedStage.Stage)`` above.")
    $md.Add("2. Re-run ``cmd.exe /c '$($failedStage.Command)'`` directly to debug.")
    $md.Add("3. Update code, re-run ``.\local-ci.ps1``, and confirm all stages pass.")

    [System.IO.File]::WriteAllText($reportPath, ($md -join "`n"), $utf8NoBom)
    Write-Host "`n[REPORT] Saved patch-ready local CI failure report to:" -ForegroundColor Yellow
    Write-Host "         $reportPath`n" -ForegroundColor Yellow
    exit 1
}

Write-Host "`nAll local CI stages passed for $repoTitle." -ForegroundColor Green
exit 0
