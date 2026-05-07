\"\"\"筛选系统API集成测试\"\"\"

import unittest
import json
from flask import Flask
from screening.routes import create_screening_blueprint


class TestScreeningAPI(unittest.TestCase):
    \"\"\"筛选系统API端点集成测试\"\"\"
    
    @classmethod
    def setUpClass(cls):
        \"\"\"设置测试客户端\"\"\"
        cls.app = Flask(__name__)
        cls.app.register_blueprint(create_screening_blueprint())
        cls.app.config['TESTING'] = True
        cls.client = cls.app.test_client()
    
    def test_standardize_symptoms_endpoint(self):
        \"\"\"测试症状标准化端点\"\"\"
        response = self.client.post(
            '/api/screening/symptoms/standardize',
            data=json.dumps({'symptoms': ['头疼', '发烧']}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertIn('standardized_symptoms', data['data'])
    
    def test_get_synonyms_endpoint(self):
        \"\"\"测试获取同义词端点\"\"\"
        response = self.client.get(
            '/api/screening/symptoms/synonyms?symptom_name=头痛'
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertIn('synonyms', data['data'])
    
    def test_screening_query_endpoint(self):
        \"\"\"测试筛选查询端点\"\"\"
        response = self.client.post(
            '/api/screening/query',
            data=json.dumps({
                'symptoms': ['头痛', '发热'],
                'patient_info': {'age': 35},
                'filters': {'max_results': 10}
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertIn('results', data)
    
    def test_batch_screening_endpoint(self):
        \"\"\"测试批量筛选端点\"\"\"
        response = self.client.post(
            '/api/screening/batch',
            data=json.dumps({
                'queries': [
                    {'symptoms': ['头痛']},
                    {'symptoms': ['腹泻']}
                ]
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['total_queries'], 2)
    
    def test_get_config_endpoint(self):
        \"\"\"测试获取配置端点\"\"\"
        response = self.client.get('/api/screening/config')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertIn('config', data['data'])
    
    def test_update_config_endpoint(self):
        \"\"\"测试更新配置端点\"\"\"
        response = self.client.put(
            '/api/screening/config',
            data=json.dumps({
                'config_name': 'default',
                'max_results': 25
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
    
    def test_get_history_endpoint(self):
        \"\"\"测试获取历史端点\"\"\"
        response = self.client.get(
            '/api/screening/history?user_id=1&limit=10'
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
    
    def test_get_status_endpoint(self):
        \"\"\"测试获取状态端点\"\"\"
        response = self.client.get('/api/screening/status')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['service_name'], 'ScreeningService')


if __name__ == '__main__':
    unittest.main()
