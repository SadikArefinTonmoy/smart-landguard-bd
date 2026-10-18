"""Generate local-only secrets/URLs without printing credentials. Python stdlib only.

DO NOT use generated credentials in production. A real deployment requires review.
"""
from pathlib import Path
import base64
import secrets
import sys
import urllib.parse

root=Path(__file__).resolve().parents[1]
root_env=root/'.env'
backend_env=root/'backend'/'.env'
if root_env.exists() or backend_env.exists():
    print('Existing .env found. Stopping to avoid overwriting database or encryption keys.')
    print('For first setup only, remove stale .env files after backing them up, then rerun.')
    sys.exit(1)
password=secrets.token_urlsafe(24)
secret=secrets.token_hex(32)
file_key=base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('ascii')
root_env.write_text(f'POSTGRES_PASSWORD={password}\n',encoding='utf8')
backend_env.write_text('''# GENERATED LOCAL DEMO CONFIG. KEEP SECRET. NOT FOR PUBLIC HOSTING.
LANDGUARD_ENV=development
LANDGUARD_DATABASE_MODE=postgresql
DATABASE_URL=postgresql://landguard_demo:%s@localhost:5432/landguard_demo
LANDGUARD_ALLOWED_ORIGINS=http://localhost:4173,http://127.0.0.1:4173
LANDGUARD_SECRET_KEY=%s
LANDGUARD_FILE_ENCRYPTION_KEY=%s
'''%(urllib.parse.quote(password,safe=''),secret,file_key), encoding='utf8')
if sys.platform!='win32':
    root_env.chmod(0o600); backend_env.chmod(0o600)
print('Generated local PostgreSQL configuration at project .env and backend/.env.')
print('Secrets are not displayed. Do not commit, publish, or share .env files.')
