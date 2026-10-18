# One-time setup, for a NEWLY EXTRACTED folder. Does not delete PostgreSQL volumes.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root
if (!(Get-Command python -ErrorAction SilentlyContinue)) { throw 'Python is missing. Install Python and reopen VS Code.' }
if (!(Get-Command docker -ErrorAction SilentlyContinue)) { throw 'Docker CLI is missing. Start Docker Desktop.' }
if (!(Test-Path 'backend\.venv\Scripts\python.exe')) {
  Write-Host 'Creating Python virtual environment...'
  python -m venv 'backend\.venv'
  if ($LASTEXITCODE -ne 0) { throw 'Could not create backend virtual environment.' }
}
$py = Join-Path $root 'backend\.venv\Scripts\python.exe'
Write-Host 'Installing backend dependencies...'
& $py -m pip install -r (Join-Path $root 'backend\requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'Python dependency installation failed.' }
Write-Host 'Checking previous PostgreSQL data and recovering only missing settings...'
& $py (Join-Path $root 'scripts\prepare_existing_or_fresh.py')
if ($LASTEXITCODE -ne 0) { throw 'STOP: Setup did not complete. Read the message above. Existing DB has not been deleted.' }
Write-Host 'Preparing sample records (idempotent)...'
Push-Location (Join-Path $root 'backend')
try {
  & $py -m app.seed_demo_registry
  if ($LASTEXITCODE -ne 0) { throw 'Demo registry initialization failed.' }
} finally { Pop-Location }
Write-Host ''
Write-Host 'SETUP FINISHED: Do NOT run setup_local.py again. Keep .env files backed up.'
Write-Host 'NEXT: Run Run_Backend.ps1 in one terminal and Run_Frontend.ps1 in another.'
Write-Host 'Existing accounts will remain if selected database already contains them.'
