"""症状提取子代理 - 从用户输入提取结构化症状信息"""

import logging
import json
import asyncio
import re
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class Gender(Enum):
    """性别枚举"""
    MALE = "M"
    FEMALE = "F"
    OTHER = "other"


class ExtractionError(Exception):
    """症状提取异常"""
    pass


@dataclass
class PatientInfo:
    """患者基本信息"""
    age: Optional[int] = None              # 年龄
    weight: Optional[float] = None         # 体重（kg）
    gender: Optional[str] = None           # 性别 (M/F/other)
    allergies: Optional[List[str]] = None  # 过敏史
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "age": self.age,
            "weight": self.weight,
            "gender": self.gender,
            "allergies": self.allergies or []
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PatientInfo":
        """从字典创建"""
        return cls(
            age=data.get("age"),
            weight=data.get("weight"),
            gender=data.get("gender"),
            allergies=data.get("allergies")
        )


@dataclass
class StructuredSymptoms:
    """结构化症状信息"""
    chief_complaint: str                   # 主诉（主要症状）
    symptoms: List[str] = field(default_factory=list)  # 症状列表
    signs: Dict[str, Any] = field(default_factory=dict)  # 体征 {体征名称: 值}
    patient_info: PatientInfo = field(default_factory=PatientInfo)  # 患者信息
    medical_history: Optional[Dict[str, Any]] = None  # 既往史
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "chief_complaint": self.chief_complaint,
            "symptoms": self.symptoms,
            "signs": self.signs,
            "patient_info": self.patient_info.to_dict(),
            "medical_history": self.medical_history
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StructuredSymptoms":
        """从字典创建"""
        return cls(
            chief_complaint=data.get("chief_complaint", ""),
            symptoms=data.get("symptoms", []),
            signs=data.get("signs", {}),
            patient_info=PatientInfo.from_dict(data.get("patient_info", {})),
            medical_history=data.get("medical_history")
        )


class SymptomExtractor:
    """症状提取核心类 - 支持两种提取模式：规则提取和LLM提取"""
    
    def __init__(self, llm_client=None, use_llm: bool = True):
        """
        初始化症状提取器
        
        Args:
            llm_client: LLM客户端实例（可选）
            use_llm: 是否使用LLM模式，False则使用规则提取（快速但精度低）
        """
        self.llm_client = llm_client
        self.use_llm = use_llm and llm_client is not None
        
        if not self.use_llm:
            logger.info("症状提取器初始化为规则提取模式")
        else:
            logger.info("症状提取器初始化为LLM提取模式")
    
    def extract(self, user_input: str) -> StructuredSymptoms:
        """
        同步症状提取（推荐使用异步版本）
        
        Args:
            user_input: 用户输入的症状描述
        
        Returns:
            StructuredSymptoms: 结构化症状信息
        
        Raises:
            ExtractionError: 提取失败时抛出
        """
        if not user_input or not user_input.strip():
            raise ExtractionError("用户输入不能为空")
        
        try:
            if self.use_llm:
                return self._extract_with_llm(user_input)
            else:
                return self._extract_with_rules(user_input)
        
        except Exception as e:
            logger.error(f"症状提取失败: {e}")
            raise ExtractionError(f"症状提取失败: {str(e)}")
    
    async def extract_async(self, user_input: str) -> StructuredSymptoms:
        """
        异步症状提取
        
        Args:
            user_input: 用户输入的症状描述
        
        Returns:
            StructuredSymptoms: 结构化症状信息
        """
        if not user_input or not user_input.strip():
            raise ExtractionError("用户输入不能为空")
        
        try:
            if self.use_llm:
                return await self._extract_with_llm_async(user_input)
            else:
                return self._extract_with_rules(user_input)
        
        except Exception as e:
            logger.error(f"异步症状提取失败: {e}")
            raise ExtractionError(f"症状提取失败: {str(e)}")
    
    def _extract_with_rules(self, text: str) -> StructuredSymptoms:
        """规则提取模式（快速，精度低）"""
        logger.debug("使用规则提取症状信息")
        
        chief_complaint = self.extract_chief_complaint(text)
        symptoms = self.extract_symptoms(text)
        signs = self.extract_signs(text)
        patient_info = self.extract_patient_info(text)
        medical_history = self.extract_medical_history(text)
        
        return StructuredSymptoms(
            chief_complaint=chief_complaint,
            symptoms=symptoms,
            signs=signs,
            patient_info=patient_info,
            medical_history=medical_history
        )
    
    def _extract_with_llm(self, text: str) -> StructuredSymptoms:
        """LLM提取模式（精度高，速度慢）"""
        logger.debug("使用LLM提取症状信息")
        
        if not self.llm_client:
            logger.warning("LLM客户端不可用，降级为规则提取")
            return self._extract_with_rules(text)
        
        try:
            prompt = self._build_extraction_prompt(text)
            
            messages = [
                {"role": "system", "content": "你是医学信息提取专家"},
                {"role": "user", "content": prompt}
            ]
            
            response = self.llm_client.chat(messages)
            
            # 提取JSON响应
            json_text = self._extract_json_from_response(response.get("content", ""))
            result = json.loads(json_text)
            
            return StructuredSymptoms.from_dict(result)
        
        except Exception as e:
            logger.error(f"LLM提取失败，降级为规则提取: {e}")
            return self._extract_with_rules(text)
    
    async def _extract_with_llm_async(self, text: str) -> StructuredSymptoms:
        """异步LLM提取"""
        # 在线程池中运行同步LLM调用
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._extract_with_llm, text)
    
    def extract_chief_complaint(self, text: str) -> str:
        """提取主诉"""
        # 简单规则：取第一句或第一长句
        sentences = re.split(r'[。！？]', text.strip())
        if sentences:
            complaint = sentences[0].strip()
            return complaint if complaint else "患者症状描述"
        return "患者症状描述"
    
    def extract_patient_info(self, text: str) -> PatientInfo:
        """提取患者基本信息"""
        info = PatientInfo()
        
        # 提取年龄
        age_match = re.search(r'(\d{1,3})岁|年龄.*?(\d{1,3})', text)
        if age_match:
            age = age_match.group(1) or age_match.group(2)
            try:
                info.age = int(age)
            except ValueError:
                pass
        
        # 提取体重
        weight_match = re.search(r'体重.*?(\d+(?:\.\d+)?)\s*kg|(\d+(?:\.\d+)?)\s*kg', text)
        if weight_match:
            weight = weight_match.group(1) or weight_match.group(2)
            try:
                info.weight = float(weight)
            except ValueError:
                pass
        
        # 提取性别
        if re.search(r'男|男性', text):
            info.gender = Gender.MALE.value
        elif re.search(r'女|女性', text):
            info.gender = Gender.FEMALE.value
        
        # 提取过敏史
        allergies = []
        allergy_match = re.search(r'对(\S+?)过敏|过敏[于到]?\s*(\S+?)[,，。！]', text)
        if allergy_match:
            allergen = allergy_match.group(1) or allergy_match.group(2)
            if allergen:
                allergies.append(allergen.strip())
        
        # 支持列表式过敏
        multiple_allergies = re.findall(r'过敏[于到]?\s*([^,，。！]+)', text)
        allergies.extend(multiple_allergies)
        
        if allergies:
            info.allergies = list(set(allergies))  # 去重
        
        return info
    
    def extract_symptoms(self, text: str) -> List[str]:
        """提取症状列表"""
        # 常见症状库
        symptom_keywords = [
            '头痛', '头晕', '发热', '发烧', '烧', '咳嗽', '咳', '喉咙痛',
            '喉症', '流鼻涕', '打喷嚏', '喷嚏', '恶心', '呕吐', '腹泻',
            '腹痛', '肚子痛', '肌肉酸痛', '乏力', '疲劳', '疲惫',
            '失眠', '多梦', '食欲', '胃痛', '胃酸', '反酸',
            '便秘', '腹胀', '胸痛', '心悸', '心跳加快', '低血糖',
            '四肢无力', '手抖', '头昏', '眩晕', '皮疹', '皮痒',
            '湿疹', '荨麻疹', '过敏', '浮肿', '肿胀', '出血'
        ]
        
        symptoms = []
        for symptom in symptom_keywords:
            if symptom in text:
                if symptom not in symptoms:
                    symptoms.append(symptom)
        
        return symptoms
    
    def extract_signs(self, text: str) -> Dict[str, Any]:
        """提取体征"""
        signs = {}
        
        # 体温
        temp_match = re.search(r'体温.*?(\d+(?:\.\d+)?)\s*°?C|温度.*?(\d+(?:\.\d+)?)', text)
        if temp_match:
            temp = temp_match.group(1) or temp_match.group(2)
            try:
                signs['体温'] = float(temp)
            except ValueError:
                pass
        
        # 心率
        heart_rate_match = re.search(r'心率.*?(\d+)\s*(?:次|bpm)|脉搏.*?(\d+)', text)
        if heart_rate_match:
            hr = heart_rate_match.group(1) or heart_rate_match.group(2)
            try:
                signs['心率'] = int(hr)
            except ValueError:
                pass
        
        # 血压
        bp_match = re.search(r'血压.*?(\d+).*?(\d+)|(\d+)/(\d+)\s*mmHg', text)
        if bp_match:
            if bp_match.group(1) and bp_match.group(2):
                signs['血压'] = f"{bp_match.group(1)}/{bp_match.group(2)}"
            elif bp_match.group(3) and bp_match.group(4):
                signs['血压'] = f"{bp_match.group(3)}/{bp_match.group(4)}"
        
        # 其他通用体征
        if '黄疸' in text:
            signs['黄疸'] = True
        if '水肿' in text or '浮肿' in text:
            signs['水肿'] = True
        
        return signs
    
    def extract_medical_history(self, text: str) -> Optional[Dict[str, Any]]:
        """提取既往史"""
        history = {}
        
        # 常见既往病史
        conditions = {
            '高血压': ['高血压', '血压高'],
            '糖尿病': ['糖尿病', '血糖'],
            '心脏病': ['心脏病', '冠心病', '心梗'],
            '肺结核': ['结核', '肺结核'],
            '肝炎': ['肝炎', '乙肝', '丙肝'],
            '肾脏病': ['肾病', '肾炎'],
            '癌症': ['癌症', '癌', '肿瘤'],
            '哮喘': ['哮喘', '气喘'],
            '胃溃疡': ['胃溃疡', '消化性溃疡']
        }
        
        for condition, keywords in conditions.items():
            for keyword in keywords:
                if keyword in text:
                    history[condition] = True
                    break
        
        return history if history else None
    
    def validate_symptoms(self, symptoms: StructuredSymptoms) -> Tuple[bool, Optional[str]]:
        """
        验证提取的症状信息
        
        Returns:
            Tuple[bool, Optional[str]]: (是否有效, 错误信息)
        """
        if not symptoms.chief_complaint or not symptoms.chief_complaint.strip():
            return False, "主诉不能为空"
        
        if not symptoms.symptoms and not symptoms.signs:
            return False, "至少需要症状或体征信息"
        
        if symptoms.patient_info.age is not None:
            if not (0 < symptoms.patient_info.age < 150):
                return False, f"年龄无效: {symptoms.patient_info.age}"
        
        if symptoms.patient_info.weight is not None:
            if not (1 < symptoms.patient_info.weight < 500):
                return False, f"体重无效: {symptoms.patient_info.weight}"
        
        return True, None
    
    @staticmethod
    def _build_extraction_prompt(text: str) -> str:
        """构建LLM提取提示词"""
        return f"""请分析患者的症状描述，提取结构化的医学信息。

患者描述：
{text}

请返回JSON格式的结果，包含以下字段：
{{
    "chief_complaint": "主诉（主要症状）",
    "symptoms": ["症状1", "症状2", ...],
    "signs": {{
        "体征名称": "值",
        ...
    }},
    "patient_info": {{
        "age": 年龄或null,
        "weight": 体重或null,
        "gender": "M"/"F"/"other" 或null,
        "allergies": ["过敏1", ...] 或null
    }},
    "medical_history": {{
        "既往病": "描述",
        ...
    }} 或null
}}

只返回JSON，不要其他内容。"""
    
    @staticmethod
    def _extract_json_from_response(response: str) -> str:
        """从LLM响应中提取JSON"""
        # 尝试找到JSON块
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json_match.group(0)
        
        # 如果找不到，尝试暴力解析
        if response.strip().startswith('{'):
            return response.strip()
        
        raise ExtractionError("无法从响应中提取JSON")


# 便捷函数：同步版本
def extract_symptoms(user_input: str, llm_client=None) -> StructuredSymptoms:
    """
    同步症状提取函数
    
    Args:
        user_input: 用户输入的症状描述
        llm_client: 可选的LLM客户端，使用则启用LLM模式
    
    Returns:
        StructuredSymptoms: 结构化症状信息
    
    Raises:
        ExtractionError: 提取失败时抛出
    """
    use_llm = llm_client is not None
    extractor = SymptomExtractor(llm_client, use_llm=use_llm)
    return extractor.extract(user_input)


# 便捷函数：异步版本
async def extract_symptoms_async(user_input: str, llm_client=None) -> StructuredSymptoms:
    """
    异步症状提取函数
    
    Args:
        user_input: 用户输入的症状描述
        llm_client: 可选的LLM客户端，使用则启用LLM模式
    
    Returns:
        StructuredSymptoms: 结构化症状信息
    """
    use_llm = llm_client is not None
    extractor = SymptomExtractor(llm_client, use_llm=use_llm)
    return await extractor.extract_async(user_input)


# 便捷函数：同步版本（使用完整LLM）
def extract_symptoms_sync(user_input: str, llm_client=None) -> StructuredSymptoms:
    """同步症状提取的别名"""
    return extract_symptoms(user_input, llm_client)
