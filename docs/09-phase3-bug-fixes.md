# Phase 3 — targeted reliability fixes (October 2026)

This update is **incremental** over the Phase 2 PostgreSQL demo. Existing Docker compose configuration and database schema are unchanged: **no reset, no re-seeding requirement, no database migration**. Keep your `.env` and `backend/.env` files from your local installation.

## Changes

1. **Local comparison semantics:** A synthetic registry result of `demo_match` now requires all six comparison fields to be supplied and to match. If some values are missing, the response is `incomplete_demo_check`. A mismatching value yields `demo_mismatch`. A match is NOT deed authentication.
2. **Extraction integrity:** Common Bengali field labels are recognized in extracted text; fields are read from labelled lines instead of potentially consuming the next record. Crucially, decimal land areas and khatian identifiers preserve punctuation (`1.26 Bigha` and `K-221/445`). The comparison still takes a conservative position on ambiguous units and uncertain readings. OCR uses Bengali + English only if those trained languages are installed in Tesseract. **Scanned PDFs are not OCR'd by this version.**
3. **Unreadable files:** All-unreadable results halt the frontend verification wizard. The backend returns `review_assessment` (separate from parsing `status`) and explicitly indicates that government verification was NOT performed.
4. **Search:** The original property-search API now includes mouza and the frontend uses it when filtering.
5. **Dashboard:** Account-specific demo counts replace hypothetical numbers. Unreadable uploads and synthetic registry inconsistencies are flagged separately. Display wording no longer implies a completed official verification.
6. **Print-to-PDF:** The old manually assembled one-page ASCII PDF was removed. Click **Print / Save PDF**, select **Save as PDF** in Windows/Chrome/Edge print dialog. This uses the browser's Unicode fonts and pagination. Pop-ups must be allowed for localhost. Always check the resulting PDF visually, especially Bengali glyphs.
7. **Privacy response:** `/api/privacy/me` now exposes the account's encrypted private document count and differentiates temporarily processed verification inputs from intentionally retained encrypted vault documents.
8. Existing Login, Admin permissions, encrypted documents, registration, demo registry, footer, and header are retained.

## Regression checks

Use local dependencies installed in the backend venv:

```powershell
cd D:\land2\Smart_LandGuard_BD_2.0\backend
.\.venv\Scripts\Activate.ps1
$env:LANDGUARD_DATABASE_MODE = "sqlite"
python -m unittest discover -s tests -v
Remove-Item Env:\LANDGUARD_DATABASE_MODE
```

CAUTION: tests use a temporary SQLite test DB; they must not overwrite live PostgreSQL credentials. Do not use `docker compose down -v`; it deletes PostgreSQL data. Run `docker compose up -d` for your existing volume.

## Remaining launch blockers

This is **not ready for real citizens' deeds**. No official integration, no verified owner consent/identity, no scanned-PDF OCR, no antivirus/sandbox, no full rate-limited production rollout, no retention/deletion fulfillment, no independent security audit. Only synthetic test data should be used. A certificate of genuine deed ownership can never be inferred from matching demo records.
