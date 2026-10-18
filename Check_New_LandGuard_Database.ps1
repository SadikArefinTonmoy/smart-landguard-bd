$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$py = Join-Path $root 'backend\.venv\Scripts\python.exe'
$script = Join-Path $root 'scripts\check_new_database.py'
if (!(Test-Path $py)) { throw 'Missing backend .venv. Create/install backend venv first.' }
if (!(Test-Path $script)) { throw 'Missing scripts\check_new_database.py. Copy all files from setup ZIP.' }
& $py $script
if ($LASTEXITCODE -ne 0) { throw 'Database check failed. Inspect local backend/.env and Docker status.' }
