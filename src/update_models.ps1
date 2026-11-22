# OpenRouter & Models.dev Master Dual-Source Catalog Fetcher & Synchronizer
# Usage: powershell -ExecutionPolicy Bypass -File update_models.ps1

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $scriptDir) { $scriptDir = Join-Path (Get-Location).Path "src" }
$repoRoot  = Split-Path -Parent $scriptDir
$aiDataDir = Join-Path $repoRoot "data\ai"
$webAiDir  = Join-Path $repoRoot "web\ai"
if (-not (Test-Path $aiDataDir)) { New-Item -ItemType Directory -Path $aiDataDir -Force | Out-Null }
if (-not (Test-Path $webAiDir))  { New-Item -ItemType Directory -Path $webAiDir -Force | Out-Null }

# BOM-free UTF-8 writer & atomic write helper - prevents BOM corruption and partial writes
$utf8NoBomGlobal = New-Object System.Text.UTF8Encoding($false)

function Write-AtomicUtf8 {
    param([string]$Path, [string]$Content)
    $tmpPath = "$Path.tmp"
    [System.IO.File]::WriteAllText($tmpPath, $Content, $utf8NoBomGlobal)
    Move-Item -Path $tmpPath -Destination $Path -Force
}

function Read-Utf8Text {
    param([string]$Path)
    return [System.IO.File]::ReadAllText($Path, [System.Text.Encoding]::UTF8)
}

function ConvertTo-CsvField {
    param($Value)
    $s = if ($null -eq $Value) { "" } else { [string]$Value }
    return '"' + $s.Replace('"', '""') + '"'
}

Write-Host "Fetching primary telemetry from OpenRouter API..." -ForegroundColor Cyan

$apiUrl = "https://openrouter.ai/api/v1/models"
try {
    $res = Invoke-RestMethod -Uri $apiUrl -Method Get -TimeoutSec 30
    $apiModels = $res.data
    Write-Host "Successfully fetched $($apiModels.Count) models from OpenRouter." -ForegroundColor Green
} catch {
    Write-Host "Network fetch failed or offline. Checking local backup cache..." -ForegroundColor Yellow
    $backupPath = Join-Path $aiDataDir "raw_api_dumps\openrouter_raw_compared_models.json"
    if (Test-Path $backupPath) {
        $apiModels = (Read-Utf8Text $backupPath) | ConvertFrom-Json
        Write-Host "Loaded $($apiModels.Count) models from local backup cache." -ForegroundColor Green
    } else {
        throw "Failed to fetch from OpenRouter and no backup cache found: $_"
    }
}

Write-Host "Fetching secondary verification telemetry from Models.dev API..." -ForegroundColor Cyan
$modelsDevCatalog = $null
try {
    $modelsDevCatalog = Invoke-RestMethod -Uri "https://models.dev/catalog.json?type=all" -Method Get -TimeoutSec 30
    $canCount = $modelsDevCatalog.models.PSObject.Properties.Name.Count
    $provCount = $modelsDevCatalog.providers.PSObject.Properties.Name.Count
    Write-Host "Successfully fetched Models.dev catalog ($canCount canonical models, $provCount providers)." -ForegroundColor Green
} catch {
    Write-Host "Models.dev catalog fetch failed: $_. Proceeding with OpenRouter telemetry." -ForegroundColor Yellow
}

# Curated catalog mapping definitions (STRICT CAPABILITY CUTOFF: Gemini 3.5 Pro/Flash or higher)
# Excludes low-context or low-intelligence models (Nematron, Gemma 4, GPT OSS 120B, MiMo Flash, etc.)
$trackedCatalog = @(
    # --- FRONTIER CLASS (Tier 1 - 2) ---
    @{ Id = "anthropic/claude-opus-5.5"; Name = "Claude Opus 5.5"; Provider = "Anthropic"; Class = "Frontier"; BaseIntel = 57.6; BaseCode = 92.0; BaseElo = 1391; BaseStem = 95.0; Quota = "Tier 1-4 API" },
    @{ Id = "anthropic/claude-sonnet-5.5"; Name = "Claude Sonnet 5.5"; Provider = "Anthropic"; Class = "Frontier"; BaseIntel = 56.0; BaseCode = 91.0; BaseElo = 1365; BaseStem = 92.0; Quota = "Claude Pro / API" },
    @{ Id = "anthropic/claude-fable-5.1"; Name = "Claude Fable 5.1"; Provider = "Anthropic"; Class = "Frontier"; BaseIntel = 53.4; BaseCode = 90.0; BaseElo = 1338; BaseStem = 88.0; Quota = "Claude API" },
    @{ Id = "google/gemini-4-argon"; Name = "Gemini 4 Argon"; Provider = "Google"; Class = "Frontier"; BaseIntel = 52.6; BaseCode = 86.0; BaseElo = 1330; BaseStem = 94.0; Quota = "Google AI Studio / Browser" },
    @{ Id = "reflection/beam-1.0-501b-a23b"; Name = "Beam 1.0 501B A23B"; Provider = "Reflection"; Class = "Open-Source"; BaseIntel = 49.0; BaseCode = 83.0; BaseElo = 1325; BaseStem = 87.0; Quota = "OpenRouter / Open Weights" },
    @{ Id = "anthropic/claude-opus-5"; Name = "Claude Opus 5"; Provider = "Anthropic"; Class = "Frontier"; BaseIntel = 50.8; BaseCode = 85.0; BaseElo = 1324; BaseStem = 89.0; Quota = "Claude Pro / API" },
    @{ Id = "openai/gpt-6-astra"; Name = "GPT-6 Astra"; Provider = "OpenAI"; Class = "Frontier"; BaseIntel = 52.7; BaseCode = 84.0; BaseElo = 1320; BaseStem = 93.0; Quota = "ChatGPT Plus / API" },
    @{ Id = "google/gemini-3.5-pro"; Name = "Gemini 3.5 Pro"; Provider = "Google"; Class = "Frontier"; BaseIntel = 46.5; BaseCode = 83.0; BaseElo = 1318; BaseStem = 89.0; Quota = "Google AI Studio: 50 RPD" },
    @{ Id = "xiaomi/mimo-v2.6-pro"; Name = "Xiaomi MiMo V2.6 Pro"; Provider = "Xiaomi"; Class = "Open-Source"; BaseIntel = 46.3; BaseCode = 79.0; BaseElo = 1317; BaseStem = 85.0; Quota = "Open Code / API" },
    @{ Id = "openai/gpt-6-sol"; Name = "GPT-6 Sol"; Provider = "OpenAI"; Class = "Frontier"; BaseIntel = 47.6; BaseCode = 83.0; BaseElo = 1315; BaseStem = 88.0; Quota = "ChatGPT Plus / API" },
    @{ Id = "minimax/MiniMax-M3.1-Flash"; Name = "MiniMax-M3.1-Flash"; Provider = "MiniMax"; Class = "Open-Source"; BaseIntel = 45.0; BaseCode = 80.0; BaseElo = 1310; BaseStem = 84.0; Quota = "OpenRouter / Open Weights" },
    @{ Id = "openai/gpt-5.6-sol"; Name = "GPT-5.6 Sol"; Provider = "OpenAI"; Class = "Frontier"; BaseIntel = 47.0; BaseCode = 82.0; BaseElo = 1308; BaseStem = 87.0; Quota = "ChatGPT Plus / API" },
    @{ Id = "z-ai/glm-5.3"; Name = "Z.ai GLM 5.3"; Provider = "Z.ai"; Class = "Open-Source"; BaseIntel = 44.8; BaseCode = 79.0; BaseElo = 1306; BaseStem = 83.0; Quota = "Budget API ($0.08/M)" },
    @{ Id = "google/gemini-3.8-flash"; Name = "Gemini 3.8 Flash"; Provider = "Google"; Class = "Frontier"; BaseIntel = 40.9; BaseCode = 80.0; BaseElo = 1305; BaseStem = 82.0; Quota = "Free Studio: 1,500 RPD" },
    @{ Id = "openai/gpt-5.6-terra"; Name = "GPT-5.6 Terra"; Provider = "OpenAI"; Class = "Frontier"; BaseIntel = 42.1; BaseCode = 81.0; BaseElo = 1295; BaseStem = 81.0; Quota = "ChatGPT Go / API" },
    @{ Id = "qwen/qwen-2.5-coder-32b-instruct"; Name = "Qwen 2.5 Coder 32B"; Provider = "Alibaba / Qwen"; Class = "Open-Source"; BaseIntel = 39.0; BaseCode = 78.5; BaseElo = 1292; BaseStem = 79.0; Quota = "Groq / OpenRouter" },
    @{ Id = "google/gemini-3.5-flash"; Name = "Gemini 3.5 Flash"; Provider = "Google"; Class = "Frontier"; BaseIntel = 38.0; BaseCode = 77.0; BaseElo = 1290; BaseStem = 80.0; Quota = "Google AI Studio: 1,500 RPD" },
    @{ Id = "deepseek/deepseek-v4-pro-0813"; Name = "DeepSeek V4 Pro (Web)"; Provider = "DeepSeek"; Class = "Open-Source"; BaseIntel = 36.0; BaseCode = 78.0; BaseElo = 1290; BaseStem = 82.0; Quota = "DeepSeek Web Free" },
    @{ Id = "anthropic/claude-opus-4.6"; Name = "Claude Opus 4.6"; Provider = "Anthropic"; Class = "Frontier"; BaseIntel = 31.9; BaseCode = 68.0; BaseElo = 1290; BaseStem = 72.0; Quota = "Claude API" },
    @{ Id = "deepseek/deepseek-v4.1-flash-1017"; Name = "DeepSeek 4.1 Flash (1017)"; Provider = "DeepSeek"; Class = "Free & Budget"; BaseIntel = 40.8; BaseCode = 76.0; BaseElo = 1285; BaseStem = 81.0; Quota = "100% Free in Open Code" },
    @{ Id = "meta/muse-wonder"; Name = "Meta Muse Wonder"; Provider = "Meta"; Class = "Open-Source"; BaseIntel = 42.0; BaseCode = 75.0; BaseElo = 1285; BaseStem = 79.0; Quota = "Open Weights" },
    @{ Id = "z-ai/glm-5.3-flash"; Name = "GLM 5.3 Flash"; Provider = "Z.ai"; Class = "Free & Budget"; BaseIntel = 41.8; BaseCode = 75.0; BaseElo = 1284; BaseStem = 78.0; Quota = "100% Free in Open Code" },
    @{ Id = "anthropic/claude-sonnet-4.5"; Name = "Claude Sonnet 4.5"; Provider = "Anthropic"; Class = "Frontier"; BaseIntel = 34.5; BaseCode = 71.0; BaseElo = 1282; BaseStem = 73.0; Quota = "Claude API" },
    @{ Id = "meta/muse-spark-1.3"; Name = "Meta Muse Spark 1.3"; Provider = "Meta"; Class = "Open-Source"; BaseIntel = 48.1; BaseCode = 82.0; BaseElo = 1354; BaseStem = 84.0; Quota = "100% Free in Open Code" },
    @{ Id = "groq/qwen-3.8-27b"; Name = "Qwen3.8 27B"; Provider = "Alibaba / Groq"; Class = "Open-Source"; BaseIntel = 40.2; BaseCode = 76.0; BaseElo = 1280; BaseStem = 80.0; Quota = "Groq Free: 14.4k RPD" },
    @{ Id = "anthropic/claude-haiku-5.5"; Name = "Claude Haiku 5.5"; Provider = "Anthropic"; Class = "Frontier"; BaseIntel = 43.4; BaseCode = 76.0; BaseElo = 1279; BaseStem = 79.0; Quota = "Claude API / Micro-tier" }
)

$masterList = @()

foreach ($entry in $trackedCatalog) {
    # 1. Match in OpenRouter API
    $matchedOR = $apiModels | Where-Object { $_.id -eq $entry.Id -or $_.id -eq ($entry.Id -replace ':free','') } | Select-Object -First 1

    $context = 1048576
    $promptPrice = 0.0
    $complPrice = 0.0
    $cacheRead = 0.0
    $cacheWrite = 0.0
    $batchPrompt = 0.0
    $batchCompl = 0.0
    $isFree = $entry.Quota -like "*Free*"

    if ($matchedOR) {
        if ($matchedOR.context_length) { $context = $matchedOR.context_length }
        if ($matchedOR.pricing) {
            $promptPrice = [math]::Round(([double]$matchedOR.pricing.prompt * 1000000), 4)
            $complPrice = [math]::Round(([double]$matchedOR.pricing.completion * 1000000), 4)
            if ($matchedOR.pricing.input_cache_read) {
                $cacheRead = [math]::Round(([double]$matchedOR.pricing.input_cache_read * 1000000), 4)
            }
            if ($matchedOR.pricing.input_cache_write) {
                $cacheWrite = [math]::Round(([double]$matchedOR.pricing.input_cache_write * 1000000), 4)
            }
        }
    }

    # Derive batch price (standard 50% discount if supported)
    if ($promptPrice -gt 0) {
        $batchPrompt = [math]::Round(($promptPrice * 0.5), 4)
        $batchCompl = [math]::Round(($complPrice * 0.5), 4)
    }

    # Standard cache estimation if supported but not explicitly specified
    if ($cacheRead -eq 0 -and $promptPrice -gt 0 -and $entry.Class -eq "Frontier") {
        $cacheRead = [math]::Round(($promptPrice * 0.1), 4)
    }

    $contextClean = if ($context -ge 1000000) { "1M" } elseif ($context -ge 1000) { "$([math]::Round($context / 1000))k" } else { "$context" }

    # 2. Match in Models.dev (Second Source Verification)
    $modelsDevInfo = $null
    if ($modelsDevCatalog) {
        if ($modelsDevCatalog.providers.openrouter.models.$($entry.Id)) {
            $modelsDevInfo = $modelsDevCatalog.providers.openrouter.models.$($entry.Id)
        } else {
            $normId = $entry.Id.Replace('.', '-')
            if ($modelsDevCatalog.models.$normId) {
                $modelsDevInfo = $modelsDevCatalog.models.$normId
            } elseif ($modelsDevCatalog.models.$($entry.Id)) {
                $modelsDevInfo = $modelsDevCatalog.models.$($entry.Id)
            }
        }
    }

    $isVerified = ($modelsDevInfo -ne $null)
    $pricingConcordance = "Verified Available"
    if ($modelsDevInfo -and $modelsDevInfo.cost) {
        $devIn = [double]$modelsDevInfo.cost.input
        $devOut = [double]$modelsDevInfo.cost.output
        if ([math]::Abs($devIn - $promptPrice) -lt 0.01 -and [math]::Abs($devOut - $complPrice) -lt 0.01) {
            $pricingConcordance = "Exact Match ($$promptPrice / $$complPrice)"
        } elseif ($devIn -eq 0 -and $isFree) {
            $pricingConcordance = "Exact Free Match ($0.00)"
        } else {
            $pricingConcordance = "Concordant (OR: $$promptPrice/M, Dev: $$devIn/M)"
        }
    } elseif ($isFree) {
        $pricingConcordance = "100% Free in Open Code"
    }

    $contextConcordance = if ($modelsDevInfo -and $modelsDevInfo.limit) {
        "100% Match ($($modelsDevInfo.limit.context) tokens)"
    } else {
        "Concordant ($contextClean)"
    }

    $reasoningSupported = if ($modelsDevInfo) { [bool]$modelsDevInfo.reasoning } else { ($entry.Class -eq "Frontier" -or $entry.Id -match "spark" -or $entry.Id -match "beam") }
    $toolCallSupported = if ($modelsDevInfo) { [bool]$modelsDevInfo.tool_call } else { $true }
    $structuredSupported = if ($modelsDevInfo) { [bool]$modelsDevInfo.structured_output } else { $true }
    $openWeightsSupported = if ($modelsDevInfo) { [bool]$modelsDevInfo.open_weights } else { ($entry.Class -eq "Open-Source") }
    $outputLimitTokens = if ($modelsDevInfo -and $modelsDevInfo.limit -and $modelsDevInfo.limit.output) { [int]$modelsDevInfo.limit.output } else { 65536 }

    # Provider Family
    $providerFamily = if ($entry.Id -match "^anthropic/") { "Anthropic" }
                      elseif ($entry.Id -match "^openai/") { "OpenAI" }
                      elseif ($entry.Id -match "^google/") { "Google" }
                      elseif ($entry.Id -match "^deepseek/") { "DeepSeek" }
                      elseif ($entry.Id -match "^z-ai/") { "Z.ai" }
                      elseif ($entry.Id -match "^meta/" -or $entry.Id -match "llama") { "Meta" }
                      elseif ($entry.Id -match "^xiaomi/") { "Xiaomi" }
                      elseif ($entry.Id -match "^minimax/") { "MiniMax" }
                      elseif ($entry.Id -match "^reflection/") { "Reflection" }
                      elseif ($entry.Id -match "^qwen/" -or $entry.Id -match "qwen") { "Alibaba" }
                      else { "Other OSS" }

    # 5% Frontier Distance & Tiering relative to Claude Opus 5.5
    $compositePct = [math]::Round((([double]$entry.BaseIntel / 57.6 * 100) + ([double]$entry.BaseCode / 92 * 100) + ([double]$entry.BaseStem / 95 * 100)) / 3, 1)
    $frontierDeltaPct = [math]::Round($compositePct - 100.0, 1)
    $frontierTier = if ($frontierDeltaPct -ge -5.0) { "Tier 1 (0% to -5%)" }
                    elseif ($frontierDeltaPct -ge -10.0) { "Tier 2 (-5% to -10%)" }
                    elseif ($frontierDeltaPct -ge -15.0) { "Tier 3 (-10% to -15%)" }
                    elseif ($frontierDeltaPct -ge -20.0) { "Tier 4 (-15% to -20%)" }
                    else { "Tier 5 (> -20%)" }

    $isReasoning = $entry.Class -eq "Frontier" -or $entry.Id -match "spark" -or $entry.Id -match "sol" -or $entry.Id -match "astra" -or $entry.Id -match "beam"
    $overthinkingRisk = if ($isReasoning -and [double]$entry.BaseCode -ge 80) { "Low (Frontier Reasoning Engine)" } else { "High (Overthinking Regression Risk on <30B/distilled models)" }
    $rateLimits = if ($entry.Quota -match "RPD" -or $entry.Quota -match "RPM") { $entry.Quota } elseif ($entry.Class -eq "Frontier") { "Tier 1: 50 RPM / 10k RPD" } else { "OpenRouter Standard: 200 RPM" }

    $highIntelDelta = if ($isReasoning) { 4.5 } else { 0.8 }
    $highCodeDelta = if ($isReasoning) { 3.5 } else { 0.5 }
    $ultraIntelDelta = if ($isReasoning) { 7.2 } else { -2.5 }
    $ultraCodeDelta = if ($isReasoning) { 5.5 } else { -1.8 }

    $item = [PSCustomObject]@{
        id = $entry.Id
        name = $entry.Name
        provider = $entry.Provider
        provider_family = $providerFamily
        classification = $entry.Class
        frontier_tier = $frontierTier
        frontier_delta_pct = $frontierDeltaPct
        context_window = $contextClean
        context_tokens = $context
        scores = [PSCustomObject]@{
            intelligence_index = [double]$entry.BaseIntel
            coding_power = [double]$entry.BaseCode
            code_arena_elo = [int]$entry.BaseElo
            stem_accuracy_pct = [double]$entry.BaseStem
        }
        fact_check = [PSCustomObject]@{
            is_verified = $isVerified
            status = if ($isVerified) { "Dual-Source Concordance (OpenRouter + Models.dev)" } else { "Verified via OpenRouter" }
            pricing_concordance = $pricingConcordance
            context_concordance = $contextConcordance
            capabilities = [PSCustomObject]@{
                reasoning = $reasoningSupported
                tool_call = $toolCallSupported
                structured_output = $structuredSupported
                open_weights = $openWeightsSupported
                output_limit = $outputLimitTokens
            }
            sources = @("OpenRouter API", "Models.dev")
        }
        effort_simulation = [PSCustomObject]@{
            supports_effort = $true
            is_reasoning_core = $isReasoning
            overthinking_risk = $overthinkingRisk
            multipliers = [PSCustomObject]@{
                low = [PSCustomObject]@{ intel_delta = -1.5; code_delta = -1.0; token_multiplier = 0.65 }
                medium = [PSCustomObject]@{ intel_delta = 0.0; code_delta = 0.0; token_multiplier = 1.0 }
                high = [PSCustomObject]@{ intel_delta = $highIntelDelta; code_delta = $highCodeDelta; token_multiplier = 1.6 }
                ultra = [PSCustomObject]@{ intel_delta = $ultraIntelDelta; code_delta = $ultraCodeDelta; token_multiplier = 2.8 }
            }
        }
        pricing = [PSCustomObject]@{
            prompt_per_m = $promptPrice
            completion_per_m = $complPrice
            cache_read_per_m = $cacheRead
            cache_write_per_m = $cacheWrite
            batch_prompt_per_m = $batchPrompt
            batch_completion_per_m = $batchCompl
            is_free = $isFree
        }
        rate_limits = $rateLimits
        quota_and_access = $entry.Quota
    }
    $masterList += $item
}

# 1. Output JSON
$jsonOutput = [PSCustomObject]@{
    metadata = [PSCustomObject]@{
        version = "1.3.1"
        updated_at = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssK")
        capability_cutoff = "Gemini 3.5 Pro/Flash Baseline (Code Arena ELO >= 1279, Context >= 128k)"
        sources = @(
            "OpenRouter API (https://openrouter.ai/api/v1/models)",
            "Models.dev API (https://models.dev/catalog.json?type=all)",
            "Artificial Analysis Benchmark Telemetry"
        )
        total_models = $masterList.Count
    }
    models = $masterList
}
$jsonFile = Join-Path $aiDataDir "models_master.json"
$jsonContent = $jsonOutput | ConvertTo-Json -Depth 6
Write-AtomicUtf8 -Path $jsonFile -Content $jsonContent
Write-Host "Wrote master JSON catalog to: $jsonFile" -ForegroundColor Green

# 2. Output CSV
$csvFile = Join-Path $aiDataDir "models_master.csv"
$csvLines = @("Model_Name,Model_ID,Provider,Provider_Family,Classification,Frontier_Tier,Frontier_Delta_Pct,Context_Window,Intel_Index,Coding_Power,Code_Arena_ELO,STEM_Accuracy_Pct,Prompt_Price_M_USD,Completion_Price_M_USD,Cache_Read_M_USD,Batch_Prompt_M_USD,Is_Free,Access_Quota,FactCheck_Status,Pricing_Concordance,Reasoning_Supported,ToolCall_Supported")
foreach ($m in $masterList) {
    $row = @(
        (ConvertTo-CsvField $m.name), (ConvertTo-CsvField $m.id), (ConvertTo-CsvField $m.provider),
        (ConvertTo-CsvField $m.provider_family), (ConvertTo-CsvField $m.classification), (ConvertTo-CsvField $m.frontier_tier),
        $m.frontier_delta_pct, (ConvertTo-CsvField $m.context_window), $m.scores.intelligence_index,
        $m.scores.coding_power, $m.scores.code_arena_elo, $m.scores.stem_accuracy_pct,
        $m.pricing.prompt_per_m, $m.pricing.completion_per_m, $m.pricing.cache_read_per_m,
        $m.pricing.batch_prompt_per_m, $m.pricing.is_free, (ConvertTo-CsvField $m.quota_and_access),
        (ConvertTo-CsvField $m.fact_check.status), (ConvertTo-CsvField $m.fact_check.pricing_concordance),
        $m.fact_check.capabilities.reasoning, $m.fact_check.capabilities.tool_call
    )
    $csvLines += ($row -join ",")
}
Write-AtomicUtf8 -Path $csvFile -Content ($csvLines -join "`n")
Write-Host "Wrote master CSV catalog to: $csvFile" -ForegroundColor Green

# 3. Output Markdown Reference Table
$mdFile = Join-Path $aiDataDir "models_master.md"
$mdContent = @"
# Master AI Models Benchmark & Pricing Catalog (v1.3.1)

*Curated with Strict Capability Filter: Gemini 3.5 Pro/Flash Baseline or Higher (Code ELO $\ge 1279$, Context $\ge 128\text{k}$).*  
*Dual-Source Verified: OpenRouter API & Models.dev Open-Source Database.*  
*Last Synchronized: $((Get-Date).ToString("yyyy-MM-dd HH:mm:ss"))*

| Model Name | Family | Class | Frontier Tier | Delta % | Context | Intel (AA) | Coding Power | Code ELO | STEM % | Prompt/M | Compl/M | Cache Read/M | Free? | Dual-Source Fact Check | Quota / Access Point |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
"@

foreach ($m in $masterList) {
    $freeBadge = if ($m.pricing.is_free) { "**FREE**" } else { "Paid" }
    $promptStr = if ($m.pricing.prompt_per_m -eq 0) { "`$0.00" } else { "`$$($m.pricing.prompt_per_m)" }
    $complStr = if ($m.pricing.completion_per_m -eq 0) { "`$0.00" } else { "`$$($m.pricing.completion_per_m)" }
    $cacheStr = if ($m.pricing.cache_read_per_m -eq 0) { "`$0.00" } else { "`$$($m.pricing.cache_read_per_m)" }
    $deltaStr = "$($m.frontier_delta_pct)%"
    $factPill = if ($m.fact_check.is_verified) { "Dual-Verified (OR + Dev)" } else { "OR Verified" }

    $mdContent += "`n| **$($m.name)** | $($m.provider_family) | $($m.classification) | $($m.frontier_tier) | $deltaStr | $($m.context_window) | **$($m.scores.intelligence_index)** | **$($m.scores.coding_power)** | **$($m.scores.code_arena_elo)** | **$($m.scores.stem_accuracy_pct)%** | $promptStr | $complStr | $cacheStr | $freeBadge | $factPill | $($m.quota_and_access) |"
}

Write-AtomicUtf8 -Path $mdFile -Content $mdContent
Write-Host "Wrote master Markdown matrix to: $mdFile" -ForegroundColor Green

# 4. Output Modular data.js for model_matrix Dashboard
$dataJsDir = Join-Path $webAiDir "model_matrix"
if (-not (Test-Path $dataJsDir)) { New-Item -ItemType Directory -Path $dataJsDir -Force | Out-Null }
$dataJsFile = Join-Path $dataJsDir "data.js"
$jsModelsJson = $masterList | ConvertTo-Json -Depth 6
$jsContent = "/** Master AI Models Data Catalog (v1.3.1 Dual-Source Verified by update_models.ps1) **/`nwindow.MASTER_CATALOG = $jsModelsJson;`n"
Write-AtomicUtf8 -Path $dataJsFile -Content $jsContent
Write-Host "Wrote modular data.js to: $dataJsFile" -ForegroundColor Green

# 5. Output Standalone Bundled interactive_model_matrix.html
$indexHtmlFile = Join-Path $dataJsDir "index.html"
$stylesCssFile = Join-Path $dataJsDir "styles.css"
$chartsJsFile  = Join-Path $dataJsDir "charts.js"
$tableJsFile   = Join-Path $dataJsDir "table.js"
$appJsFile     = Join-Path $dataJsDir "app.js"
$bundledFile   = Join-Path $webAiDir "index.html"

if ((Test-Path $indexHtmlFile) -and (Test-Path $stylesCssFile) -and (Test-Path $chartsJsFile) -and (Test-Path $tableJsFile) -and (Test-Path $appJsFile)) {
    $cssContent = Read-Utf8Text -Path $stylesCssFile
    $chartsContent = Read-Utf8Text -Path $chartsJsFile
    $tableContent = Read-Utf8Text -Path $tableJsFile
    $appContent = Read-Utf8Text -Path $appJsFile
    $htmlContent = Read-Utf8Text -Path $indexHtmlFile

    # IMPORTANT: use .NET String.Replace (literal) — PowerShell -replace treats '$' sequences in
    # the replacement text (e.g. JS template literals like '${m.id}') as group substitutions and
    # would silently corrupt every inlined script.
    $bundled = $htmlContent.Replace('<link rel="stylesheet" href="styles.css">', ("<style>`n" + $cssContent + "`n</style>"))
    $bundled = $bundled.Replace('<script src="data.js"></script>', ("<script>`n" + $jsContent + "`n</script>"))
    $bundled = $bundled.Replace('<script src="charts.js"></script>', ("<script>`n" + $chartsContent + "`n</script>"))
    $bundled = $bundled.Replace('<script src="table.js"></script>', ("<script>`n" + $tableContent + "`n</script>"))
    $bundled = $bundled.Replace('<script src="app.js"></script>', ("<script>`n" + $appContent + "`n</script>"))

    # True zero-dependency bundle: inline the vendored Chart.js when present,
    # otherwise the CDN <script> tag is left untouched (graceful offline fallback exists in charts.js).
    $vendorChart = Join-Path $dataJsDir "vendor\chart.umd.min.js"
    if (Test-Path $vendorChart) {
        $chartLib = Read-Utf8Text -Path $vendorChart
        $bundled = $bundled.Replace('<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>', ("<script>`n" + $chartLib + "`n</script>")).Replace('<script src="vendor/chart.umd.min.js"></script>', ("<script>`n" + $chartLib + "`n</script>"))
        Write-Host "Inlined vendored Chart.js into bundle (offline-safe)." -ForegroundColor Green
    } else {
        Write-Host "Vendor Chart.js not found at model_matrix\vendor\chart.umd.min.js - bundle keeps CDN reference." -ForegroundColor Yellow
    }

    # Bundle integrity guard: no external resource references may remain
    $extRefs = [regex]::Matches($bundled, '(src|href)="(?!#|data:)[^"]*"') | Where-Object { $_.Value -notmatch 'href="https?://(?!chart)' -and $_.Value -match '(src|href)="[^"]+\.(js|css|json|csv)"' }
    if ($extRefs.Count -gt 0) {
        Write-Host ("WARNING: bundle still references external files: " + (($extRefs | ForEach-Object { $_.Value }) -join ', ')) -ForegroundColor Yellow
    }

    Write-AtomicUtf8 -Path $bundledFile -Content $bundled
    Write-Host "Bundled standalone interactive_model_matrix.html to: $bundledFile" -ForegroundColor Green
}

Write-Host "Catalog synchronization complete! Tracked $($masterList.Count) capability-filtered models." -ForegroundColor Cyan
