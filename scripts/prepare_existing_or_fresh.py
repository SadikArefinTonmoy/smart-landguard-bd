#!/usr/bin/env python3
"""Local Windows bootstrap. Safe with existing Docker data.

Does not delete Docker databases, overwrite existing secrets, or print passwords.
Will refuse recreating an encryption key when document records/files exist.
Only for LOCAL DEVELOPMENT / synthetic sample data.
"""
from __future__ import annotations

import os
import secrets
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import quote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
ROOT_ENV = ROOT / '.env'
BACKEND_ENV = ROOT / 'backend' / '.env'
CONTAINER = 'landguard-demo-postgres'
KNOWN_DBS = ('landguard_fresh_2026', 'landguard_demo')


def fail(message):
    print('STOP: ' + message, file=sys.stderr)
    raise SystemExit(1)


def docker(*argv, timeout=25, required=True):
    try:
        r = subprocess.run(['docker', *argv], text=True, capture_output=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        fail('Docker Desktop is not running or Docker CLI is not available.')
    if required and r.returncode:
        fail('Docker command failed. Check Docker Desktop, then try again; no data was removed.')
    return r


def get_container():
    r = docker('inspect', '--format', '{{.Name}}', CONTAINER, required=False)
    return r.returncode == 0


def container_password():
    result = docker('inspect', '--format', '{{range .Config.Env}}{{println .}}{{end}}', CONTAINER)
    passwords = [line.split('=', 1)[1] for line in result.stdout.splitlines() if line.startswith('POSTGRES_PASSWORD=')]
    if len(passwords) != 1 or not passwords[0]:
        fail('Existing Docker container has no recoverable PostgreSQL password. Restore your private backup.')
    return passwords[0]


def get_databases():
    result = docker('exec', CONTAINER, 'psql', '-U', 'landguard_demo', '-d', 'postgres', '-At',
                    '-c', 'SELECT datname FROM pg_database WHERE datallowconn;')
    return set(result.stdout.strip().splitlines())


def wait_postgres_ready():
    for _ in range(30):
        result = docker('exec', CONTAINER, 'pg_isready', '-U', 'landguard_demo', '-d', 'postgres', required=False)
        if result.returncode == 0:
            return
        time.sleep(2)
    fail('PostgreSQL did not become ready within 60 seconds. Check Docker Desktop logs.')


def private_document_count(db):
    # Direct psql inside the container does not reveal the DB password.
    check = docker('exec', CONTAINER, 'psql', '-U', 'landguard_demo', '-d', db, '-At',
                   '-c', "SELECT COALESCE(to_regclass('public.private_documents')::text, 'MISSING');")
    if check.stdout.strip() == 'MISSING':
        fail('Cannot verify documents in ' + db + '; stop to avoid losing encryption access.')
    out = docker('exec', CONTAINER, 'psql', '-U', 'landguard_demo', '-d', db, '-At',
                 '-c', 'SELECT COUNT(*) FROM public.private_documents;').stdout.strip()
    try:
        return int(out)
    except ValueError:
        fail('Could not safely check document count in ' + db + '.')


def read_config_value(path, key):
    # The app uses python-dotenv, and the venv has been provisioned before this script.
    from dotenv import dotenv_values
    if not path.exists():
        return None
    return dotenv_values(path).get(key)


def write_private(path, value):
    with path.open('x', encoding='utf8', newline='\n') as handle:
        handle.write(value)
    if os.name != 'nt':
        path.chmod(0o600)


def recover_existing():
    password = container_password()
    if ROOT_ENV.exists():
        if read_config_value(ROOT_ENV, 'POSTGRES_PASSWORD') != password:
            fail('Root .env does not match existing Docker password; do not overwrite or reset the database.')
        print('OK: Root .env preserved')
    else:
        write_private(ROOT_ENV, 'POSTGRES_PASSWORD=' + password + '\n')
        print('OK: Root .env recovered from existing Docker container (secret not shown)')

    # Container may be stopped; safe start has no data deletion.
    state = docker('inspect', '--format', '{{.State.Running}}', CONTAINER).stdout.strip()
    if state != 'true':
        docker('start', CONTAINER)
        print('OK: Existing PostgreSQL container started')
    wait_postgres_ready()

    dbs = get_databases()
    if BACKEND_ENV.exists():
        db_url = read_config_value(BACKEND_ENV, 'DATABASE_URL') or ''
        if not db_url or urlsplit(db_url).path.lstrip('/') not in dbs:
            fail('Existing backend/.env has an invalid database target. Restore/check it, do not overwrite secrets.')
        print('OK: Existing backend/.env preserved')
        return

    # Missing encryption key: do not silently regenerate if ANY known existing DB has document records.
    for db in KNOWN_DBS:
        if db in dbs and private_document_count(db):
            fail(f'{db} has encrypted document metadata. Original backend/.env backup is REQUIRED; nothing overwritten.')
    vault = ROOT / 'backend' / 'instance' / 'encrypted_documents'
    if vault.is_dir() and any(p.is_file() for p in vault.rglob('*')):
        fail('Encrypted vault files exist. Restore original backend/.env to recover access.')

    target = next((db for db in KNOWN_DBS if db in dbs), None)
    if not target:
        fail('No recognized previous database found. Stop and inspect Docker before making a new one.')

    from cryptography.fernet import Fernet
    config = ('# RECOVERED FOR LOCAL DEMO ONLY. Store privately and back up outside ZIP.\n'
              'LANDGUARD_ENV=development\nLANDGUARD_DATABASE_MODE=postgresql\n'
              'DATABASE_URL=postgresql://landguard_demo:' + quote(password, safe='') +
              '@127.0.0.1:5432/' + target + '\n'
              'LANDGUARD_ALLOWED_ORIGINS=http://localhost:4173,http://127.0.0.1:4173\n'
              'LANDGUARD_SECRET_KEY=' + secrets.token_hex(32) + '\n'
              'LANDGUARD_FILE_ENCRYPTION_KEY=' + Fernet.generate_key().decode('ascii') + '\n')
    write_private(BACKEND_ENV, config)
    print('OK: Missing backend/.env recreated for existing ' + target + ' (without modifying records)')
    print('NOTE: Old browser sessions must sign in again; previous lost encryption keys cannot be recovered.')


def new_environment():
    if ROOT_ENV.exists() or BACKEND_ENV.exists():
        fail('There is no Docker container but .env files exist. Do not reset credentials; investigate volume/backups.')
    volumes = docker('volume', 'ls', '--format', '{{.Name}}').stdout.splitlines()
    if any('landguard_demo_pg' in name for name in volumes):
        fail('An old PostgreSQL volume exists but the container is missing. Restore its credentials/container first.')
    script = ROOT / 'scripts' / 'setup_local.py'
    result = subprocess.run([sys.executable, str(script)], cwd=ROOT)
    if result.returncode:
        fail('Fresh setup failed.')
    print('OK: Fresh local secrets created (no existing Docker data detected)')


def verify_current_connection():
    from dotenv import dotenv_values
    import psycopg
    url = dotenv_values(BACKEND_ENV).get('DATABASE_URL')
    if not url:
        fail('DATABASE_URL not configured.')
    parts = urlsplit(url)
    dbs = get_databases()
    if parts.path.lstrip('/') not in dbs:
        fail('Selected database not found in existing PostgreSQL container.')
    try:
        opts = {'host': '127.0.0.1'} if parts.hostname == 'localhost' else {}
        with psycopg.connect(url, connect_timeout=7, **opts) as connection:
            connection.execute('SELECT 1').fetchone()
    except psycopg.Error:
        fail('Python-to-PostgreSQL authentication failed. Existing records were not modified.')
    print('OK: Backend PostgreSQL connection:', parts.path.lstrip('/'))


def main():
    if not (ROOT / 'backend' / 'app' / 'main.py').is_file():
        fail('Run the provided script from the unzipped project, not from another folder.')
    docker('info', '--format', '{{.ServerVersion}}')
    if get_container():
        recover_existing()
    else:
        new_environment()
    # Existing container: compose should reuse it, never delete volume.
    docker('compose', '-f', str(ROOT / 'docker-compose.yml'), '--project-directory', str(ROOT), 'up', '-d', timeout=120)
    wait_postgres_ready()
    verify_current_connection()
    print('READY: Existing data was preserved. Keep the generated .env files private.')


if __name__ == '__main__':
    main()
