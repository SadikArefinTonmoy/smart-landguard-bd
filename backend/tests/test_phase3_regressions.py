"""Phase 3 conservative-data regression tests.

Run after configuring a local-only test database:
  set LANDGUARD_DATABASE_MODE=sqlite
  python -m unittest discover -s tests -v
These tests use a temporary SQLite database and never access your PostgreSQL data.
"""
import os
import tempfile
import unittest
import uuid
from pathlib import Path
from pypdf import PdfReader
from app.document_analysis import extract_property_fields, compare_extracted_values
from app.database import connect, initialize, utcnow
from app.demo_registry import seed, check_record
from app.crud import get_dashboard_summary


class Phase3Regressions(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.before = {name: os.environ.get(name) for name in ('LANDGUARD_DATABASE_MODE', 'LANDGUARD_DB_PATH')}
        os.environ['LANDGUARD_DATABASE_MODE'] = 'sqlite'
        os.environ['LANDGUARD_DB_PATH'] = os.path.join(self.tmp.name, 'test.sqlite3')
        initialize()
        self.user = str(uuid.uuid4())
        with connect() as db:
            db.execute('INSERT INTO users(id,email,name,role,password_hash,created_at,updated_at) VALUES (?,?,?,?,?,?,?)',
                       (self.user, 'phase3@example.test', 'Test Account', 'buyer', 'test-only-no-login', utcnow(), utcnow()))

    def tearDown(self):
        for name, value in self.before.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
        self.tmp.cleanup()

    def test_sample_pdf_keeps_decimal_and_survey_id(self):
        pdf_path = Path(__file__).resolve().parents[2] / 'DEMO LAND DOCUMENT.pdf'
        extracted = extract_property_fields(PdfReader(str(pdf_path)).pages[0].extract_text())
        self.assertEqual(extracted['land_area'], '1.26 Bigha')
        self.assertEqual(extracted['khatian_number'], 'K-221/445')
        result = compare_extracted_values({
            'propertyOwnerName': '', 'mouza': 'Bharatpur', 'khatianNumber': 'K-221/445',
            'dagNumber': 'Dag 18', 'landArea': '1.26 Bigha'}, extracted)
        self.assertFalse(result['ambiguous'])
        self.assertEqual(len(result['matched']), 4)

    def test_bangla_labels_do_not_match_different_people(self):
        extracted = extract_property_fields('মালিকের নাম: রহিম\nমৌজা: কলাবাগান\nদাগ নং: ১২৩')
        self.assertEqual(extracted['owner_name'], 'রহিম')
        result = compare_extracted_values({'propertyOwnerName': 'করিম'}, extracted)
        self.assertEqual([v['field'] for v in result['mismatched']], ['owner_name'])

    def test_incomplete_demo_registry_input_is_not_complete_match(self):
        self.assertEqual(seed(), 12)
        r = check_record(self.user, 'DEMO-LR-1001', 'own_records',
                         {'owner_name':'Demo Owner Alpha'})
        self.assertEqual(r['result'], 'incomplete_demo_check')
        self.assertEqual(len(r['unprovided_fields']), 5)
        m = check_record(self.user, 'DEMO-LR-1001', 'own_records',
                         {'owner_name':'Demo Owner XYZ'})
        self.assertEqual(m['result'], 'demo_mismatch')
        valid = {'owner_name':'Demo Owner Alpha', 'district':'Dhaka', 'mouza':'Sample Mouza A',
                 'khatian':'DEMO-KH-101','dag':'DEMO-DAG-01','land_area':'5 decimal'}
        good = check_record(self.user, 'DEMO-LR-1001','own_records',valid)
        self.assertEqual(good['result'],'demo_match')
        self.assertFalse(good['government_verification_performed'])

    def test_dashboard_shows_actual_counts_not_invented(self):
        empty = get_dashboard_summary(self.user)
        self.assertEqual(empty['verification_requests'], 0)
        self.assertEqual(empty['completed_checks'], 0)
        seed()
        check_record(self.user,'DEMO-LR-1001','own_records',{'owner_name':'Demo Owner XYZ'})
        with connect() as db:
            db.execute('''INSERT INTO verification_events(id,user_id,purpose,authority_attested,input_file_count,evidence_status,created_at)
                          VALUES (?,?,?,?,?,?,?)''', (str(uuid.uuid4()),self.user,'own_records',1,1,'unreadable',utcnow()))
        data=get_dashboard_summary(self.user)
        self.assertEqual(data['verification_requests'],2)
        self.assertEqual(data['completed_checks'],1)
        self.assertEqual(data['pending_checks'],1)
        self.assertEqual(data['unresolved_issues'],2)


if __name__ == '__main__':
    unittest.main()
