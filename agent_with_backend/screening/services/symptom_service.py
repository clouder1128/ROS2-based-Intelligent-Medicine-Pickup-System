"""症状处理服务"""

import json
import logging
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class SymptomService:
    """症状处理服务
    
    负责：
    - 症状文本标准化
    - 同义词扩展
    - 症状相似度计算
    """
    
    # 示例基础症状库 - 实际应该从数据库加载
    STANDARD_SYMPTOMS = {
        '头痛': ['头疼', '头痛'],
        '发热': ['发烧', '发热', '高热'],
        '咳嗽': ['咳嗽'],
        '喉咙疼痛': ['喉咙痛', '咽痛'],
        '腹泻': ['腹泻', '拉肚子'],
        '便秘': ['便秘', '排便困难'],
        '恶心': ['恶心', '想吐'],
        '呕吐': ['呕吐', '吐'],
        '腹痛': ['腹痛', '肚子疼'],
        '肌肉酸痛': ['肌肉酸痛', '肌肉疼'],
        '失眠': ['失眠', '睡眠不好'],
        '嗜睡': ['嗜睡', '总想睡', '嗜睡'],
        '手脚冰冷': ['手脚冷', '怕冷'],
        '皮疹': ['皮疹', '长疹子'],
        '瘙痒': ['瘙痒', '痒'],
    }
    
    def __init__(self, db_session=None):
        """初始化症状服务
        
        Args:
            db_session: 数据库会话，用于从数据库加载症状库
        """
        self.db_session = db_session
        self.symptom_cache = {}
        self._load_symptoms()
    
    def _load_symptoms(self):
        \"\"\"从数据库加载症状定义\"\"\"
        # TODO: 从数据库加载症状
        # 如果提供了db_session，从数据库加载
        # 否则使用内置的示例症状库
        pass
    
    def standardize_symptom(self, symptom_text: str) -> Optional[str]:
        \"\"\"标准化单个症状
        
        将用户输入的症状文本转换为标准症状名称
        
        Args:
            symptom_text: 用户输入的症状文本
            
        Returns:
            标准症状名称，如果没有匹配则返回None
        \"\"\"
        symptom_text = symptom_text.strip().lower()
        
        # 精确匹配
        for standard, synonyms in self.STANDARD_SYMPTOMS.items():
            if symptom_text in synonyms or symptom_text in standard.lower():
                return standard
        
        # 模糊匹配 - 使用相似度算法
        best_match = None
        best_ratio = 0.6  # 相似度阈值
        
        for standard, synonyms in self.STANDARD_SYMPTOMS.items():
            for synonym in synonyms:
                ratio = SequenceMatcher(None, symptom_text, synonym.lower()).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_match = standard
        
        return best_match
    
    def standardize_symptoms(self, symptom_texts: List[str]) -> Dict[str, any]:
        \"\"\"标准化多个症状
        
        Args:
            symptom_texts: 症状文本列表
            
        Returns:
            {
                'standardized_symptoms': [...],  # 标准化后的症状列表
                'unmatched': [...],  # 无法匹配的症状
                'confidence': float,  # 整体匹配置信度
            }
        \"\"\"
        standardized = []
        unmatched = []
        matched_count = 0
        
        for symptom_text in symptom_texts:
            standard = self.standardize_symptom(symptom_text)
            if standard:
                standardized.append(standard)
                matched_count += 1
            else:
                unmatched.append(symptom_text)
        
        confidence = matched_count / len(symptom_texts) if symptom_texts else 0
        
        return {
            'standardized_symptoms': list(set(standardized)),  # 去重
            'unmatched': unmatched,
            'confidence': confidence,
            'input_count': len(symptom_texts),
            'matched_count': matched_count,
            'unmatched_count': len(unmatched),
        }
    
    def get_synonyms(self, symptom_name: str) -> List[str]:
        \"\"\"获取症状的所有同义词
        
        Args:
            symptom_name: 标准症状名称
            
        Returns:
            同义词列表
        \"\"\"
        return self.STANDARD_SYMPTOMS.get(symptom_name, [])
    
    def calculate_symptom_similarity(self, text1: str, text2: str) -> float:
        \"\"\"计算两个症状文本的相似度
        
        Args:
            text1: 第一个症状文本
            text2: 第二个症状文本
            
        Returns:
            相似度分数（0-1）
        \"\"\"
        text1_lower = text1.lower().strip()
        text2_lower = text2.lower().strip()
        
        return SequenceMatcher(None, text1_lower, text2_lower).ratio()
    
    def get_symptom_categories(self) -> Dict[str, List[str]]:
        \"\"\"获取按分类组织的症状
        
        Returns:
            按分类组织的症状字典
        \"\"\"
        categories = {}
        
        # 简单分类逻辑
        category_map = {
            '消化道': ['腹泻', '便秘', '腹痛', '恶心', '呕吐'],
            '呼吸道': ['咳嗽', '喉咙疼痛'],
            '神经系统': ['头痛', '失眠', '嗜睡'],
            '全身症状': ['发热', '肌肉酸痛', '手脚冰冷'],
            '皮肤': ['皮疹', '瘙痒'],
        }
        
        return category_map
    
    def expand_symptoms_with_synonyms(self, symptoms: List[str]) -> List[str]:
        \"\"\"使用同义词扩展症状列表
        
        Args:
            symptoms: 症状列表（标准名称）
            
        Returns:
            扩展后的症状列表（包含同义词）
        \"\"\"
        expanded = set()
        
        for symptom in symptoms:
            expanded.add(symptom)
            synonyms = self.get_synonyms(symptom)
            expanded.update(synonyms)
        
        return list(expanded)
