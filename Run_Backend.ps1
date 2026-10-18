$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$py = Join-Path $root 'backend\.venv\Scripts\python.exe'
if (!(Test-Path $py)) { throw 'Run START_HERE_WINDOWS.ps1 first.' }
if (!(Test-Path (Join-Path $root 'backend\.env'))) { throw 'backend/.env is missing. Run START_HERE_WINDOWS.ps1 safely first.' }
Set-Location (Join-Path $root 'backend')
Write-Host 'Starting Flask API at http://localhost:8000 ...'
& $py -m app.main
