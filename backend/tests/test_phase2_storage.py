"""SQLite-backed behavioural tests for PostgreSQL-compatible phase-2 data layer.

These tests do not substitute for a real PostgreSQL/browser penetration test.
"""
import os
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch
from cryptography.fernet import Fernet
from app.database import initialize, connect, utcnow
from app.demo_registry import seed, list_records, check_record
from app import private_vault

class Phase2DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.env=patch.dict(os.environ,{
            'LANDGUARD_DATABASE_MODE':'sqlite',
            'LANDGUARD_DB_PATH':str(Path(self.tmp.name)/'unit.sqlite3'),
            'LANDGUARD_FILE_ENCRYPTION_KEY':Fernet.generate_key().decode(),
        })
        self.env.start()
        self.vault_patch=patch.object(private_vault,'DIR',Path(self.tmp.name)/'encrypted')
        self.vault_patch.start()
        initialize()
        self.alice=str(uuid.uuid4())
        self.bob=str(uuid.uuid4())
        self.admin=str(uuid.uuid4())
        with connect() as db:
            for uid,name,role in ((self.alice,'alice','buyer'),(self.bob,'bob','seller'),(self.admin,'admin','admin')):
                db.execute('INSERT INTO users(id,email,name,role,password_hash,created_at,updated_at) VALUES (?,?,?,?,?,?,?)',
                           (uid,name+'@example.test',name,role,'hashed',utcnow(),utcnow()))

    def tearDown(self):
        self.vault_patch.stop()
        self.env.stop()
        self.tmp.cleanup()

    def test_seed_fictional_and_no_official_match(self):
        self.assertEqual(seed(),12)
        self.assertEqual(seed(),0)
        self.assertEqual(len(list_records('Demo Owner')),12)
        sample=list_records('DEMO-LR-1001')[0]
        good=check_record(self.alice,sample['id'],'own_records',{'owner_name':sample['owner_name']})
        self.assertEqual(good['result'],'demo_match')
        self.assertFalse(good['government_verification_performed'])
        wrong=check_record(self.bob,sample['id'],'own_records',{'owner_name':'Not same name'})
        self.assertEqual(wrong['result'],'demo_mismatch')
        with connect() as db:
            alice_checks=db.execute('SELECT COUNT(*) FROM registry_checks WHERE user_id=?',(self.alice,)).fetchone()[0]
        self.assertEqual(alice_checks,1)

    def test_share_revoke_and_expire_permissions(self):
        from datetime import datetime, timedelta, timezone
        identifier=private_vault.store(self.alice,'sample.pdf',b'%PDF-1.4\nSample')
        expiration=(datetime.now(timezone.utc)+timedelta(hours=24)).isoformat(timespec='seconds')
        gid=str(uuid.uuid4())
        with connect() as db:
            db.execute('''INSERT INTO document_grants(id,document_id,grantee_user_id,granted_by,purpose,expires_at,created_at)
                       VALUES (?,?,?,?,?,?,?)''',(gid,identifier,self.bob,self.alice,'purchase_due_diligence',expiration,utcnow()))
        self.assertIsNotNone(private_vault.accessible(self.bob,identifier))
        self.assertIsNone(private_vault.accessible(self.admin,identifier))
        with connect() as db:
            db.execute('UPDATE document_grants SET revoked_at=? WHERE id=?',(utcnow(),gid))
        self.assertIsNone(private_vault.accessible(self.bob,identifier))
        with connect() as db:
            db.execute('UPDATE document_grants SET revoked_at=NULL,expires_at=? WHERE id=?',('2020-01-01T00:00:00+00:00',gid))
        self.assertIsNone(private_vault.accessible(self.bob,identifier))

    def test_file_ciphertext_owner_permissions_and_deletion(self):
        identifier=private_vault.store(self.alice,'sample.pdf',b'%PDF-1.4\nFictional sample')
        self.assertIsNotNone(private_vault.accessible(self.alice,identifier))
        self.assertIsNone(private_vault.accessible(self.bob,identifier))
        self.assertIsNone(private_vault.accessible(self.admin,identifier))
        owner_item=private_vault.accessible(self.alice,identifier)
        self.assertEqual(private_vault.read_file(owner_item),b'%PDF-1.4\nFictional sample')
        saved=list(private_vault.DIR.iterdir())[0].read_bytes()
        self.assertNotIn(b'Fictional sample',saved)
        self.assertFalse(private_vault.delete_own(self.bob,identifier))
        self.assertTrue(private_vault.delete_own(self.alice,identifier))
        self.assertIsNone(private_vault.accessible(self.alice,identifier))
        self.assertEqual(list(private_vault.DIR.iterdir()),[])

if __name__=='__main__': unittest.main()
