"""Encrypted, owner-scoped test-file vault. No public URLs and no demo credentials."""
import hashlib
import os
import re
import uuid
from pathlib import Path
from cryptography.fernet import Fernet
from app.database import BASE_DIR, connect, utcnow

DIR = BASE_DIR / 'instance' / 'encrypted_documents'
MIME = {'.pdf':'application/pdf', '.docx':'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.png':'image/png', '.jpg':'image/jpeg', '.jpeg':'image/jpeg'}

def cipher():
    raw = os.getenv('LANDGUARD_FILE_ENCRYPTION_KEY','').strip()
    if not raw:
        raise RuntimeError('Set LANDGUARD_FILE_ENCRYPTION_KEY in backend/.env before storing demo files.')
    try:
        return Fernet(raw.encode('ascii'))
    except (ValueError, TypeError) as exc:
        raise RuntimeError('Invalid LANDGUARD_FILE_ENCRYPTION_KEY. Generate a new Fernet key.') from exc

def store(user_id, name, data):
    DIR.mkdir(parents=True, exist_ok=True)
    safe_name = Path(name).name[:120]
    storage = f'{uuid.uuid4().hex}.encrypted'
    location = DIR / storage
    encrypted = cipher().encrypt(data)
    try:
        # Atomic create; no externally readable URLs.
        with location.open('xb') as handle:
            handle.write(encrypted)
        if os.name != 'nt':
            os.chmod(location, 0o600)
        file_id = str(uuid.uuid4())
        extension = Path(safe_name).suffix.lower()
        with connect() as db:
            db.execute('''INSERT INTO private_documents(id,owner_user_id,original_filename,mime_type,byte_count,storage_name,sha256_hash,created_at)
                          VALUES (?,?,?,?,?,?,?,?)''', (file_id,user_id,safe_name,MIME[extension],len(data),storage,hashlib.sha256(data).hexdigest(),utcnow()))
        return file_id
    except Exception:
        location.unlink(missing_ok=True)
        raise

def accessible(user_id, file_id):
    with connect() as db:
        row = db.execute('''SELECT d.* FROM private_documents d WHERE d.id=? AND
          (d.owner_user_id=? OR EXISTS
            (SELECT 1 FROM document_grants g WHERE g.document_id=d.id AND g.grantee_user_id=?
              AND g.revoked_at IS NULL AND g.expires_at > ?))''', (file_id,user_id,user_id,utcnow())).fetchone()
    return dict(row) if row else None

def read_file(item):
    # Location derived from server-generated storage identifier, never the client.
    storage = str(item['storage_name'])
    if not re.fullmatch(r'[a-f0-9]{32}\.encrypted', storage):
        raise ValueError('Unsafe storage identifier')
    return cipher().decrypt((DIR / storage).read_bytes())

def delete_own(user_id, file_id):
    with connect() as db:
        row = db.execute('SELECT storage_name FROM private_documents WHERE id=? AND owner_user_id=?',(file_id,user_id)).fetchone()
        if not row:
            return False
        db.execute('DELETE FROM private_documents WHERE id=? AND owner_user_id=?',(file_id,user_id))
    (DIR / str(row['storage_name'])).unlink(missing_ok=True)
    return True
