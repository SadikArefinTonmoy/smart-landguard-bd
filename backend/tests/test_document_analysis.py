import unittest

from app.document_analysis import (
    analyze_document_for_evidence,
    compare_extracted_values,
    extract_property_fields,
    normalize_numeric_value,
)

from app.main import app


class DocumentAnalysisTests(unittest.TestCase):
    def test_decimal_normalization_handles_space_and_dot(self):
        self.assertEqual(normalize_numeric_value('1.26')[0], '1.26')
        self.assertEqual(normalize_numeric_value('1 26')[0], '1.26')
        self.assertEqual(normalize_numeric_value('1 26 bigha')[0], '1.26')

    def test_decimal_normalization_marks_ambiguous_values(self):
        normalized, ambiguous, reason = normalize_numeric_value('1 26', context='land_area')
        self.assertEqual(normalized, '1.26')
        self.assertTrue(ambiguous)
        self.assertIn('ambiguous', reason.lower())

    def test_compare_extracted_values_tracks_owner_name_and_ambiguous_land_area(self):
        user_input = {
            'propertyOwnerName': 'Rahman Ali',
            'mouza': 'Bharatpur',
            'khatianNumber': 'K-221/445',
            'dagNumber': 'Dag 18',
            'landArea': '1.26',
        }
        extracted_fields = {
            'owner_name': 'Rahman Ali',
            'mouza': 'Bharatpur',
            'khatian_number': 'K-221/445',
            'dag_number': 'Dag 18',
            'land_area': '1 26 Bigha',
        }

        result = compare_extracted_values(user_input, extracted_fields)
        self.assertIn('matched', result)
        self.assertIn('ambiguous', result)
        self.assertIn('owner_name', [item['field'] for item in result['matched']])
        self.assertTrue(any(item['field'] == 'land_area' for item in result['ambiguous']))

    def test_missing_owner_name_is_reported(self):
        text = 'Mouza: Bharatpur\nKhatian Number: K-221/445\nDag Number: Dag 18\nLand Area: 1.62 bigha'
        extracted = extract_property_fields(text)
        self.assertIsNone(extracted['owner_name'])

    def test_unsupported_file_type_is_reported(self):
        analysis = analyze_document_for_evidence({}, 'sample.xyz', b'garbage')
        self.assertEqual(analysis['status'], 'unreadable')
        self.assertIn('Unsupported', analysis['message'])

    def test_mismatch_is_reported_for_different_owner_name(self):
        user_input = {'propertyOwnerName': 'Rahman Ali', 'mouza': '', 'khatianNumber': '', 'dagNumber': '', 'landArea': ''}
        extracted_fields = {'owner_name': 'Karim Mia'}
        result = compare_extracted_values(user_input, extracted_fields)
        self.assertTrue(any(item['field'] == 'owner_name' for item in result['mismatched']))

    def test_risk_report_marks_demo_data(self):
        client = app.test_client()
        response = client.get('/api/reports/LG-1001')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('Sample / Demo Data', data['status'])


if __name__ == '__main__':
    unittest.main()
