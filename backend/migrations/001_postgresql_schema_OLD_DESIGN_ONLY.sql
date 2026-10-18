-- SCHEMA DESIGN ONLY: NOT AN ACTIVE PRODUCTION MIGRATION.
-- Requires independent security review, migrations, constraints, access policy,
-- encryption and backups before any real user's information is stored.
-- No government data connection or legal identity validation is implemented.
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TYPE user_role AS ENUM ('buyer','seller','admin');
CREATE TABLE users (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email text NOT NULL UNIQUE,
  name text NOT NULL,
  role user_role NOT NULL,
  password_hash text NOT NULL,
  is_active boolean NOT NULL DEFAULT true,
  identity_verification_state text NOT NULL DEFAULT 'not_verified',
  created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE sessions (
  token_hash char(64) PRIMARY KEY,
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at timestamptz NOT NULL DEFAULT now(),
  expires_at timestamptz NOT NULL, revoked_at timestamptz
);
CREATE INDEX sessions_user_idx ON sessions(user_id);
CREATE TABLE login_attempts (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  principal_hash char(64) NOT NULL, ip_hash char(64) NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX attempts_created_idx ON login_attempts(created_at);
CREATE TABLE audit_events (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  actor_id uuid REFERENCES users(id) ON DELETE SET NULL,
  event_type text NOT NULL, result text NOT NULL, request_id uuid NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE verification_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  purpose text NOT NULL CHECK(purpose IN ('own_records','purchase_due_diligence','professional_review')),
  authority_attested boolean NOT NULL CHECK(authority_attested),
  input_file_count integer NOT NULL CHECK(input_file_count BETWEEN 1 AND 3),
  evidence_status text NOT NULL,
  official_check_status text NOT NULL DEFAULT 'not_performed',
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX verification_events_user_idx ON verification_events(user_id,created_at DESC);
CREATE TABLE consent_grants (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  grantee_user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  scope text NOT NULL, purpose text NOT NULL,
  expires_at timestamptz NOT NULL,
  revoked_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE privacy_requests (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  request_type text NOT NULL CHECK(request_type IN ('access','delete')),
  status text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
-- Missing on purpose: government records, raw document storage, public lookups.
-- Future: policy-driven RLS, column/key encryption, lifecycle retention jobs,
-- append-only audit storage, backups, DSR operational workflow.
