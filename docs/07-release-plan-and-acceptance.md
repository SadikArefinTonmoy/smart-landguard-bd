# Smart LandGuard BD 2.0 — incremental release plan

**Goal:** Safe, consent-based land document pre-screening. Government records may only be accessed through officially sanctioned, auditable integrations. No public launch based on the current code.

## Phase 1 — delivered in this ZIP

- Kept original React layout/pages and footer, search/demo reports, 2026 year, compact scrolling header.
- Replaced plaintext demo auth with locally provisioned Argon2id credentials, HttpOnly revocable sessions, CSRF, role checks, lockout throttles, logout and password change endpoint.
- Created SQLite development metadata database and PostgreSQL *design draft*.
- Added no-raw-document-storage principle, privacy request intake, ephemeral upload analysis, upload validation, conservative cross-document comparisons, and user-purpose declaration.
- Added basic audit, per-account local request quotas, explicit `official_verification_available=false` status.

**Acceptance before Phase 2:** Re-run unit/integration tests on user's installed Python environment; manually exercise all website flows using both Buyer and Admin; ensure no sensitive data in logs; keep only test documents.

## Phase 2 — required before real user data

- Review and implement PostgreSQL with least privilege, encryption/key management, backups, migration strategy, data retention schedule.
- Create legally appropriate user identity verification, owner verification and revocable purpose/scope/time-bound document consent with evidence and multi-person admin review.
- Add two-factor authentication and secure self-signup/recovery; user-visible data export, verified deletion and notifications; mandatory audit log retention rules.
- Run document parser in isolated workers with malware scanning and strict CPU/memory/time limits, make typed metadata stores; security logs in tamper-evident storage.
- Add structured access decisions for every object: requester ID, subject/owner ID, scope, purpose, legal basis, expiration/revocation, source authority policy.
- Conduct privacy impact assessment and independent penetration testing.

## Phase 3 — lawful government integration

- Identify authoritative agency per record type (deed registry, khatian, mutation). Seek written authorization/data-sharing agreement, approved API specifications, service terms and permitted fields.
- Use least-privilege service credentials, scoped access, per-source consent/authority checks, audit every official lookup and cache only if permitted.
- Map statuses per source; 'Matched' means only that *specified fields matched at an identified authoritative source/time*, not that legal ownership is established.
- Never scrape restricted official data, automate CAPTCHA bypass, or allow arbitrary third-party bulk lookups.

## Phase 4 — controlled pilot, then possible public launch

- Controlled rollout with synthetic and formally consented data; security monitoring, incident response drills, backups/restores, fail-closed government integrations, manual exception handling and accessible Bangla notices.
- Formal privacy/legal sign-off, operational service-level controls, incident and customer support, compliance monitoring.

**Non-negotiable:** Failing to reach an official system must yield `not_checked`, not 'Verified'. A user-uploaded document that matches locally can still be forged; no score or UI badge certifies ownership.
