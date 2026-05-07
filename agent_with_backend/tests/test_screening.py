\"\"\"筛选系统单元测试\"\"\"

import unittest
import json
from datetime import datetime, timedelta
from screening.services import (
    SymptomService,
    ScreeningService,
    ConfigService,
    HistoryService,
)


class TestSymptomService(unittest.TestCase):
    \"\"\"症状服务测试\"\"\"
    
    def setUp(self):
        self.service = SymptomService()
    
    def test_standardize_symptom_exact_match(self):
        \"\"\"测试精确匹配\"\"\"
        result = self.service.standardize_symptom('头疼')
        self.assertEqual(result, '头痛')
    
    def test_standardize_symptom_no_match(self):
        \"\"\"测试无匹配\"\"\"
        result = self.service.standardize_symptom('未知症状')
        self.assertIsNone(result)
    
    def test_standardize_symptoms(self):
        \"\"\"测试多症状标准化\"\"\"
        result = self.service.standardize_symptoms(['头疼', '发烧', '咳嗽'])
        self.assertTrue(result['confidence'] > 0)
        self.assertIn('头痛', result['standardized_symptoms'])
        self.assertEqual(result['matched_count'], 3)
    
    def test_get_synonyms(self):
        \"\"\"测试获取同义词\"\"\"
        synonyms = self.service.get_synonyms('头痛')
        self.assertIn('头疼', synonyms)
        self.assertIn('头痛', synonyms)
    
    def test_calculate_symptom_similarity(self):
        \"\"\"测试相似度计算\"\"\"
        similarity = self.service.calculate_symptom_similarity('头痛', '头疼')
        self.assertGreater(similarity, 0.7)


class TestScreeningService(unittest.TestCase):
    \"\"\"筛选服务测试\"\"\"
    
    def setUp(self):
        self.symptom_service = SymptomService()
        self.service = ScreeningService(self.symptom_service)
    
    def test_screening_query_success(self):
        \"\"\"测试成功筛选\"\"\"
        result = self.service.screening_query(['头痛', '发热'])
        self.assertTrue(result['success'])
        self.assertGreater(result['total_count'], 0)
        self.assertIn('results', result)
    
    def test_screening_query_empty_symptoms(self):
        \"\"\"测试空症状列表\"\"\"
        result = self.service.screening_query([])
        self.assertFalse(result['success'])
    
    def test_screening_query_with_filters(self):
        \"\"\"测试带筛选条件的查询\"\"\"
        filters = {
            'price_range': [0, 10],
            'max_results': 5
        }
        result = self.service.screening_query(['头痛'], filters=filters)
        self.assertTrue(result['success'])
        self.assertLessEqual(result['total_count'], 5)
    
    def test_batch_screening(self):
        \"\"\"测试批量筛选\"\"\"
        queries = [
            {'symptoms': ['头痛']},
            {'symptoms': ['腹泻']},
        ]
        result = self.service.batch_screening(queries)
        self.assertEqual(result['total_queries'], 2)
        self.assertEqual(result['successful_queries'], 2)


class TestConfigService(unittest.TestCase):
    \"\"\"配置服务测试\"\"\"
    
    def setUp(self):
        self.service = ConfigService()
    
    def test_get_default_config(self):
        \"\"\"测试获取默认配置\"\"\"
        config = self.service.get_config('default')
        self.assertIsNotNone(config)
        self.assertEqual(config['config_name'], 'default')
    
    def test_get_active_config(self):
        \"\"\"测试获取活跃配置\"\"\"
        config = self.service.get_active_config()
        self.assertIsNotNone(config)
        self.assertTrue(config['is_active'])
    
    def test_create_config(self):
        \"\"\"测试创建配置\"\"\"
        config_data = {
            'config_name': 'test_config',
            'description': '测试配置',
            'confidence_threshold': 0.6
        }
        result = self.service.create_config(config_data)
        self.assertTrue(result['success'])
    
    def test_update_config(self):
        \"\"\"测试更新配置\"\"\"
        # 先创建配置
        self.service.create_config({'config_name': 'update_test'})
        
        # 更新配置
        result = self.service.update_config(
            'update_test',
            {'confidence_threshold': 0.7}
        )
        self.assertTrue(result['success'])
        self.assertEqual(
            result['config']['confidence_threshold'],
            0.7
        )
    
    def test_validate_confidence_threshold(self):
        \"\"\"测试置信度阈值验证\"\"\"
        result = self.service._validate_config_fields({
            'confidence_threshold': 1.5
        })
        self.assertFalse(result['valid'])


class TestHistoryService(unittest.TestCase):
    \"\"\"历史服务测试\"\"\"
    
    def setUp(self):
        self.service = HistoryService()
    
    def test_save_history(self):
        \"\"\"测试保存历史\"\"\"
        history_data = {
            'user_id': 1,
            'input_symptoms': ['头痛'],
            'result_drugs': [{'id': 1, 'name': '退烧药'}],
            'result_count': 1,
            'status': 'success'
        }
        result = self.service.save_history(history_data)
        self.assertTrue(result['success'])
    
    def test_get_history(self):
        \"\"\"测试获取历史\"\"\"
        # 先保存一条历史
        self.service.save_history({
            'user_id': 1,
            'input_symptoms': ['头痛'],
            'result_drugs': [],
            'status': 'success'
        })
        
        # 获取历史
        result = self.service.get_history(user_id=1)
        self.assertTrue(result['success'])
        self.assertGreater(result['total'], 0)
    
    def test_get_history_detail(self):
        \"\"\"测试获取历史详情\"\"\"
        # 先保存一条历史
        save_result = self.service.save_history({
            'user_id': 2,
            'input_symptoms': ['发热'],
            'result_drugs': [],
            'status': 'success',
            'request_id': 'test-request-123'
        })
        
        # 获取详情
        history_id = save_result['history_id']
        result = self.service.get_history_detail(history_id)
        self.assertTrue(result['success'])
    
    def test_get_user_statistics(self):
        \"\"\"测试获取用户统计\"\"\"
        # 保存多条历史
        for i in range(3):
            self.service.save_history({
                'user_id': 3,
                'input_symptoms': ['头痛'],
                'result_drugs': [],
                'status': 'success',
                'execution_time': 0.1
            })
        
        # 获取统计
        stats = self.service.get_user_statistics(user_id=3)
        self.assertTrue(stats['success'])
        self.assertEqual(stats['total_queries'], 3)
        self.assertEqual(stats['successful_queries'], 3)


if __name__ == '__main__':
    unittest.main()
