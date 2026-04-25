"""症状提取核心业务逻辑 - SymptomExtractor类"""

import re
import json
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple

from .models import Gender, PatientInfo, StructuredSymptoms
from .exceptions import ExtractionError

logger = logging.getLogger(__name__)


class SymptomExtractor:
    """症状提取核心类 - 支持两种提取模式：规则提取和LLM提取"""

    DEGREE_WORDS = ["轻度", "中度", "重度", "轻微", "严重", "剧烈",
                    "偶尔", "持续性", "阵发性", "反复", "间断性"]

    def __init__(self, llm_client=None, use_llm: bool = True):
        self.llm_client = llm_client
        self.use_llm = use_llm and llm_client is not None
        if not self.use_llm:
            logger.info("症状提取器初始化为规则提取模式")
        else:
            logger.info("症状提取器初始化为LLM提取模式")

    def extract(self, user_input: str) -> StructuredSymptoms:
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
            json_text = self._extract_json_from_response(response.get("content", ""))
            result = json.loads(json_text)
            result["symptoms"] = self._clean_symptoms(result.get("symptoms", []))
            return StructuredSymptoms.from_dict(result)
        except Exception as e:
            logger.error(f"LLM提取失败，降级为规则提取: {e}")
            return self._extract_with_rules(text)

    async def _extract_with_llm_async(self, text: str) -> StructuredSymptoms:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._extract_with_llm, text)

    def extract_chief_complaint(self, text: str) -> str:
        sentences = re.split(r'[。！？]', text.strip())
        if sentences:
            complaint = sentences[0].strip()
            return complaint if complaint else "患者症状描述"
        return "患者症状描述"

    def extract_patient_info(self, text: str) -> PatientInfo:
        info = PatientInfo()
        age_match = re.search(r'(\d{1,3})岁|年龄.*?(\d{1,3})', text)
        if age_match:
            age = age_match.group(1) or age_match.group(2)
            try:
                info.age = int(age)
            except ValueError:
                pass
        weight_match = re.search(r'体重.*?(\d+(?:\.\d+)?)\s*kg|(\d+(?:\.\d+)?)\s*kg', text)
        if weight_match:
            weight = weight_match.group(1) or weight_match.group(2)
            try:
                info.weight = float(weight)
            except ValueError:
                pass
        if re.search(r'男|男性', text):
            info.gender = Gender.MALE.value
        elif re.search(r'女|女性', text):
            info.gender = Gender.FEMALE.value
        allergies = []
        allergy_match = re.search(r'对(\S+?)过敏|过敏[于到]?\s*(\S+?)[,，。！]', text)
        if allergy_match:
            allergen = allergy_match.group(1) or allergy_match.group(2)
            if allergen:
                allergies.append(allergen.strip())
        multiple_allergies = re.findall(r'过敏[于到]?\s*([^,，。！]+)', text)
        allergies.extend(multiple_allergies)
        if allergies:
            info.allergies = list(set(allergies))
        return info

    def extract_symptoms(self, text: str) -> List[str]:
        symptom_keywords = [
            '头痛', '头疼', '头晕', '发热', '发烧', '烧', '咳嗽', '咳', '喉咙痛',
            '喉症', '流鼻涕', '打喷嚏', '喷嚏', '恶心', '呕吐', '腹泻',
            '腹痛', '肚子痛', '肌肉酸痛', '乏力', '疲劳', '疲惫',
            '失眠', '多梦', '食欲', '胃痛', '胃酸', '反酸',
            '便秘', '腹胀', '胸痛', '心悸', '心跳加快', '低血糖',
            '四肢无力', '手抖', '头昏', '眩晕', '皮疹', '皮痒',
            '湿疹', '荨麻疹', '过敏', '浮肿', '肿胀', '出血'
        ]
        from common.config import Config
        negation_words = Config.NEGATION_WORDS
        symptoms = []
        for symptom in symptom_keywords:
            position = text.find(symptom)
            while position != -1:
                is_negated = False
                preceding_text = text[:position]
                for negation in negation_words:
                    negation_pos = preceding_text.rfind(negation)
                    if negation_pos != -1 and (position - negation_pos) < 20:
                        text_between = preceding_text[negation_pos:position]
                        if '。' not in text_between and '！' not in text_between and '？' not in text_between:
                            is_negated = True
                            break
                if not is_negated and symptom not in symptoms:
                    symptoms.append(symptom)
                position = text.find(symptom, position + len(symptom))
        return symptoms

    def extract_signs(self, text: str) -> Dict[str, Any]:
        signs = {}
        temp_match = re.search(r'体温.*?(\d+(?:\.\d+)?)\s*°?C|温度.*?(\d+(?:\.\d+)?)', text)
        if temp_match:
            temp = temp_match.group(1) or temp_match.group(2)
            try:
                signs['体温'] = float(temp)
            except ValueError:
                pass
        heart_rate_match = re.search(r'心率.*?(\d+)\s*(?:次|bpm)|脉搏.*?(\d+)', text)
        if heart_rate_match:
            hr = heart_rate_match.group(1) or heart_rate_match.group(2)
            try:
                signs['心率'] = int(hr)
            except ValueError:
                pass
        bp_match = re.search(r'血压.*?(\d+).*?(\d+)|(\d+)/(\d+)\s*mmHg', text)
        if bp_match:
            if bp_match.group(1) and bp_match.group(2):
                signs['血压'] = f"{bp_match.group(1)}/{bp_match.group(2)}"
            elif bp_match.group(3) and bp_match.group(4):
                signs['血压'] = f"{bp_match.group(3)}/{bp_match.group(4)}"
        if '黄疸' in text:
            signs['黄疸'] = True
        if '水肿' in text or '浮肿' in text:
            signs['水肿'] = True
        return signs

    def extract_medical_history(self, text: str) -> Optional[Dict[str, Any]]:
        history = {}
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
        if not symptoms.chief_complaint or not symptoms.chief_complaint.strip():
            return False, "主诉不能为空"
        if not symptoms.symptoms and not symptoms.signs:
            return False, "至少需要症状或体征信息"
        if symptoms.patient_info.age is not None and not (0 < symptoms.patient_info.age < 150):
            return False, f"年龄无效: {symptoms.patient_info.age}"
        if symptoms.patient_info.weight is not None and not (1 < symptoms.patient_info.weight < 500):
            return False, f"体重无效: {symptoms.patient_info.weight}"
        return True, None

    @staticmethod
    def _clean_symptoms(symptoms: List[str]) -> List[str]:
        """从症状列表中剥离程度词"""
        cleaned = []
        for s in symptoms:
            for degree in SymptomExtractor.DEGREE_WORDS:
                if s.startswith(degree):
                    s = s[len(degree):].strip()
            s = s.strip()
            if s:
                cleaned.append(s)
        return cleaned

    @staticmethod
    def _build_extraction_prompt(text: str) -> str:
        return f"""请分析患者的症状描述，提取结构化的医学信息。

患者描述：
{text}

请返回JSON格式的结果，包含以下字段：
{{
    "chief_complaint": "主诉（主要症状）",
    "symptoms": ["症状1", "症状2", ...],
    "severity": {{"症状名": "程度"}},
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

注意：
- symptoms 列表中的每一项只写症状名称，不要包含"轻度""中度""重度"等程度修饰词
- 程度信息（如"轻度""中度""重度"）请填写到 severity 字段中，如 {{"头疼": "轻度"}}
- 如果没有程度信息，severity 返回空对象

只返回JSON，不要其他内容。"""

    @staticmethod
    def _extract_json_from_response(response: str) -> str:
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json_match.group(0)
        if response.strip().startswith('{'):
            return response.strip()
        raise ExtractionError("无法从响应中提取JSON")
