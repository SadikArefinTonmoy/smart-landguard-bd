# Smart LandGuard BD 2.0 — Phase 1 security architecture

## Scope and trust boundaries

`React SPA (localhost:4173)` -> `Flask API (localhost:8000)` -> `SQLite local dev metadata`.

- Browser **cannot** obtain a session token from JS: auth cookie is HttpOnly, SameSite=Lax; server looks up a SHA-256 hash of the token in the sessions table.
- Session cookies require HTTPS in a later production environment. Production mode is **blocked** in this repo.
- POSTs have Origin checks and a short-lived CSRF challenge bound to a separate HttpOnly cookie.
- Only `/api/properties`, property sample details and demo reports are public. `/api/dashboard` is signed-in-only; `/api/moderation` is Admin-only; document upload and privacy controls require login.
- Login credentials are Argon2id-hashed; users must be provisioned through a local CLI. No fixed default passwords.
- The login throttling table uses keyed hashes of email and remote IP, not raw addresses. This is not a distributed rate limiter; a multi-node implementation remains necessary.
- Security event audit records do not include uploaded documents, document filenames, document contents, raw IP, or raw extracted owner details.
- The only persistent verification data are user ID, count of documents, purpose, timestamp, result and the permanent `official_check_status='not_performed'`.
- No government database connector exists. No result establishes deed authenticity, title, ownership or a right to access confidential government data.
- Owner consent grants are *schema-only*. We will **not** enable third-party confidential record retrieval until government permission, legally sufficient consent, identity verification, consent expiration/revocation, and operator review exist.

## Data model

- `users` → unique email, Argon2id password hash, role, activation state
- `sessions` → salted random session ID hash, expiry, revocation; foreign-key user
- `login_attempts` → hashed rate-limit keys, timestamp; short lifecycle
- `audit_events` → minimal actor ID, event type, result, request ID, timestamp
- `verification_events` → metadata, no document bytes or parsed PII
- `privacy_requests` → access/deletion requests; **manual fulfillment pending**
- `consent_grants` → reserved only; no operational endpoints, cannot grant official data access

`backend/app/database.py` is the active SQLite development schema. `backend/migrations/001_postgresql_schema_DESIGN_ONLY.sql` is a **review draft**, not an applied production migration. PostgreSQL integration and managed private object storage remain later phases.

## Threat model & limitations

Threats: credential stuffing, session theft, unauthorized API access, cross-site requests, parser exploits, exfiltration, insider curiosity, falsely claimed government data verification, and misuse of customer records.

Phase 1 controls: session revocation, strict authorization checks, local Origin allowlist, CSRF, 5 failures/15-minute local throttle, extension and magic-byte checks, ≤3 files / ≤10 MB each, request cap 32 MB, limited PDF pages, limited OCR runtime, minimal storage, warnings and audit metadata.

**Still required before any public launch:** HTTPS with reverse proxy, PostgreSQL with encryption and least-privilege roles, encrypted external storage (only if persistence needed), file malware scanning and isolated parsing workers, monitoring and alerting, distributed rate limiting, verified identity and consent, purpose-specific access with review, retention/deletion workflow, independent penetration tests, verified government API authorizations and legal/privacy review. Users must not upload real private records to this Phase 1 dev environment.

## API security matrix

| API | User | Permission |
|---|---|---|
| `/api/health`, `/api/official/status` | anyone | health/status only |
| `/api/auth/csrf` | anyone | issue CSRF challenge |
| `/api/auth/login` | anyone + CSRF | login, throttled |
| `/api/auth/me` | signed in | own identity only |
| `/api/auth/logout`, `/api/auth/change-password` | signed in + CSRF | own session/password |
| `/api/properties`, `/api/properties/:id`, `/api/reports/:id` | anyone | synthetic demo data only |
| `/api/dashboard` | signed in | synthetic demo stats only |
| `/api/moderation` | admin | synthetic admin queue |
| `/api/verification/extract` | signed in + CSRF + declaration | private *ephemeral* local processing |
| `/api/privacy/me` | signed in | own stored activity metadata |
| `/api/privacy/request` | signed in + CSRF | record manual access/deletion request |
