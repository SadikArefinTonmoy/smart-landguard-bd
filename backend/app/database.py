"""DB-API layer: PostgreSQL for the full demo; explicit SQLite only for tests.

Credentials live in environment variables. All records here are SYNTHETIC demo data.
"""
import os
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DB = BASE_DIR / 'instance' / 'landguard.sqlite3'
from dotenv import load_dotenv
load_dotenv(BASE_DIR / '.env')

# IDs and timestamps are text on both backends to preserve Phase 1 compatibility.
SCHEMA = '''
CREATE TABLE IF NOT EXISTS users (
 id TEXT PRIMARY KEY, email TEXT NOT NULL UNIQUE,
 name TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('buyer','seller','admin')),
 password_hash TEXT NOT NULL, is_active INTEGER NOT NULL DEFAULT 1,
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
 token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 created_at TEXT NOT NULL, expires_at TEXT NOT NULL, revoked_at TEXT, last_seen_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
CREATE TABLE IF NOT EXISTS login_attempts (
 id INTEGER PRIMARY KEY AUTOINCREMENT, principal_hash TEXT NOT NULL,
 ip_hash TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_attempts_lookup ON login_attempts(principal_hash,ip_hash,created_at);
CREATE TABLE IF NOT EXISTS audit_events (
 id INTEGER PRIMARY KEY AUTOINCREMENT, actor_id TEXT REFERENCES users(id) ON DELETE SET NULL,
 event_type TEXT NOT NULL, result TEXT NOT NULL, created_at TEXT NOT NULL, request_id TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_audit_actor ON audit_events(actor_id,created_at);
CREATE TABLE IF NOT EXISTS verification_events (
 id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 purpose TEXT NOT NULL CHECK(purpose IN ('own_records','purchase_due_diligence','professional_review')),
 authority_attested INTEGER NOT NULL CHECK(authority_attested = 1),
 input_file_count INTEGER NOT NULL, evidence_status TEXT NOT NULL,
 official_check_status TEXT NOT NULL DEFAULT 'not_performed', created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_verification_user ON verification_events(user_id,created_at);
CREATE TABLE IF NOT EXISTS privacy_requests (
 id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 request_type TEXT NOT NULL CHECK(request_type IN ('access','delete')),
 status TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS land_records (
 id TEXT PRIMARY KEY, owner_name TEXT NOT NULL, district TEXT NOT NULL,
 upazila TEXT NOT NULL, mouza TEXT NOT NULL, khatian TEXT NOT NULL,
 dag TEXT NOT NULL, land_area TEXT NOT NULL,
 is_demo INTEGER NOT NULL DEFAULT 1 CHECK(is_demo=1),
 status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','inactive')),
 created_by TEXT REFERENCES users(id) ON DELETE SET NULL,
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_demo_land_search ON land_records(district,mouza);
CREATE TABLE IF NOT EXISTS private_documents (
 id TEXT PRIMARY KEY, owner_user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 original_filename TEXT NOT NULL, mime_type TEXT NOT NULL, byte_count INTEGER NOT NULL,
 storage_name TEXT NOT NULL UNIQUE, sha256_hash TEXT NOT NULL,
 label TEXT NOT NULL DEFAULT 'Demo document',
 created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_document_owner ON private_documents(owner_user_id,created_at);
CREATE TABLE IF NOT EXISTS document_grants (
 id TEXT PRIMARY KEY, document_id TEXT NOT NULL REFERENCES private_documents(id) ON DELETE CASCADE,
 grantee_user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 granted_by TEXT NOT NULL REFERENCES users(id), purpose TEXT NOT NULL,
 expires_at TEXT NOT NULL, revoked_at TEXT, created_at TEXT NOT NULL,
 UNIQUE(document_id, grantee_user_id)
);
CREATE INDEX IF NOT EXISTS idx_grants_grantee ON document_grants(grantee_user_id,expires_at);
CREATE TABLE IF NOT EXISTS registry_checks (
 id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 record_id TEXT REFERENCES land_records(id) ON DELETE SET NULL,
 purpose TEXT NOT NULL, result TEXT NOT NULL,
 matched_fields TEXT NOT NULL, mismatched_fields TEXT NOT NULL,
 created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_registry_checks_user ON registry_checks(user_id,created_at);
'''
POSTGRES_SCHEMA = SCHEMA.replace('id INTEGER PRIMARY KEY AUTOINCREMENT', 'id BIGSERIAL PRIMARY KEY')

def utcnow():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')

def backend_mode():
    mode = os.getenv('LANDGUARD_DATABASE_MODE', 'postgresql').lower()
    if mode not in ('postgresql', 'sqlite'):
        raise RuntimeError('LANDGUARD_DATABASE_MODE must be postgresql or sqlite')
    return mode

def db_path():
    raw = os.getenv('LANDGUARD_DB_PATH')
    return Path(raw).expanduser().resolve() if raw else DEFAULT_DB

class HybridRow(dict):
    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.values())[key]
        return super().__getitem__(key)

class Result:
    def __init__(self, cursor):
        self.cursor = cursor
    def fetchone(self):
        row = self.cursor.fetchone()
        return HybridRow(row) if row is not None else None
    def fetchall(self):
        return [HybridRow(row) for row in self.cursor.fetchall()]

class PGConnection:
    def __init__(self, raw):
        self.raw = raw
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            self.raw.rollback()
        else:
            self.raw.commit()
        self.raw.close()
    def execute(self, statement, params=()):
        return Result(self.raw.execute(statement.replace('?', '%s'), params))

def connect():
    if backend_mode() == 'sqlite':
        path = db_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(path), timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys = ON')
        conn.execute('PRAGMA busy_timeout = 10000')
        return conn
    url = os.getenv('DATABASE_URL', '').strip()
    if not url:
        raise RuntimeError('DATABASE_URL is required for PostgreSQL. Copy backend/.env.example to backend/.env and configure credentials.')
    import psycopg
    from psycopg.rows import dict_row
    # Docker Desktop publishes PostgreSQL on IPv4 loopback. On some Windows
    # machines resolving `localhost` can stall behind IPv6 / DNS. Restrict this
    # override to a local-development URL; remote DB hosts are left untouched.
    from urllib.parse import urlsplit
    host = urlsplit(url).hostname
    options = {'host': '127.0.0.1'} if host == 'localhost' and os.getenv('LANDGUARD_ENV', 'development') == 'development' else {}
    return PGConnection(psycopg.connect(url, row_factory=dict_row, connect_timeout=6, **options))

def initialize():
    if backend_mode() == 'sqlite':
        with connect() as db:
            db.execute('PRAGMA journal_mode = WAL')
            db.executescript(SCHEMA)
    else:
        with connect() as db:
            for statement in POSTGRES_SCHEMA.split(';'):
                if statement.strip():
                    db.execute(statement)

def audit(actor_id, event_type, result, request_id):
    with connect() as db:
        db.execute('INSERT INTO audit_events(actor_id,event_type,result,created_at,request_id) VALUES (?,?,?,?,?)',
                   (actor_id, event_type, result, utcnow(), request_id))
