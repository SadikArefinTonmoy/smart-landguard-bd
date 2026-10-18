# Apply Phase 7 source-only changes from this newly extracted ZIP to an existing folder.
# PostgreSQL volume, credentials, stored documents and existing sessions are NOT changed.
param([Parameter(Mandatory=$true)][string]$ExistingProject)
$ErrorActionPreference = 'Stop'
$source = Split-Path -Parent $MyInvocation.MyCommand.Path
$target = (Resolve-Path -LiteralPath $ExistingProject -ErrorAction Stop).Path
if ([IO.Path]::GetFullPath($source).TrimEnd('\') -eq [IO.Path]::GetFullPath($target).TrimEnd('\')) {
    throw 'Extract this Phase 7 ZIP to a SEPARATE new folder. Do not apply the source to itself.'
}
if (!(Test-Path (Join-Path $target 'frontend\src\App.tsx')) -or !(Test-Path (Join-Path $target 'backend\app\main.py'))) {
    throw 'The destination does not look like an existing Smart LandGuard BD 2.0 project.'
}
$backup = Join-Path (Split-Path -Parent $target) ('LandGuard_Phase7_Code_Backup_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
New-Item -ItemType Directory -Path (Join-Path $backup 'frontend\src') -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $target 'frontend\src\App.tsx') -Destination (Join-Path $backup 'frontend\src\App.tsx')
Copy-Item -LiteralPath (Join-Path $target 'frontend\src\index.css') -Destination (Join-Path $backup 'frontend\src\index.css')
# Only whitelisted code/documentation paths. NEVER replace .env, Docker volume, backend/instance or .venv.
$updates = @(
    'frontend\src\App.tsx',
    'frontend\src\index.css',
    'frontend\vite.config.ts',
    'frontend\vite.config.js',
    'Run_LAN.ps1',
    'PHASE7_FINAL_LAN_SETUP_BN.txt',
    'backend\tests\test_phase7_ui_lan.py'
)
foreach ($relative in $updates) {
    $from = Join-Path $source $relative
    $to = Join-Path $target $relative
    if (!(Test-Path -LiteralPath $from)) { throw "Missing packaged source file: $relative" }
    $parent = Split-Path -Parent $to
    if (!(Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
    Copy-Item -LiteralPath $from -Destination $to -Force
}
# If the older project has no launch helpers, add missing helpers only.
foreach ($helper in @('Run_Backend.ps1','Run_Frontend.ps1','START_HERE_WINDOWS.ps1')) {
    $destination = Join-Path $target $helper
    if (!(Test-Path $destination)) { Copy-Item -LiteralPath (Join-Path $source $helper) -Destination $destination }
}
Write-Host "Phase 7 source files applied to $target" -ForegroundColor Green
Write-Host "Frontend code backup: $backup" -ForegroundColor Yellow
Write-Host 'Existing Docker database, .env files and encrypted document files were NOT touched.'
Write-Host 'Next: close old frontend/backend terminals and start Run_LAN.ps1 from the existing project folder.'
