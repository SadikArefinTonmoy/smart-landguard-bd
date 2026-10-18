"""Run locally: from backend, LANDGUARD_DATABASE_MODE=sqlite python -m unittest discover -s tests -p test_phase5_guest_auth.py -v
Test database is isolated in temporary SQLite, never touches actual Docker volume.
"""
import os
import tempfile
import unittest
import uuid

os.environ['LANDGUARD_DATABASE_MODE'] = 'sqlite'

from app.auth import ph
from app.database import connect, initialize, utcnow
from app.main import app


class GuestAndLoginTests(unittest.TestCase):
    def setUp(self):
        self._old_db = os.environ.get('LANDGUARD_DB_PATH')
        self._temp = tempfile.TemporaryDirectory()
        os.environ['LANDGUARD_DB_PATH'] = os.path.join(self._temp.name, 'phase5.sqlite3')
        initialize()
        self.client = app.test_client()
        with connect() as db:
            db.execute(
                'INSERT INTO users(id,email,name,role,password_hash,created_at,updated_at) VALUES (?,?,?,?,?,?,?)',
                (str(uuid.uuid4()), 'admin@example.test', 'Demo Admin', 'admin', ph.hash('StrongUniquePass42!'), utcnow(), utcnow())
            )

    def tearDown(self):
        if self._old_db is None:
            os.environ.pop('LANDGUARD_DB_PATH', None)
        else:
            os.environ['LANDGUARD_DB_PATH'] = self._old_db
        self._temp.cleanup()

    def _csrf(self):
        response = self.client.get('/api/auth/csrf')
        self.assertEqual(response.status_code, 200)
        return response.json['csrf_token']

    def test_guest_can_only_access_public_endpoints(self):
        self.assertEqual(self.client.get('/api/health').status_code, 200)
        for path in ('/api/properties', '/api/properties/DEMO-1001',
                     '/api/properties/DEMO-1001/purchase-checklist',
                     '/api/reports/DEMO-1001', '/api/dashboard',
                     '/api/demo-registry', '/api/documents'):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 401)

    def test_correct_credentials_work_and_logout_revokes_session(self):
        token = self._csrf()
        wrong = self.client.post('/api/auth/login', json={
            'email':'admin@example.test', 'password':'wrong'},
            headers={'X-CSRF-Token':token, 'Origin':'http://localhost:4173'})
        self.assertEqual(wrong.status_code, 401)
        good = self.client.post('/api/auth/login', json={
            'email':'ADMIN@example.test', 'password':'StrongUniquePass42!'},
            headers={'X-CSRF-Token':self._csrf(), 'Origin':'http://localhost:4173'})
        self.assertEqual(good.status_code, 200, good.get_json())
        self.assertEqual(good.json['user_role'], 'admin')
        self.assertEqual(self.client.get('/api/auth/me').status_code, 200)
        self.assertEqual(self.client.get('/api/properties').status_code, 200)
        logout=self.client.post('/api/auth/logout', headers={
            'X-CSRF-Token':self._csrf(), 'Origin':'http://localhost:4173'})
        self.assertEqual(logout.status_code, 200)
        self.assertEqual(self.client.get('/api/properties').status_code, 401)

    def test_no_csrf_denies_login(self):
        self.assertEqual(self.client.post('/api/auth/login', json={
            'email':'admin@example.test', 'password':'StrongUniquePass42!'}).status_code, 403)

if __name__ == '__main__': unittest.main()
