import unittest

from app.main import app


class ModerationQueueAPITest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_moderation_queue_requires_login(self):
        response = self.client.get('/api/moderation')
        self.assertEqual(response.status_code, 401)


if __name__ == '__main__':
    unittest.main()
