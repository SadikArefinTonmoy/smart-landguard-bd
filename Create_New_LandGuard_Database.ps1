# Smart LandGuard BD 2.0 / local-only fresh PostgreSQL database creation.
# This script does NOT delete, reset, or modify the previous database.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $root 'backend\.venv\Scripts\python.exe'
$script = Join-Path $root 'scripts\create_fresh_postgres_db.py'

if (!(Test-Path $python)) {
  Write-Host 'STOP: Python .venv missing. Use python -m venv .venv inside backend and install requirements.'
  exit 1
}
if (!(Test-Path $script)) {
  Write-Host 'STOP: scripts\create_fresh_postgres_db.py missing. Copy all files from the setup ZIP into the project root.'
  exit 1
}
Write-Host 'Smart LandGuard BD 2.0 - NEW, SEPARATE PostgreSQL Demo Database'
Write-Host 'Existing database, accounts, files, Docker volume and encryption keys will NOT be deleted.'
& $python $script --name 'landguard_fresh_2026'
if ($LASTEXITCODE -ne 0) {
  Write-Host 'Setup did not finish. Please read the STOP message above. No old database was deleted.'
  exit $LASTEXITCODE
}
Write-Host 'DONE: New DB selected. Restart your Flask backend, then provision a new Admin.'
