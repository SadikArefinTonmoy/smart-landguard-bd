# API endpoints — Smart LandGuard BD 2.0 (Phase 1)

These are **local development** API endpoints. POST endpoints require a CSRF challenge (`GET /api/auth/csrf`) and an `X-CSRF-Token` header, plus `credentials: 'include'` on the client. Protected routes authenticate from a server-managed HttpOnly cookie.

| Method | Endpoint | Access | Notes |
|---|---|---|---|
| GET | `/api/health` | public | demo status, no PII |
| GET | `/api/official/status` | public | explicitly `connected=false` |
| GET | `/api/auth/csrf` | public | issue short-lived CSRF challenge |
| POST | `/api/auth/login` | csrf + credentials | Argon2id check and lockout |
| GET | `/api/auth/me` | login | current user only |
| POST | `/api/auth/logout` | login + csrf | revoke session |
| POST | `/api/auth/change-password` | login + csrf | current password required; revoke sessions |
| GET | `/api/properties` | public | **fictional demo listings only** |
| GET | `/api/properties/:id` | public | fictional demo detail |
| GET | `/api/properties/:id/purchase-checklist` | public | fictional readiness checklist |
| GET | `/api/reports/:id` | public | fictional report, official check not performed |
| GET | `/api/dashboard` | login | synthetic dashboard data |
| GET | `/api/moderation` | **admin** | sample admin queue |
| POST | `/api/verification/extract` | login + csrf + purpose + authorityAttested | local parsing only, 1–3 files, ≤10 MiB each, quota 10/hour |
| GET | `/api/privacy/me` | login | own account/verification metadata |
| POST | `/api/privacy/request` | login + csrf | queue manual access/delete request; quota 3/day |

**No official government records are fetched or stored.**

Future endpoints for official government verification, verified owner consent, genuine citizen identity, and official record access are **not implemented** and must remain unavailable until written authorization and security/legal review.
