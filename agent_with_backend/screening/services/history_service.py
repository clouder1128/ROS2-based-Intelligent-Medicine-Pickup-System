"""筛选历史服务"""

import json
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class HistoryService:
    \"\"\"筛选历史服务
    
    负责：
    - 保存筛选历史
    - 查询历史记录
    - 历史数据分析
    \"\"\"
    
    def __init__(self, db_session=None):
        \"\"\"初始化历史服务
        
        Args:
            db_session: 数据库会话
        \"\"\"
        self.db_session = db_session
        self._memory_storage = []  # 内存存储，用于开发测试
    
    def save_history(self, history_data: Dict) -> Dict:
        \"\"\"保存筛选历史记录
        
        Args:
            history_data: 历史数据
            
        Returns:
            保存结果
        \"\"\"
        try:
            # 准备历史记录
            record = {
                'id': len(self._memory_storage) + 1,  # 简单计数ID
                'user_id': history_data.get('user_id'),
                'input_symptoms': history_data.get('input_symptoms', []),
                'input_text': history_data.get('input_text'),
                'patient_info': history_data.get('patient_info'),
                'filters': history_data.get('filters'),
                'result_drugs': history_data.get('result_drugs', []),
                'result_count': history_data.get('result_count', 0),
                'confidence_scores': history_data.get('confidence_scores', {}),
                'execution_time': history_data.get('execution_time'),
                'status': history_data.get('status', 'success'),
                'error_message': history_data.get('error_message'),
                'request_id': history_data.get('request_id'),
                'created_at': datetime.utcnow().isoformat(),
            }
            
            # 保存到内存（开发用）
            self._memory_storage.append(record)
            
            # TODO: 保存到数据库
            # if self.db_session:
            #     from screening.models import ScreeningHistory
            #     db_history = ScreeningHistory(**record)
            #     self.db_session.add(db_history)
            #     self.db_session.commit()
            
            return {
                'success': True,
                'history_id': record['id'],
                'message': '历史记录保存成功'
            }
            
        except Exception as e:
            logger.error(f\"Error saving history: {str(e)}\")
            return {
                'success': False,
                'error': str(e),
            }
    
    def get_history(
        self,
        user_id: int,
        limit: int = 20,
        offset: int = 0,
        date_range: Optional[tuple] = None,
    ) -> Dict:
        \"\"\"获取用户的筛选历史
        
        Args:
            user_id: 用户ID
            limit: 返回数量限制
            offset: 分页偏移
            date_range: 日期范围 (start_date, end_date)
            
        Returns:
            历史记录列表
        \"\"\"
        # 过滤用户记录
        user_records = [
            r for r in self._memory_storage
            if r['user_id'] == user_id
        ]
        
        # 应用日期范围过滤
        if date_range:
            start_date, end_date = date_range
            user_records = [
                r for r in user_records
                if start_date <= datetime.fromisoformat(r['created_at']) <= end_date
            ]
        
        # 按时间倒序
        user_records.sort(
            key=lambda x: x['created_at'],
            reverse=True
        )
        
        # 分页
        total = len(user_records)
        paginated = user_records[offset:offset + limit]
        
        return {
            'success': True,
            'user_id': user_id,
            'total': total,
            'limit': limit,
            'offset': offset,
            'count': len(paginated),
            'history': paginated,
            'timestamp': datetime.utcnow().isoformat(),
        }
    
    def get_history_detail(self, history_id: int) -> Dict:
        \"\"\"获取单条历史记录详情
        
        Args:
            history_id: 历史记录ID
            
        Returns:
            历史记录详情
        \"\"\"
        for record in self._memory_storage:
            if record['id'] == history_id:
                return {
                    'success': True,
                    'detail': record,
                    'timestamp': datetime.utcnow().isoformat(),
                }
        
        return {
            'success': False,
            'error': f'历史记录 {history_id} 不存在',
        }
    
    def get_history_by_request_id(self, request_id: str) -> Dict:
        \"\"\"根据请求ID获取历史记录
        
        Args:
            request_id: 请求ID
            
        Returns:
            历史记录
        \"\"\"
        for record in self._memory_storage:
            if record['request_id'] == request_id:
                return {
                    'success': True,
                    'detail': record,
                    'timestamp': datetime.utcnow().isoformat(),
                }
        
        return {
            'success': False,
            'error': f'请求ID {request_id} 对应的历史记录不存在',
        }
    
    def delete_history(self, history_id: int) -> Dict:
        \"\"\"删除历史记录
        
        Args:
            history_id: 历史记录ID
            
        Returns:
            删除结果
        \"\"\"
        for idx, record in enumerate(self._memory_storage):
            if record['id'] == history_id:
                del self._memory_storage[idx]
                return {
                    'success': True,
                    'message': '历史记录删除成功'
                }
        
        return {
            'success': False,
            'error': f'历史记录 {history_id} 不存在',
        }
    
    def clear_old_history(self, days: int = 30) -> Dict:
        \"\"\"清理旧的历史记录
        
        Args:
            days: 保留天数，超过此时间的记录将被删除
            
        Returns:
            清理结果
        \"\"\"
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        original_count = len(self._memory_storage)
        
        # 保留新的记录
        self._memory_storage = [
            r for r in self._memory_storage
            if datetime.fromisoformat(r['created_at']) >= cutoff_date
        ]
        
        deleted_count = original_count - len(self._memory_storage)
        
        return {
            'success': True,
            'original_count': original_count,
            'remaining_count': len(self._memory_storage),
            'deleted_count': deleted_count,
            'message': f'成功删除 {deleted_count} 条旧记录'
        }
    
    def get_user_statistics(self, user_id: int) -> Dict:
        \"\"\"获取用户的筛选统计信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            统计信息
        \"\"\"
        user_records = [
            r for r in self._memory_storage
            if r['user_id'] == user_id
        ]
        
        if not user_records:
            return {
                'success': True,
                'user_id': user_id,
                'total_queries': 0,
                'successful_queries': 0,
                'failed_queries': 0,
                'average_execution_time': 0,
                'most_common_symptoms': [],
                'timestamp': datetime.utcnow().isoformat(),
            }
        
        # 计算统计信息
        successful = len([r for r in user_records if r['status'] == 'success'])
        failed = len([r for r in user_records if r['status'] != 'success'])
        
        # 计算平均执行时间
        execution_times = [
            r['execution_time'] for r in user_records
            if r['execution_time'] is not None
        ]
        avg_time = sum(execution_times) / len(execution_times) if execution_times else 0
        
        # 统计最常见的症状
        symptom_count = {}
        for record in user_records:
            for symptom in record['input_symptoms']:
                symptom_count[symptom] = symptom_count.get(symptom, 0) + 1
        
        common_symptoms = sorted(
            symptom_count.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            'success': True,
            'user_id': user_id,
            'total_queries': len(user_records),
            'successful_queries': successful,
            'failed_queries': failed,
            'success_rate': successful / len(user_records) if user_records else 0,
            'average_execution_time': avg_time,
            'most_common_symptoms': [s[0] for s in common_symptoms],
            'symptom_frequencies': dict(common_symptoms),
            'timestamp': datetime.utcnow().isoformat(),
        }
