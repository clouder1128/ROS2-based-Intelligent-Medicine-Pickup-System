"""药品评分排序引擎"""

import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class RankingEngine:
    """药品评分排序引擎

    综合评分维度：
    - 症状匹配度（命中适应症的比例）
    - 过敏排除（直接排除）
    - 库存可用性（库存为0则降级）
    - 患者适宜性（年龄限制、孕期分级）
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.weights = {
            'match_ratio': self.config.get('weight_match_ratio', 0.5),
            'effectiveness': self.config.get('weight_effectiveness', 0.3),
            'price': self.config.get('weight_price', 0.2),
        }

    def rank(
        self,
        candidates: List[Dict[str, Any]],
        patient_info: Dict[str, Any] = None,
        symptoms: List[str] = None,
    ) -> List[Dict[str, Any]]:
        """对候选药品进行评分排序

        Args:
            candidates: 候选药品列表
            patient_info: 患者信息 {age, gender, allergies, ...}
            symptoms: 原始症状列表

        Returns:
            评分排序后的药品列表，每项包含 confidence_score
        """
        patient_info = patient_info or {}
        allergies = patient_info.get('allergies', []) or []

        # 第一轮：过敏排除
        filtered = self._filter_by_allergies(candidates, allergies)

        # 第二轮：患者适宜性过滤
        filtered = self._filter_by_patient_suitability(filtered, patient_info)

        # 第三轮：评分
        for drug in filtered:
            score = self._calculate_score(drug, patient_info)
            drug['confidence_score'] = round(score, 4)

        # 按评分降序排列
        ranked = sorted(filtered, key=lambda x: x['confidence_score'], reverse=True)
        return ranked

    def _filter_by_allergies(
        self, candidates: List[Dict], allergies: List[str]
    ) -> List[Dict]:
        """排除患者过敏的药品"""
        if not allergies:
            return candidates

        result = []
        for drug in candidates:
            contraindications = (drug.get('contraindications') or '').lower()
            is_allergic = False
            for allergy in allergies:
                if allergy.lower() in contraindications:
                    is_allergic = True
                    break
            if not is_allergic:
                result.append(drug)
            else:
                drug['excluded'] = True
                drug['exclude_reason'] = '过敏禁忌'
                result.append(drug)  # 仍保留但标记
        return result

    def _filter_by_patient_suitability(
        self, candidates: List[Dict], patient_info: Dict
    ) -> List[Dict]:
        """根据患者年龄、孕期等信息过滤"""
        age = patient_info.get('age')
        if age is None:
            return candidates

        result = []
        for drug in candidates:
            try:
                restrictions = json.loads(drug.get('age_restrictions') or '{}')
            except (json.JSONDecodeError, TypeError):
                restrictions = {}

            min_age = restrictions.get('min_age', 0)
            max_age = restrictions.get('max_age', 200)

            if min_age <= age <= max_age:
                result.append(drug)
            else:
                drug['excluded'] = True
                drug['exclude_reason'] = f'年龄限制({min_age}-{max_age}岁)'
                result.append(drug)

        return result

    def _calculate_score(self, drug: Dict, patient_info: Dict) -> float:
        """计算单个药品的综合评分"""
        match_ratio = drug.get('match_ratio', 0)
        price = drug.get('price', 0)
        quantity = drug.get('quantity', 0)

        # 症状匹配分
        match_score = match_ratio * self.weights['match_ratio']

        # 价格分（价格越低分越高）
        price_score = (1 - min(price, 100) / 100) * self.weights['price'] if price > 0 else 0

        # 库存可用性加权（库存为0则在基线分基础上减半）
        stock_multiplier = 0.5 if quantity <= 0 else 1.0

        # 排除惩罚
        exclusion_penalty = 0.3 if drug.get('excluded') else 0

        base_score = match_score + 0.5 * self.weights['effectiveness'] + price_score
        final_score = base_score * stock_multiplier - exclusion_penalty

        return max(final_score, 0)


# 便捷函数
def rank_drugs(
    candidates: List[Dict[str, Any]],
    patient_info: Dict[str, Any] = None,
    config: Dict[str, Any] = None,
) -> List[Dict[str, Any]]:
    engine = RankingEngine(config)
    return engine.rank(candidates, patient_info)
