#!/usr/bin/env python3
"""Safe local-only configuration recovery for Smart LandGuard BD 2.0 Phase 7.

Reads credentials from an EXISTING local Docker PostgreSQL container. It never
resets a password, deletes a volume, modifies a database, or overwrites an .env.
Refuses fresh encryption keys if any existing document records/files are found.
Run this script from the extracted project's ROOT folder using Python 3.9+.
"""
from __future__ import annotations

import base64
import os
from pathlib import Path
import secrets
import subprocess
import sys
from urllib.parse import quote

CONTAINER = 'landguard-demo-postgres'
DATABASE = 'landguard_fresh_2026'
DATABASE_USER = 'landguard_demo'
KNOWN_DATABASES = ('landguard_fresh_2026', 'landguard_demo')
ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / 'backend'
ROOT_ENV = ROOT / '.env'
BACKEND_ENV = BACKEND / '.env'


def stop(message: str) -> None:
    print(f'STOP: {message}', file=sys.stderr)
    sys.exit(1)


def docker(*args: str) -> str:
    try:
        completed = subprocess.run(
            ['docker', *args], text=True, capture_output=True, timeout=25, check=False
        )
    except (OSError, subprocess.TimeoutExpired):
        stop('Docker Desktop/CLI unavailable. Start Docker Desktop and try again.')
    if completed.returncode:
        stop('Docker check failed. Nothing was changed; verify the existing container is running.')
    return completed.stdout.strip()


def psql(database: str, sql: str) -> str:
    return docker('exec', CONTAINER, 'psql', '-X', '-U', DATABASE_USER,
                  '-d', database, '-tA', '-v', 'ON_ERROR_STOP=1', '-c', sql)


def read_root_password(path: Path) -> str | None:
    if not path.exists():
        return None
    # Only accept simple, non-multiline dot-env entries. Do not accidentally use
    # a wrong credential, and never print the value in errors or logs.
    lines = path.read_text(encoding='utf-8-sig').splitlines()
    entries = [line.split('=', 1)[1].strip() for line in lines
               if line.strip().startswith('POSTGRES_PASSWORD=')]
    if len(entries) != 1:
        stop('Existing root .env is missing/duplicates POSTGRES_PASSWORD; resolve manually.')
    val = entries[0]
    if len(val) >= 2 and val[0] == val[-1] and val[0] in ('"', "'"):
        val = val[1:-1]
    return val


def inspect_documents(database: str) -> int:
    exists = psql(database, "SELECT to_regclass('public.private_documents') IS NOT NULL;")
    if exists == 'f':
        return 0
    if exists != 't':
        stop(f'Could not verify document table in {database}.')
    count = psql(database, 'SELECT COUNT(*) FROM public.private_documents;')
    if not count.isdecimal():
        stop(f'Could not verify private document count in {database}.')
    return int(count)


def write_no_overwrite(path: Path, value: str) -> None:
    try:
        with path.open('x', encoding='utf-8', newline='\n') as handle:
            handle.write(value)
    except FileExistsError:
        stop(f'{path.relative_to(ROOT)} already exists; no secrets were overwritten.')
    except OSError:
        stop(f'Could not create {path.relative_to(ROOT)}; inspect permissions.')


def main() -> None:
    print('Smart LandGuard Phase 7: recover missing LOCAL .env safely')
    if not (ROOT / 'docker-compose.yml').is_file() or not (BACKEND / 'app' / 'database.py').is_file():
        stop('Save this file in the project ROOT: D:\\land2\\Smart_LandGuard_BD_2.0')
    if BACKEND_ENV.exists():
        stop('backend/.env already exists. Do not replace existing security keys.')

    health = docker('inspect', '--format', '{{.State.Health.Status}}', CONTAINER)
    if health != 'healthy':
        stop(f'Container is not healthy ({health}). Start the existing container first.')
    raw_env = docker('inspect', '--format', '{{range .Config.Env}}{{println .}}{{end}}', CONTAINER)
    passwords = [entry.partition('=')[2] for entry in raw_env.splitlines()
                 if entry.startswith('POSTGRES_PASSWORD=')]
    if len(passwords) != 1 or not passwords[0]:
        stop('Cannot recover the EXISTING PostgreSQL password; restore original configuration.')
    password = passwords[0]
    if '\n' in password or '\r' in password:
        stop('Unsupported multiline PostgreSQL password; manual recovery required.')

    # psql in the existing container uses local peer/trust auth; an actual local
    # Python-to-PostgreSQL auth check can be done afterward with check_new_database.py.
    dbs = set(psql('postgres', 'SELECT datname FROM pg_database WHERE datallowconn;').splitlines())
    if DATABASE not in dbs:
        stop(f'Existing {DATABASE} database was not found. No new database will be created.')

    # These counts are read-only. Recovery MUST stop before minting a new Fernet
    # key when any old document exists because old ciphertext would be unreadable.
    for db in KNOWN_DATABASES:
        if db in dbs:
            count = inspect_documents(db)
            print(f'Checked encrypted document metadata in {db}: {count} record(s)')
            if count:
                stop('Encrypted document records exist. Restore the ORIGINAL backend/.env/key from backup; new keys would permanently break decryption.')

    for vault in (BACKEND / 'instance' / 'encrypted_documents',
                  BACKEND / 'instance' / 'private_documents'):
        if vault.is_dir() and any(p.is_file() for p in vault.rglob('*')):
            stop(f'Encrypted document files exist in {vault}. Recover ORIGINAL encryption key first.')
    # The current Phase 7 backend stores encrypted objects under backend/instance.
    # Do not infer that a wiped folder's old files are recoverable.

    existing_password = read_root_password(ROOT_ENV)
    if existing_password is not None and existing_password != password:
        stop('Root .env password does not match Docker container. Neither file was changed.')

    records = psql(DATABASE, 'SELECT COUNT(*) FROM public.land_records;')
    users = psql(DATABASE, 'SELECT COUNT(*) FROM public.users;')
    if not records.isdecimal() or not users.isdecimal():
        stop('Could not validate selected database records/users. No files were changed.')
    print(f'Existing database confirmed: {DATABASE}; land records={records}; users={users}')

    if existing_password is None:
        # Quote so a PostgreSQL password with #/spaces is parsed as a single value.
        quoted = password.replace('\\', '\\\\').replace('"', '\\"')
        write_no_overwrite(ROOT_ENV, f'POSTGRES_PASSWORD="{quoted}"\n')
        print('OK: root .env recovered (password NOT printed)')
    else:
        print('OK: root .env retained unchanged')

    key = base64.urlsafe_b64encode(os.urandom(32)).decode('ascii')
    secret = secrets.token_hex(32)
    password_url = quote(password, safe='')
    backend_text = (
        '# Recovered for LOCAL ACADEMIC DEMO only. Never share/commit this file.\n'
        'LANDGUARD_ENV=development\n'
        'LANDGUARD_DATABASE_MODE=postgresql\n'
        f'DATABASE_URL=postgresql://{DATABASE_USER}:{password_url}@127.0.0.1:5432/{DATABASE}\n'
        'LANDGUARD_ALLOWED_ORIGINS=http://localhost:4173,http://127.0.0.1:4173\n'
        f'LANDGUARD_SECRET_KEY={secret}\n'
        f'LANDGUARD_FILE_ENCRYPTION_KEY={key}\n'
    )
    write_no_overwrite(BACKEND_ENV, backend_text)
    print('OK: backend/.env recovered for the EXISTING database')
    print('NO Docker volume/database/users/land records were modified.')
    print('Old browser sessions will need a new login (session signing key was missing).')
    print('IMPORTANT: Keep BOTH new .env files backed up privately and never send their contents.')
    print('NEXT: Test Python DB connectivity; then run Run_LAN.ps1.')


if __name__ == '__main__':
    main()
