"""Phase 4 login regression; always isolates tests from the Docker PostgreSQL DB.

Run with installed backend dependencies, from backend directory:
    python -m unittest discover -s tests -p test_phase4_login.py -v
"""
import os
import tempfile
import unittest
import uuid

# Set SQLite before the Flask app is imported. Never use the real PG database.
os.environ['LANDGUARD_DATABASE_MODE'] = 'sqlite'
from app.auth import ph
from app.database import connect, initialize, utcnow
from app.main import app


class Phase4LoginTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_path = os.environ.get('LANDGUARD_DB_PATH')
        os.environ['LANDGUARD_DB_PATH'] = os.path.join(self.tmp.name, 'test.sqlite3')
        initialize()
        self.client = app.test_client()
        with connect() as db:
            for email in ('account-a@example.test', 'account-b@example.test'):
                db.execute('''INSERT INTO users(id,email,name,role,password_hash,created_at,updated_at)
                    VALUES (?,?,?,?,?,?,?)''', (str(uuid.uuid4()), email, 'Demo tester',
                                                'buyer', ph.hash('CorrectPassword123!'), utcnow(), utcnow()))

    def tearDown(self):
        if self.old_path is None:
            os.environ.pop('LANDGUARD_DB_PATH', None)
        else:
            os.environ['LANDGUARD_DB_PATH'] = self.old_path
        self.tmp.cleanup()

    def login(self, email, password):
        token = self.client.get('/api/auth/csrf').get_json()['csrf_token']
        return self.client.post('/api/auth/login', json={'email':email,'password':password},
                                headers={'X-CSRF-Token':token, 'Origin':'http://localhost:4173'})

    def test_same_ip_different_account_not_locked_at_five(self):
        for _ in range(5):
            response = self.login('account-a@example.test', 'WrongPassword')
            self.assertEqual(response.status_code, 401)
        blocked = self.login('account-a@example.test', 'CorrectPassword123!')
        self.assertEqual(blocked.status_code, 429)
        self.assertGreater(int(blocked.headers['Retry-After']), 0)
        self.assertGreater(blocked.get_json()['retry_after_seconds'], 0)
        allowed = self.login('account-b@example.test', 'CorrectPassword123!')
        self.assertEqual(allowed.status_code, 200, allowed.get_json())

    def test_successful_login_and_logout_work(self):
        response = self.login('account-a@example.test', 'CorrectPassword123!')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get('/api/auth/me').status_code, 200)
        token = self.client.get('/api/auth/csrf').get_json()['csrf_token']
        response = self.client.post('/api/auth/logout', headers={'X-CSRF-Token': token, 'Origin':'http://localhost:4173'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get('/api/auth/me').status_code, 401)

if __name__ == '__main__':
    unittest.main()
