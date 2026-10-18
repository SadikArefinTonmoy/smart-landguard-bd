-- Reference schema from the exact Smart LandGuard BD 2.0 Phase 5 code.
-- The setup script initializes from the installed backend/app/database.py, not this file.

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
 id BIGSERIAL PRIMARY KEY, principal_hash TEXT NOT NULL,
 ip_hash TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_attempts_lookup ON login_attempts(principal_hash,ip_hash,created_at);
CREATE TABLE IF NOT EXISTS audit_events (
 id BIGSERIAL PRIMARY KEY, actor_id TEXT REFERENCES users(id) ON DELETE SET NULL,
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
