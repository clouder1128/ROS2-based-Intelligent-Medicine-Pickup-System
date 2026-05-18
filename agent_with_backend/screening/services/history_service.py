"""筛选历史服务"""

import json
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class HistoryService:
    """筛选历史服务

    负责：
    - 保存筛选历史
    - 查询历史记录
    - 历史数据分析
    """

    def __init__(self, db_session=None):
        """初始化历史服务

        Args:
            db_session: 数据库会话
        """
        self.db_session = db_session
        self._memory_storage = []  # 内存存储，用于开发测试

    def save_history(self, history_data: Dict) -> Dict:
        """保存筛选历史记录到数据库

        Args:
            history_data: 历史数据

        Returns:
            保存结果
        """
        try:
            from common.utils.database import get_db_connection
            conn = get_db_connection()
            try:
                conn.execute(
                    """INSERT INTO screening_history
                       (user_id, input_symptoms, patient_info, filters,
                        result_drugs, result_count, confidence_scores,
                        execution_time, status, error_message, request_id)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        history_data.get('user_id'),
                        json.dumps(history_data.get('input_symptoms', []), ensure_ascii=False),
                        json.dumps(history_data.get('patient_info', {}), ensure_ascii=False),
                        json.dumps(history_data.get('filters', {}), ensure_ascii=False),
                        json.dumps(history_data.get('result_drugs', []), ensure_ascii=False),
                        history_data.get('result_count', 0),
                        json.dumps(history_data.get('confidence_scores', {}), ensure_ascii=False),
                        history_data.get('execution_time'),
                        history_data.get('status', 'success'),
                        history_data.get('error_message', ''),
                        history_data.get('request_id', ''),
                    )
                )
                conn.commit()
                history_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                return {'success': True, 'history_id': history_id, 'message': '历史记录保存成功'}
            finally:
                conn.close()
        except Exception as e:
            logger.error(f"Error saving history: {str(e)}")
            return {'success': False, 'error': str(e)}

    def get_history(
        self,
        user_id: int,
        limit: int = 20,
        offset: int = 0,
        date_range: Optional[tuple] = None,
    ) -> Dict:
        """从数据库获取用户的筛选历史

        Args:
            user_id: 用户ID
            limit: 返回数量限制
            offset: 分页偏移
            date_range: 日期范围 (start_date, end_date)

        Returns:
            历史记录列表
        """
        try:
            from common.utils.database import get_db_connection
            conn = get_db_connection()
            try:
                where_parts = ["user_id = ?"]
                params = [user_id]

                if date_range:
                    where_parts.append("created_at >= ? AND created_at <= ?")
                    params.extend([date_range[0].isoformat(), date_range[1].isoformat()])

                where_sql = " AND ".join(where_parts)

                count_row = conn.execute(
                    f"SELECT COUNT(*) as cnt FROM screening_history WHERE {where_sql}",
                    params,
                ).fetchone()
                total = count_row["cnt"] if count_row else 0

                rows = conn.execute(
                    f"SELECT * FROM screening_history WHERE {where_sql} ORDER BY created_at DESC LIMIT ? OFFSET ?",
                    params + [limit, offset],
                ).fetchall()

                history = []
                for row in rows:
                    record = dict(row)
                    for json_field in ['input_symptoms', 'patient_info', 'filters', 'result_drugs', 'confidence_scores']:
                        try:
                            val = record.get(json_field) or '[]' if json_field in ('input_symptoms', 'result_drugs') else '{}'
                            record[json_field] = json.loads(val)
                        except (json.JSONDecodeError, TypeError):
                            record[json_field] = [] if json_field in ('input_symptoms', 'result_drugs') else {}
                    history.append(record)

                return {
                    'success': True,
                    'user_id': user_id,
                    'total': total,
                    'limit': limit,
                    'offset': offset,
                    'count': len(history),
                    'history': history,
                }
            finally:
                conn.close()
        except Exception as e:
            logger.error(f"Error getting history: {str(e)}")
            return {'success': False, 'error': str(e)}

    def get_history_detail(self, history_id: int) -> Dict:
        """获取单条历史记录详情

        Args:
            history_id: 历史记录ID

        Returns:
            历史记录详情
        """
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
        """根据请求ID获取历史记录

        Args:
            request_id: 请求ID

        Returns:
            历史记录
        """
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
        """删除历史记录

        Args:
            history_id: 历史记录ID

        Returns:
            删除结果
        """
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
        """清理旧的历史记录

        Args:
            days: 保留天数，超过此时间的记录将被删除

        Returns:
            清理结果
        """
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
        """获取用户的筛选统计信息

        Args:
            user_id: 用户ID

        Returns:
            统计信息
        """
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
