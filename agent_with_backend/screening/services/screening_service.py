"""药品筛选服务"""

import json
import logging
import time
import uuid
from typing import List, Dict, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class ScreeningService:
    """药品筛选服务
    
    负责：
    - 基于症状的药品筛选
    - 多参数筛选
    - 批量筛选
    - 结果排序和聚合
    """

    def __init__(self, symptom_service=None, db_session=None):
        """初始化筛选服务
        
        Args:
            symptom_service: 症状服务实例
            db_session: 数据库会话
        """
        self.symptom_service = symptom_service
        self.db_session = db_session
        self._cache = {}
    
    def screening_query(
        self,
        symptoms: List[str],
        patient_info: Optional[Dict] = None,
        filters: Optional[Dict] = None,
        user_id: Optional[int] = None,
        request_id: Optional[str] = None,
    ) -> Dict:
        """执行药品筛选查询
        
        Args:
            symptoms: 标准化的症状列表
            patient_info: 患者信息（年龄、性别等）
            filters: 筛选条件（如价格范围、类别等）
            user_id: 用户ID
            request_id: 请求ID
            
        Returns:
            {
                'success': bool,
                'results': [...],  # 筛选结果
                'confidence_scores': {...},  # 置信度
                'total_count': int,
                'request_id': str,
                'execution_time': float,
            }
        """
        start_time = time.time()
        request_id = request_id or str(uuid.uuid4())
        
        try:
            # 1. 症状验证
            if not symptoms:
                return {
                    'success': False,
                    'error': '症状列表不能为空',
                    'request_id': request_id,
                }
            
            # 2. 匹配药品
            candidates = self._match_drugs_by_symptoms(symptoms)
            
            # 3. 应用筛选条件
            if filters:
                candidates = self._apply_filters(candidates, filters)
            
            # 4. 考虑患者信息
            if patient_info:
                self._current_patient_info = patient_info  # 供排序引擎使用
                candidates = self._apply_patient_info_filters(candidates, patient_info)
            else:
                self._current_patient_info = None
            
            # 5. 排序和计算置信度
            ranked_results = self._rank_results(candidates, symptoms)
            
            # 6. 限制结果数量
            max_results = filters.get('max_results', 20) if filters else 20
            final_results = ranked_results[:max_results]
            
            execution_time = time.time() - start_time
            
            return {
                'success': True,
                'results': final_results,
                'confidence_scores': {
                    r['drug_id']: r['confidence_score']
                    for r in final_results
                },
                'total_count': len(final_results),
                'request_id': request_id,
                'execution_time': execution_time,
                'timestamp': datetime.utcnow().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Screening query error: {str(e)}")
            execution_time = time.time() - start_time
            
            return {
                'success': False,
                'error': str(e),
                'request_id': request_id,
                'execution_time': execution_time,
                'timestamp': datetime.utcnow().isoformat(),
            }
    
    def batch_screening(
        self,
        queries: List[Dict],
        batch_id: Optional[str] = None,
    ) -> Dict:
        """执行批量筛选
        
        Args:
            queries: 查询列表，每个查询包含症状、患者信息等
            batch_id: 批处理ID
            
        Returns:
            批处理结果
        """
        batch_id = batch_id or str(uuid.uuid4())
        results = []
        errors = []
        
        for idx, query in enumerate(queries):
            try:
                result = self.screening_query(
                    symptoms=query.get('symptoms', []),
                    patient_info=query.get('patient_info'),
                    filters=query.get('filters'),
                    user_id=query.get('user_id'),
                    request_id=f"{batch_id}-{idx}"
                )
                results.append(result)
            except Exception as e:
                errors.append({
                    'query_index': idx,
                    'error': str(e),
                })
        
        return {
            'batch_id': batch_id,
            'total_queries': len(queries),
            'successful_queries': len(results),
            'failed_queries': len(errors),
            'results': results,
            'errors': errors,
            'timestamp': datetime.utcnow().isoformat(),
        }
    
    def _load_drugs_from_db(self) -> List[Dict]:
        """从数据库加载所有可用药品（含适应症）"""
        try:
            from common.utils.database import get_db_connection
            conn = get_db_connection()
            try:
                cursor = conn.execute(
                    "SELECT * FROM inventory WHERE is_deleted = 0 AND quantity > 0"
                )
                drugs = [dict(row) for row in cursor.fetchall()]

                drug_ids = [d["drug_id"] for d in drugs]
                if drug_ids:
                    placeholders = ",".join("?" for _ in drug_ids)
                    cursor = conn.execute(
                        f"SELECT drug_id, indication FROM drug_indications WHERE drug_id IN ({placeholders})",
                        drug_ids,
                    )
                    imap = {}
                    for row in cursor.fetchall():
                        imap.setdefault(row["drug_id"], []).append(row["indication"])
                    for d in drugs:
                        d["suitable_symptoms"] = imap.get(d["drug_id"], [])
                else:
                    for d in drugs:
                        d["suitable_symptoms"] = []

                return drugs
            finally:
                conn.close()
        except Exception as e:
            logger.error(f"从数据库加载药品失败: {e}")
            return []

    def _match_drugs_by_symptoms(self, symptoms: List[str]) -> List[Dict]:
        """根据症状从数据库匹配药品"""
        all_drugs = self._load_drugs_from_db()
        if not all_drugs:
            return []

        candidates = []
        for drug in all_drugs:
            suitable = drug.get("suitable_symptoms", [])
            matched_symptoms = [s for s in symptoms if s in suitable]

            if matched_symptoms:
                match_ratio = len(matched_symptoms) / len(symptoms) if symptoms else 0
                candidates.append({
                    'drug_id': drug['drug_id'],
                    'drug_name': drug['name'],
                    'category': drug.get('category', ''),
                    'matched_symptoms': matched_symptoms,
                    'match_ratio': match_ratio,
                    'effectiveness': 0.8,  # 基线值，后续可由排序引擎调整
                    'price': drug.get('retail_price', 0),
                    'quantity': drug.get('quantity', 0),
                    'contraindications': drug.get('contraindications', ''),
                    'pregnancy_category': drug.get('pregnancy_category', ''),
                    'age_restrictions': drug.get('age_restrictions', '{}'),
                })

        return candidates
    
    def _apply_filters(self, candidates: List[Dict], filters: Dict) -> List[Dict]:
        """应用筛选条件
        
        Args:
            candidates: 候选药品列表
            filters: 筛选条件
            
        Returns:
            过滤后的药品列表
        """
        result = candidates
        
        # 价格筛选
        if 'price_range' in filters:
            min_price, max_price = filters['price_range']
            result = [
                d for d in result
                if min_price <= d['price'] <= max_price
            ]
        
        # 分类筛选
        if 'categories' in filters:
            categories = filters['categories']
            result = [
                d for d in result
                if d['category'] in categories
            ]
        
        # 效率筛选
        if 'min_effectiveness' in filters:
            min_eff = filters['min_effectiveness']
            result = [
                d for d in result
                if d['effectiveness'] >= min_eff
            ]
        
        return result
    
    def _apply_patient_info_filters(self, candidates: List[Dict], patient_info: Dict) -> List[Dict]:
        """基于患者信息应用筛选（过敏、年龄、孕期）

        Args:
            candidates: 候选药品列表
            patient_info: 患者信息

        Returns:
            过滤后的药品列表
        """
        if not patient_info:
            return candidates

        result = candidates

        # 过敏过滤
        allergies = patient_info.get('allergies', [])
        if allergies:
            result = []
            for drug in candidates:
                contraindications = (drug.get('contraindications') or '').lower()
                has_allergy = any(
                    allergy.lower() in contraindications for allergy in allergies
                )
                if not has_allergy:
                    result.append(drug)

        # 年龄过滤
        age = patient_info.get('age')
        if age is not None and age > 65:
            result = [
                d for d in result
                if not self._is_high_risk_for_elderly(d)
            ]

        return result

    def _is_high_risk_for_elderly(self, drug: Dict) -> bool:
        """判断药品是否对老年人高风险"""
        try:
            restrictions = json.loads(drug.get('age_restrictions') or '{}')
            max_age = restrictions.get('max_age', 200)
            return max_age < 65
        except (json.JSONDecodeError, TypeError):
            return False
    
    def _rank_results(self, candidates: List[Dict], symptoms: List[str]) -> List[Dict]:
        """使用评分排序引擎对结果排序"""
        from screening.services.ranking_engine import rank_drugs

        patient_info = getattr(self, '_current_patient_info', {})
        ranked = rank_drugs(candidates, patient_info)

        # 分离排除和有效药品
        valid = [d for d in ranked if not d.get('excluded')]
        excluded = [d for d in ranked if d.get('excluded')]

        # 有效药品在前，排除药品在后并标注原因
        for d in excluded:
            d['confidence_score'] = 0
        return valid + excluded
    
    def get_service_status(self) -> Dict:
        """获取筛选服务状态
        
        Returns:
            服务状态信息
        """
        return {
            'status': 'healthy',
            'service_name': 'ScreeningService',
            'version': '1.0.0',
            'timestamp': datetime.utcnow().isoformat(),
            'metrics': {
                'available_drugs': len(self._load_drugs_from_db()),
                'cache_size': len(self._cache),
            }
        }
