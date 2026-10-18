#!/usr/bin/env python3
"""Create a SEPARATE demo PostgreSQL database for the existing Smart LandGuard BD app.

Does not drop or alter the previous PostgreSQL database, users, or Docker volume.
Does not regenerate or overwrite session / document encryption keys.
Run using the backend virtual environment's Python interpreter.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
ENV_PATH = BACKEND / ".env"
BACKUP_DIR = ROOT.parent / "Smart_LandGuard_Private_Backups"
DEFAULT_NAME = "landguard_fresh_2026"


def die(message: str) -> None:
    raise SystemExit("STOP: " + message)


def new_url_with_database(original: str, new_db: str) -> str:
    parts = urlsplit(original)
    if parts.scheme not in ("postgresql", "postgres") or not parts.hostname:
        die("DATABASE_URL must be a valid PostgreSQL URL.")
    if parts.hostname not in ("localhost", "127.0.0.1"):
        die("This local-only setup only supports localhost PostgreSQL.")
    if parts.fragment:
        die("Unexpected URL fragment; please inspect DATABASE_URL locally.")
    # Avoid Windows IPv6 localhost connection delays; preserve existing credentials verbatim.
    netloc = parts.netloc
    if parts.hostname == "localhost":
        prefix, sep, hostpart = netloc.rpartition("@")
        if not sep:
            prefix = ""
            hostpart = netloc
        if not hostpart.startswith("localhost"):
            die("Unexpected localhost URL layout.")
        hostpart = "127.0.0.1" + hostpart[len("localhost"):]
        netloc = prefix + ("@" if sep else "") + hostpart
    return urlunsplit((parts.scheme, netloc, "/" + new_db, parts.query, ""))


def substitute_url(text: str, new_url: str) -> str:
    pattern = re.compile(r"^\s*DATABASE_URL\s*=.*$", re.MULTILINE)
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        die("backend/.env must have exactly one DATABASE_URL= setting.")
    return pattern.sub(lambda _: "DATABASE_URL=" + new_url, text, count=1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a fresh, separate local Smart LandGuard PostgreSQL demo database")
    parser.add_argument("--name", default=DEFAULT_NAME, help="New database name (default: landguard_fresh_2026)")
    args = parser.parse_args()
    name = args.name.strip()
    if not re.fullmatch(r"[a-z][a-z0-9_]{2,40}", name):
        die("Database name must start with a lowercase letter and contain only a-z, 0-9 and _ (3-41 characters).")

    if not (ROOT / "backend" / "app" / "database.py").is_file():
        die("Place these setup files in the existing Smart_LandGuard_BD_2.0 project folder first.")
    if not ENV_PATH.is_file():
        die("backend/.env is missing. Restore it from your backup before creating a new database; do not regenerate encryption keys.")
    if not (ROOT / ".env").is_file():
        die("Root .env is missing. Restore the existing Docker configuration; do not reset the Docker volume.")

    try:
        from dotenv import dotenv_values
        import psycopg
        from psycopg import sql
        from psycopg.conninfo import conninfo_to_dict
    except ImportError as exc:
        die(f"Missing Python package {exc}. Run with backend\\.venv\\Scripts\\python.exe after pip install.")

    text = ENV_PATH.read_text(encoding="utf-8-sig")
    config = dotenv_values(ENV_PATH)
    current_url = (config.get("DATABASE_URL") or "").strip()
    if not current_url:
        die("DATABASE_URL is missing from backend/.env.")
    if (config.get("LANDGUARD_DATABASE_MODE") or "postgresql").strip().lower() != "postgresql":
        die("LANDGUARD_DATABASE_MODE must be postgresql.")
    for secret_key in ("LANDGUARD_SECRET_KEY", "LANDGUARD_FILE_ENCRYPTION_KEY"):
        if not (config.get(secret_key) or "").strip():
            die(f"{secret_key} is missing. Restore the original secret file first.")
    new_url = new_url_with_database(current_url, name)
    old_name = urlsplit(current_url).path.lstrip("/")
    if name == old_name:
        die("The requested new database name matches the current database. No changes made.")
    updated_text = substitute_url(text, new_url)

    # Connect to the existing server's maintenance database using the existing
    # app's credentials; the original PostgreSQL Docker role has CREATEDB.
    try:
        opts = conninfo_to_dict(current_url)
        opts.update(dbname="postgres", host="127.0.0.1", connect_timeout=7)
        with psycopg.connect(autocommit=True, **opts) as connection:
            exists = connection.execute("SELECT 1 FROM pg_database WHERE datname = %s", (name,)).fetchone()
            if exists:
                die(f"Database '{name}' already exists. Nothing was overwritten; choose another name.")
            connection.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    except psycopg.Error as exc:
        print("Database connection or CREATE DATABASE failed. Old database and configuration were not changed.", file=sys.stderr)
        # Never print connection strings or server exceptions that may contain credentials.
        die(f"PostgreSQL error class: {type(exc).__name__}. Check Docker health and database privileges.")

    print(f"OK: New PostgreSQL database created: {name}")
    print("Initializing tables and 12 clearly marked DEMO land records...")
    sys.path.insert(0, str(BACKEND))
    os.environ["LANDGUARD_DATABASE_MODE"] = "postgresql"
    os.environ["DATABASE_URL"] = new_url
    try:
        from app.database import initialize, connect
        from app.demo_registry import seed
        initialize()
        inserted = seed()
        with connect() as db:
            land_count = db.execute("SELECT COUNT(*) FROM land_records").fetchone()[0]
            users_count = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            table_count = db.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE'").fetchone()[0]
        if inserted != 12 or land_count != 12 or users_count != 0 or table_count < 10:
            die("New schema did not pass its checks. The old configuration was NOT changed.")
    except Exception as exc:
        die(f"Schema initialization failed ({type(exc).__name__}); old configuration untouched. Do not re-run with the same database name.")

    BACKUP_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    if os.name != "nt":
        os.chmod(BACKUP_DIR, 0o700)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    backup = BACKUP_DIR / f"backend_env_before_new_db_{timestamp}.bak"
    try:
        # Save old connection + existing session/file keys OUTSIDE the project tree.
        shutil.copy2(ENV_PATH, backup)
        if os.name != "nt":
            os.chmod(backup, 0o600)
        tmp = ENV_PATH.with_name(".env.newdb_tmp")
        try:
            tmp.write_text(updated_text, encoding="utf-8")
            os.replace(tmp, ENV_PATH)
        finally:
            if tmp.exists():
                tmp.unlink()
    except OSError as exc:
        die(f"Could not update backend/.env ({type(exc).__name__}). Old database was not deleted. Check permissions.")

    print(f"OK: New DB initialized: {table_count} tables, {land_count} demo land records, {users_count} users")
    print("OK: backend/.env now points to the NEW database")
    print("OK: Existing session secret and file encryption key preserved")
    print(f"OK: Previous backend/.env safely backed up outside project at: {backup}")
    print("OLD DATABASE NOT DELETED. Existing users remain in the OLD database.")
    print("NEXT: Stop/restart Flask, create a NEW admin account, start Vite frontend.")
    print("WARNING: DEMO DATA ONLY. This does not verify government land records.")


if __name__ == "__main__":
    main()
