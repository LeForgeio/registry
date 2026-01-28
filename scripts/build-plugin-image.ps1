# =============================================================================
# Build LeForge Plugin Docker Image with Integration Assets (Windows)
# 
# This script generates platform integration assets and builds the Docker image
# with those assets bundled for air-gapped distribution.
#
# Usage:
#   .\scripts\build-plugin-image.ps1 -PluginName <plugin-name> [-Tag <tag>] [-Push]
#
# Examples:
#   .\scripts\build-plugin-image.ps1 -PluginName llm-service
#   .\scripts\build-plugin-image.ps1 -PluginName crypto-service -Tag v2.0.0
#   .\scripts\build-plugin-image.ps1 -PluginName llm-service -Tag latest -Push
# =============================================================================

param(
    [Parameter(Mandatory=$true)]
    [string]$PluginName,
    
    [string]$Tag = "latest",
    
    [switch]$Push
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir
$PluginDir = Join-Path $RootDir "plugins\$PluginName"

if (-not (Test-Path $PluginDir)) {
    Write-Host "Error: Plugin directory not found: $PluginDir" -ForegroundColor Red
    Write-Host ""
    Write-Host "Available plugins:"
    Get-ChildItem "$RootDir\plugins" -Directory | ForEach-Object { Write-Host "  $($_.Name)" }
    exit 1
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Building LeForge Plugin: $PluginName" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Generate integration assets
Write-Host "Step 1: Generating integration assets..." -ForegroundColor Yellow

$IntegrationsDir = Join-Path $PluginDir "integrations"
if (Test-Path $IntegrationsDir) {
    Remove-Item -Recurse -Force $IntegrationsDir
}
New-Item -ItemType Directory -Path $IntegrationsDir -Force | Out-Null

$Platforms = @("nintex-cloud", "nintex-k2", "power-automate")

foreach ($platform in $Platforms) {
    Write-Host "  Generating $platform..."
    try {
        python "$RootDir\scripts\generate-integrations.py" `
            --plugin $PluginName `
            --platform $platform `
            --output $IntegrationsDir 2>$null
    } catch {
        Write-Host "    (skipped - not supported)" -ForegroundColor Gray
    }
}

# Copy generated assets from main integrations folder
$MainIntegrationsDir = Join-Path $RootDir "integrations"
if (Test-Path $MainIntegrationsDir) {
    foreach ($platform in $Platforms) {
        $PlatformDir = Join-Path $MainIntegrationsDir $platform
        if (Test-Path $PlatformDir) {
            # Find plugin folder (handle different naming conventions)
            $PluginFolders = Get-ChildItem $PlatformDir -Directory | Where-Object { 
                $_.Name -like "*$($PluginName.Replace('-',''))*" -or 
                $_.Name -like "*$($PluginName)*" -or
                $_.Name -like "*$($PluginName.Replace('-service',''))*"
            }
            foreach ($folder in $PluginFolders) {
                $DestDir = Join-Path $IntegrationsDir $platform
                if (-not (Test-Path $DestDir)) {
                    New-Item -ItemType Directory -Path $DestDir -Force | Out-Null
                }
                Copy-Item -Path "$($folder.FullName)\*" -Destination $DestDir -Recurse -Force
            }
        }
    }
}

Write-Host "  ✓ Integration assets generated" -ForegroundColor Green
Write-Host ""

# Step 2: Build Docker image
Write-Host "Step 2: Building Docker image..." -ForegroundColor Yellow

$ImageName = "LeForge/${PluginName}:$Tag"

docker build `
    --target production `
    -t $ImageName `
    -f "$PluginDir\Dockerfile" `
    $PluginDir

Write-Host "  ✓ Image built: $ImageName" -ForegroundColor Green
Write-Host ""

# Step 3: Verify integrations
Write-Host "Step 3: Verifying integration assets..." -ForegroundColor Yellow
try {
    docker run --rm $ImageName ls -la /integrations/
} catch {
    Write-Host "  (verification skipped)" -ForegroundColor Gray
}
Write-Host ""

# Step 4: Optional push
if ($Push) {
    Write-Host "Step 4: Pushing to registry..." -ForegroundColor Yellow
    docker push $ImageName
    Write-Host "  ✓ Pushed: $ImageName" -ForegroundColor Green
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Build complete!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Image: $ImageName"
Write-Host ""
Write-Host "To extract integrations for air-gapped deployment:"
Write-Host "  docker run --rm -v ${pwd}/output:/out $ImageName cp -r /integrations /out/"
Write-Host ""
Write-Host "To save image for transfer:"
Write-Host "  docker save $ImageName -o ${PluginName}.tar"
