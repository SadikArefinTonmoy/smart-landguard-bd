# Smart LandGuard BD 2.0 — Phase 6 Final Update

## Changes from the supplied PostgreSQL project

1. Sample property search results and the selected property's details render within the search panel, immediately below the search controls; the Reports navigation anchor still works.
2. Document verification output differentiates missing evidence, actual extracted-field mismatches, and readable-document warnings. Repeated generic government advice is no longer used as every Bengali result translation. A single explicit not-government-verified notice remains in the visible result summary.
3. The demo registry comparison form and Admin create-record form have separate clear/reset actions, with discard confirmation for entered values. Admin form clears automatically only after a successful database write.
4. Removed the redundant home “এক জায়গায় নথি যাচাই” card. The full upload/extraction/verification wizard and the top “দলিল যাচাই” navigation remain.
5. Admin demo registry shows the first four records initially, followed by “আরও দেখুন”; the expanded list has “কম দেখুন”. Admin deactivation remains protected by the existing role-based backend route.
6. Removed the active green line under top navigation and the top Demo Registry shortcut. The registry workspace and its saved records are still available below the dashboard.

## Database compatibility and important protection

- The SQL schema in `backend/app/database.py` is **unchanged** from the previous provided full-project ZIP. No migration or data reset is required.
- Local development PostgreSQL connection recognizes `localhost` and uses the explicit IPv4 loopback to avoid intermittent Windows Docker Desktop resolution delays. Remote PostgreSQL hosts are not changed.
- Backend CSRF, role guards, Argon2 password hashes and private-document encryption controls remain in place.
- `Upgrade_Safely_Preserve_Database.ps1` updates source files only, checks that both `.env` files already exist and saves copies of those secrets **outside the project folder**. It does not touch Docker volumes, existing users, sessions, or encrypted document directories.
- The archive intentionally does **not** contain `.env`, `backend/.env`, `.venv`, `node_modules`, databases, or personal credentials.

## Verification completed in this packaging environment

- `tsc -p tsconfig.json --noEmit`: passed, using offline React/TS type definitions from original uploaded source. Full Vite build was not available in this environment.
- Python syntax compilation: passed.
- 4 earlier Phase-3 SQLite/document regression tests: passed.
- 3 Phase-6 isolated SQLite/source compatibility checks: passed.
- Confirmed PostgreSQL schema definition unchanged by byte-for-byte comparison to previous full-project ZIP.
- **Not executed here:** live PostgreSQL-in-Docker and live browser Login/Sign Up end-to-end test. Run the local smoke test below before using the project.

## Windows smoke test after upgrading

Run PostgreSQL, Backend on port 8000 and Vite on port 4173. Open the site at `http://localhost:4173` consistently.

```powershell
cd D:\land2\Smart_LandGuard_BD_2.0
python scripts/check_setup.py
powershell -NoProfile -ExecutionPolicy Bypass -File .\Check_New_LandGuard_Database.ps1
.\backend\.venv\Scripts\python.exe scripts\check_login_flow.py --email admin@example.test
```

The login-flow script asks for the known account password in a hidden prompt and checks CSRF → Login → `/api/auth/me` → Logout → session revocation. It does not print or store credentials.

For the previous automatic Flask test suite (requires installed dependencies):

```powershell
cd D:\land2\Smart_LandGuard_BD_2.0\backend
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_phase5_guest_auth.py" -v
```

Do not use `docker compose down -v`, do not recreate `landguard_fresh_2026`, and do not share `.env`.

This remains a **demo prototype**, not a government land title verification service and not yet suitable for real personal land documents.
