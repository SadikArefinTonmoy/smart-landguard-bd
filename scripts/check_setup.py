"""Safe local diagnostic: reports status only, never prints secrets or passwords."""
from pathlib import Path
from urllib.request import urlopen
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
backend = root / 'backend' / '.env'
root_env = root / '.env'


def has_setting(path, setting):
    if not path.is_file():
        return False
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        if line.strip().startswith(setting + '=') and line.split('=', 1)[1].strip():
            return True
    return False


def line(name, ok):
    print(f"{'OK' if ok else 'CHECK'}  {name}")


line('Root .env exists', root_env.is_file())
line('Backend .env exists', backend.is_file())
line('PostgreSQL configuration exists', has_setting(backend, 'DATABASE_URL'))
line('Session secret configured', has_setting(backend, 'LANDGUARD_SECRET_KEY'))
line('Document encryption key configured', has_setting(backend, 'LANDGUARD_FILE_ENCRYPTION_KEY'))
if not root_env.exists() or not backend.exists():
    print('IMPORTANT: Restore both secret files from your earlier backup. Do not regenerate them for an existing database.')

try:
    result = subprocess.run(
        ['docker', 'inspect', '--format', '{{.State.Health.Status}}', 'landguard-demo-postgres'],
        capture_output=True, text=True, timeout=5, check=False,
    )
    line('PostgreSQL Docker container healthy', result.returncode == 0 and result.stdout.strip() == 'healthy')
except (OSError, subprocess.TimeoutExpired):
    line('PostgreSQL Docker container healthy', False)

try:
    with urlopen('http://127.0.0.1:8000/api/health', timeout=3) as res:
        line('Flask API responding', res.status == 200)
except Exception:
    line('Flask API responding', False)

print('Note: local development system only; does not verify the authenticity of land documents.')
