"""Run after 'pip install -r requirements.txt': python -m unittest discover -s tests -v"""
import io
import os
import tempfile
import unittest
import uuid

from app.auth import ph
from app.database import connect, initialize, utcnow
from app.document_analysis import is_field_match, normalize_value
from app.main import app


class SecurityPhase1Tests(unittest.TestCase):
    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory()
        self.old_db = os.environ.get('LANDGUARD_DB_PATH')
        os.environ['LANDGUARD_DB_PATH'] = os.path.join(self.workspace.name, 'test.sqlite3')
        initialize()
        self.client = app.test_client()
        self.user_email = 'security-test@example.com'
        with connect() as db:
            db.execute('INSERT INTO users(id,email,name,role,password_hash,created_at,updated_at) VALUES (?,?,?,?,?,?,?)',
                       (str(uuid.uuid4()), self.user_email, 'Security tester', 'buyer', ph.hash('test-password-12345'), utcnow(), utcnow()))

    def tearDown(self):
        if self.old_db is None:
            os.environ.pop('LANDGUARD_DB_PATH', None)
        else:
            os.environ['LANDGUARD_DB_PATH'] = self.old_db
        self.workspace.cleanup()

    def _csrf(self):
        res = self.client.get('/api/auth/csrf')
        self.assertEqual(res.status_code, 200)
        return res.get_json()['csrf_token']

    def _login(self):
        res = self.client.post('/api/auth/login', json={'email': self.user_email, 'password': 'test-password-12345'},
                               headers={'X-CSRF-Token': self._csrf(), 'Origin': 'http://localhost:4173'})
        self.assertEqual(res.status_code, 200, res.get_json())
        return res

    def test_unauthenticated_admin_and_upload_are_rejected(self):
        self.assertEqual(self.client.get('/api/moderation').status_code, 401)
        self.assertEqual(self.client.post('/api/verification/extract', headers={'X-CSRF-Token': self._csrf()}).status_code, 401)

    def test_csrf_login_and_role_enforcement(self):
        self.assertEqual(self.client.post('/api/auth/login', json={'email': self.user_email, 'password': 'test-password-12345'}).status_code, 403)
        self._login()
        self.assertEqual(self.client.get('/api/auth/me').status_code, 200)
        self.assertEqual(self.client.get('/api/moderation').status_code, 403)
        self.assertEqual(self.client.get('/api/privacy/me').status_code, 200)

    def test_logout_revokes_session(self):
        self._login()
        self.assertEqual(self.client.post('/api/auth/logout', headers={'X-CSRF-Token': self._csrf()}).status_code, 200)
        self.assertEqual(self.client.get('/api/auth/me').status_code, 401)

    def test_upload_needs_attestation_and_has_no_official_flag(self):
        self._login()
        payload = {'purpose': 'purchase_due_diligence', 'documents': (io.BytesIO(b'%PDF-\ngarbage'), 'sample.pdf')}
        self.assertEqual(self.client.post('/api/verification/extract', data=payload, headers={'X-CSRF-Token': self._csrf()}).status_code, 403)
        res = self.client.post('/api/verification/extract', data={
            'purpose': 'purchase_due_diligence', 'authorityAttested': 'true',
            'documents': (io.BytesIO(b'fake file'), 'sample.pdf')
        }, headers={'X-CSRF-Token': self._csrf()})
        self.assertEqual(res.status_code, 400)
        self.assertFalse(self.client.get('/api/official/status').get_json()['connected'])

    def test_bengali_names_and_prefixes_do_not_false_match(self):
        self.assertFalse(is_field_match('রহিম', 'করিম'))
        self.assertFalse(is_field_match('Rahim', 'Rahima'))
        self.assertFalse(is_field_match('Dag 18', 'Dag 18 Land'))
        self.assertTrue(is_field_match('রহিম উদ্দিন', 'রহিম  উদ্দিন'))
        self.assertEqual(normalize_value('দাগ ১২'), 'দাগ 12')


if __name__ == '__main__':
    unittest.main()
