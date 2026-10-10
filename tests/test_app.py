import http.client
import json
import threading
import unittest
from http.server import HTTPServer
from api.evaluate import handler, load_knowledge_base, validate_patient
from src.evaluate import _eval, diagnose, evaluate


class ApplicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(('127.0.0.1', 0), handler)
        cls.worker = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.worker.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.worker.join()

    def request(self, body, method='POST', content_type='application/json'):
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port)
        connection.request(method, '/api/evaluate', body, {'Content-Type': content_type})
        response = connection.getresponse()
        status, data = response.status, json.loads(response.read())
        self.assertEqual(response.getheader('Cache-Control'), 'no-store')
        connection.close()
        return status, data

    def test_valid_patient(self):
        status, data = self.request(json.dumps({'patient': {'diabetes_type': 'type2', 'age': 62, 'a1c': 8.9, 'egfr': 42, 'uacr': 420, 'ascvd': True}}))
        self.assertEqual(status, 200)
        self.assertEqual(data['derived']['ckd']['stage'], 'G3bA3')
        self.assertTrue(data['prescription_instructions'])

    def test_malformed_inputs(self):
        for body in ('{', '[]', '{}', '{"patient":{}}', '{"patient":{"age":"62"}}', '{"patient":{"ascvd":"false"}}', '{"patient":{"a1c":NaN}}', '{"patient":{"age":-1}}', '{"patient":{"diabetes_type":"typo"}}', '{"patient":{"name":"patient"}}'):
            with self.subTest(body=body):
                self.assertEqual(self.request(body)[0], 400)

    def test_methods_and_media_type(self):
        self.assertEqual(self.request('', 'GET')[0], 405)
        self.assertEqual(self.request('{}', content_type='text/plain')[0], 415)
        self.assertEqual(self.request('x' * 1048577)[0], 413)

    def test_no_measurements(self):
        self.assertEqual(diagnose({})['status'], 'insufficient_data')

    def test_field_specific_not_none(self):
        node = {'field': 'retinopathy_stage', 'op': '!=', 'value': 'none'}
        self.assertFalse(_eval(node, {'diabetes_type': 'type2'}))
        self.assertTrue(_eval(node, {'retinopathy_stage': 'pdr'}))

    def test_aliases_and_nulls(self):
        kb = load_knowledge_base()
        result = evaluate({'diabetes_type': 'unknown', 'fasting_glucose': 130, 'a1c': None}, kb)
        self.assertEqual(result['derived']['diagnosis']['status'], 'probable_diabetes_needs_confirmation')
        result = evaluate({'on_acei': True}, kb)
        self.assertTrue(any('swelling of lips/face' in text for text in result['prescription_instructions']))

    def test_schema_and_rule_integrity(self):
        kb = load_knowledge_base()
        ids = {item['id'] for item in kb['instructions']}
        for rule in kb['rules']:
            self.assertTrue(set(rule.get('instructions', [])) <= ids)
        validate_patient({field['field']: None for field in kb['patient_fields']} | {'age': 62}, kb)


if __name__ == '__main__':
    unittest.main()
