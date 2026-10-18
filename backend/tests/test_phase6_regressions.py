"""Phase 6 source safety and isolated SQLite demo-registry compatibility checks.

Runs without a PostgreSQL instance and never touches production user records.
Run: cd backend && python -m unittest discover -s tests -p test_phase6_regressions.py -v
"""
import os
import tempfile
import unittest
import uuid
from pathlib import Path

from app.database import connect, initialize, utcnow
from app.demo_registry import check_record, list_records, seed

ROOT = Path(__file__).resolve().parents[2]

class Phase6Checks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.previous = {v: os.environ.get(v) for v in ['LANDGUARD_DATABASE_MODE', 'LANDGUARD_DB_PATH']}
        os.environ['LANDGUARD_DATABASE_MODE'] = 'sqlite'
        os.environ['LANDGUARD_DB_PATH'] = os.path.join(self.temp.name, 'isolated.sqlite3')
        initialize()
        self.user = str(uuid.uuid4())
        with connect() as db:
            db.execute('INSERT INTO users(id,email,name,role,password_hash,created_at,updated_at) VALUES (?,?,?,?,?,?,?)',
                       (self.user, 'phase6@example.test', 'Test', 'admin', 'hash-not-for-login', utcnow(), utcnow()))

    def tearDown(self):
        for key,value in self.previous.items():
            if value is None: os.environ.pop(key, None)
            else: os.environ[key] = value
        self.temp.cleanup()

    def test_fresh_schema_and_synthetic_land_rows(self):
        self.assertEqual(seed(), 12)
        self.assertEqual(seed(), 0)
        self.assertEqual(len(list_records()), 12)
        with connect() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM users').fetchone()[0], 1)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM private_documents').fetchone()[0], 0)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM land_records WHERE is_demo=1').fetchone()[0], 12)

    def test_comparison_requires_real_evidence_for_mismatch(self):
        seed()
        val=check_record(self.user, 'DEMO-LR-1001', 'own_records', {'owner_name':'Demo Owner Alpha'})
        self.assertEqual(val['result'],'incomplete_demo_check')
        self.assertFalse(val['government_verification_performed'])
        val=check_record(self.user, 'DEMO-LR-1001','own_records',{'owner_name':'Not Alpha'})
        self.assertEqual(val['result'],'demo_mismatch')

    def test_navigation_and_search_result_placement(self):
        source=(ROOT/'frontend/src/App.tsx').read_text(encoding='utf8')
        css=(ROOT/'frontend/src/index.css').read_text(encoding='utf8')
        self.assertNotIn("['demo-registry', 'Demo Registry', 'ডেমো রেজিস্ট্রি']",source)
        self.assertNotIn('Document review, in one place',source)
        self.assertIn('.nav a::after { display: none !important',css)
        self.assertLess(source.index('id="search"'),source.index('id="reports"'))
        self.assertLess(source.index('id="reports"'),source.index('id="verification"'))
        self.assertIn('translateVerificationMessage(item, language)',source)
        self.assertIn('setShowAllAdminRecords',source)
        self.assertIn('resetAdminRecord(false)',source)
        self.assertIn('resetDemoComparison',source)
        self.assertIn('registry.slice(0, showAllAdminRecords ? registry.length : 4)',source)
        self.assertNotIn("text(item, 'প্রকৃত সিদ্ধান্তের আগে সংশ্লিষ্ট সরকারি কর্তৃপক্ষের রেকর্ড ও যোগ্য পেশাজীবীর সঙ্গে যাচাই করুন।')", source[source.index('verificationStep === 4 && verificationResult'):source.index('id="dashboard"')])

if __name__ == '__main__':unittest.main()
