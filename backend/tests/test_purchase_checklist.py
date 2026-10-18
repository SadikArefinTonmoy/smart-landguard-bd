import unittest

from app.main import app


class PurchaseChecklistAPITest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_purchase_checklist_route_returns_steps(self):
        response = self.client.get('/api/properties/LG-1001/purchase-checklist')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('property_id', data)
        self.assertIn('checklist', data)
        self.assertTrue(len(data['checklist']) >= 3)
        self.assertEqual(data['property_id'], 'LG-1001')


if __name__ == '__main__':
    unittest.main()
