#!/usr/bin/env python3
"""Read-only check against the currently configured Smart LandGuard DB."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

try:
    from app.database import backend_mode, connect
    if backend_mode() != "postgresql":
        raise RuntimeError("Backend is not in PostgreSQL mode")
    with connect() as db:
        row = db.execute(
            "SELECT current_database() AS name, "
            "(SELECT COUNT(*) FROM land_records) AS records, "
            "(SELECT COUNT(*) FROM users) AS users"
        ).fetchone()
    print(f"DB: {row['name']} demo_records: {row['records']} users: {row['users']}")
except Exception as exc:
    print(f"Database check failed: {type(exc).__name__}. Check Docker and backend/.env locally (don't share credentials).", file=sys.stderr)
    raise SystemExit(1)
