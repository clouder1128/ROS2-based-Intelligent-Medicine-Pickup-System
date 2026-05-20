"""结构化表单模型 - 多轮症状收集的数据模型和增量提取逻辑"""

import json
import re
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Set, Tuple

from .models import StructuredSymptoms
from .extractor import SymptomExtractor

logger = logging.getLogger(__name__)


# ==================== 数据模型 ====================

@dataclass
class PatientDemographics:
    age: Optional[float] = None
    age_unit: Optional[str] = None          # 岁/月/天
    weight_kg: Optional[float] = None
    gender: Optional[str] = None            # 男/女/不愿透露
    pregnant: Optional[str] = None          # 是/否/未知/哺乳期
    gestational_weeks: Optional[int] = None
    breastfeeding: Optional[bool] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}

    def is_empty(self) -> bool:
        return all(v is None for v in self.__dict__.values())


@dataclass
class SymptomEntry:
    location: Optional[str] = None
    quality: Optional[str] = None
    severity_0_10: Optional[int] = None
    onset_time: Optional[str] = None
    duration: Optional[str] = None
    pattern: Optional[str] = None            # 持续性/间歇性/夜间加重等
    trigger_factors: Optional[str] = None
    relieving_factors: Optional[str] = None
    accompanying_symptoms: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {}
        for k, v in self.__dict__.items():
            if v is not None and v != []:
                d[k] = v
        return d


@dataclass
class VitalSigns:
    temperature_c: Optional[float] = None
    has_fever: Optional[str] = None
    fever_duration_days: Optional[float] = None
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    heart_rate_bpm: Optional[int] = None
    respiratory_rate: Optional[int] = None
    oxygen_saturation: Optional[float] = None
    skin_rash: Optional[str] = None
    rash_description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class MedicalHistory:
    chronic_diseases: List[str] = field(default_factory=list)
    has_liver_disease: Optional[str] = None
    has_kidney_disease: Optional[str] = None
    has_peptic_ulcer: Optional[str] = None
    has_gi_bleeding: Optional[str] = None
    has_epilepsy: Optional[str] = None
    has_glaucoma: Optional[str] = None
    has_prostate_hyperplasia: Optional[str] = None
    has_thyroid_disease: Optional[str] = None
    has_heart_failure: Optional[str] = None
    has_arrhythmia: Optional[str] = None
    has_bleeding_disorder: Optional[str] = None
    recent_surgery: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {}
        for k, v in self.__dict__.items():
            if v is not None and v != []:
                d[k] = v
        return d


@dataclass
class MedicationRecord:
    medication_name: str = ""
    route: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    indication: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    effectiveness: Optional[str] = None
    adverse_reaction: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"medication_name": self.medication_name}
        for k, v in self.__dict__.items():
            if v is not None and k != "medication_name":
                d[k] = v
        return d

    def is_valid(self) -> bool:
        return bool(self.medication_name)


@dataclass
class AllergyInfo:
    drug_allergies: List[str] = field(default_factory=list)
    food_allergies: List[str] = field(default_factory=list)
    excipient_allergies: List[str] = field(default_factory=list)
    other_intolerances: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v}


@dataclass
class SocialHistory:
    occupation: Optional[str] = None
    need_operate_machinery: Optional[bool] = None
    alcohol_use: Optional[str] = None
    smoking_status: Optional[str] = None
    special_diet: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class PatientExpectation:
    patient_goal: Optional[str] = None
    preferred_drug_type: Optional[str] = None
    preferred_formulation: Optional[str] = None
    cost_constraint: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class RedFlags:
    high_fever: Optional[bool] = None
    severe_headache: Optional[bool] = None
    chest_pain: Optional[bool] = None
    dyspnea: Optional[bool] = None
    altered_mental: Optional[bool] = None
    bleeding: Optional[bool] = None
    anaphylaxis: Optional[bool] = None
    child_or_elderly_frail: Optional[bool] = None
    pregnancy_with_alarm: Optional[bool] = None
    other_red_flags: Optional[str] = None

    def any_active(self) -> bool:
        return any(
            getattr(self, f.name) is True
            for f in self.__class__.__dataclass_fields__.values()
        )

    def active_list(self) -> List[str]:
        return [
            f.name for f in self.__class__.__dataclass_fields__.values()
            if getattr(self, f.name) is True
        ]

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class Question:
    """可点击问题的结构化表示"""
    text: str
    field: str
    options: List[str]
    allow_multiple: bool = False
    allow_custom: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "field": self.field,
            "options": self.options,
            "allow_multiple": self.allow_multiple,
            "allow_custom": self.allow_custom,
        }


BASICS_REQUIRED_FIELDS: List[str] = [
    "patient.age",
    "patient.weight_kg",
    "patient.gender",
    "allergies.drug_allergies",
    "current_medications",
]


@dataclass
class ConsultationForm:
    """顶层表单模型，聚合所有子结构"""

    # 结构化数据
    patient: PatientDemographics = field(default_factory=PatientDemographics)
    symptoms: List[SymptomEntry] = field(default_factory=list)
    chief_complaint: Optional[str] = None
    vital_signs: VitalSigns = field(default_factory=VitalSigns)
    medical_history: MedicalHistory = field(default_factory=MedicalHistory)
    current_medications: List[MedicationRecord] = field(default_factory=list)
    self_medicated: List[MedicationRecord] = field(default_factory=list)
    long_term_medications: List[MedicationRecord] = field(default_factory=list)
    allergies: AllergyInfo = field(default_factory=AllergyInfo)
    social: SocialHistory = field(default_factory=SocialHistory)
    expectation: PatientExpectation = field(default_factory=PatientExpectation)
    red_flags: RedFlags = field(default_factory=RedFlags)
    supplements: Dict[str, Any] = field(default_factory=dict)
    supplementary: Dict[str, Any] = field(default_factory=dict)

    # 进度追踪
    filled_fields: Set[str] = field(default_factory=set)
    skipped_fields: Set[str] = field(default_factory=set)
    phase: str = "basics_collection"
    confirmed: bool = False
    conversation_log: List[Dict[str, str]] = field(default_factory=list)

    def to_summary(self) -> str:
        """生成供 LLM 使用的文本摘要（已收集的信息概览）"""
        parts = []

        if not self.patient.is_empty():
            p = self.patient
            info = []
            if p.age is not None:
                unit = p.age_unit or "岁"
                info.append(f"年龄：{p.age}{unit}")
            if p.weight_kg is not None:
                info.append(f"体重：{p.weight_kg}kg")
            if p.gender:
                info.append(f"性别：{p.gender}")
            if p.pregnant:
                info.append(f"怀孕/哺乳：{p.pregnant}")
                if p.gestational_weeks:
                    info.append(f"孕周：{p.gestational_weeks}")
            if info:
                parts.append("【患者信息】" + "、".join(info))

        if self.chief_complaint:
            parts.append(f"【主诉】{self.chief_complaint}")

        if self.symptoms:
            for i, s in enumerate(self.symptoms):
                desc = []
                if s.location:
                    desc.append(f"部位：{s.location}")
                if s.quality:
                    desc.append(f"性质：{s.quality}")
                if s.severity_0_10 is not None:
                    desc.append(f"程度：{s.severity_0_10}/10")
                if s.duration:
                    desc.append(f"持续：{s.duration}")
                if s.onset_time:
                    desc.append(f"起病：{s.onset_time}")
                if s.accompanying_symptoms:
                    desc.append(f"伴随：{'、'.join(s.accompanying_symptoms)}")
                if desc:
                    parts.append(f"【症状{i+1}】{'，'.join(desc)}")

        if self.allergies.drug_allergies:
            parts.append(f"【药物过敏】{'、'.join(self.allergies.drug_allergies)}")
        elif "allergies.drug_allergies" in self.filled_fields:
            parts.append("【药物过敏】无已知过敏")

        vs = self.vital_signs
        if vs.temperature_c is not None:
            parts.append(f"【体温】{vs.temperature_c}℃")
        if vs.heart_rate_bpm is not None:
            parts.append(f"【心率】{vs.heart_rate_bpm}bpm")

        if self.medical_history.chronic_diseases:
            parts.append(f"【慢性病史】{'、'.join(self.medical_history.chronic_diseases)}")

        if self.current_medications:
            names = [m.medication_name for m in self.current_medications if m.is_valid()]
            if names:
                parts.append(f"【当前用药】{'、'.join(names)}")

        rf = self.red_flags
        active = rf.active_list()
        if active:
            parts.append(f"【警示信号】{'、'.join(active)}")

        if self.supplementary:
            supp_parts = [f"{k}: {v}" for k, v in self.supplementary.items()]
            parts.append(f"【附加信息】{'、'.join(supp_parts)}")

        return "\n".join(parts) if parts else "暂无已收集信息"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "patient": self.patient.to_dict(),
            "symptoms": [s.to_dict() for s in self.symptoms],
            "chief_complaint": self.chief_complaint,
            "vital_signs": self.vital_signs.to_dict(),
            "medical_history": self.medical_history.to_dict(),
            "current_medications": [m.to_dict() for m in self.current_medications if m.is_valid()],
            "self_medicated": [m.to_dict() for m in self.self_medicated if m.is_valid()],
            "long_term_medications": [m.to_dict() for m in self.long_term_medications if m.is_valid()],
            "allergies": self.allergies.to_dict(),
            "social": self.social.to_dict(),
            "expectation": self.expectation.to_dict(),
            "red_flags": self.red_flags.to_dict(),
            "supplementary": self.supplementary,
            "filled_fields": list(self.filled_fields),
            "phase": self.phase,
            "confirmed": self.confirmed,
        }


# ==================== 字段规则 ====================

GLOBAL_REQUIRED_FIELDS: List[str] = [
    "patient.age",
    "patient.weight_kg",
    "patient.gender",
    "allergies.drug_allergies",
    "current_medications",
    "chief_complaint",
]

SYMPTOM_CORE_FIELDS: List[str] = [
    "symptoms[].location",
    "symptoms[].quality",
    "symptoms[].severity_0_10",
    "symptoms[].onset_time",
]

RED_FLAG_FIELDS: List[str] = [
    "red_flags.high_fever",
    "red_flags.severe_headache",
    "red_flags.chest_pain",
    "red_flags.dyspnea",
    "red_flags.altered_mental",
    "red_flags.bleeding",
    "red_flags.anaphylaxis",
    "red_flags.child_or_elderly_frail",
    "red_flags.pregnancy_with_alarm",
]

# 按生理系统 → 需要额外采集的字段
SYSTEM_TRIGGERED_FIELDS: Dict[str, List[str]] = {
    "全身症状": [
        "vital_signs.temperature_c",
        "vital_signs.fever_duration_days",
    ],
    "呼吸系统": [
        "vital_signs.temperature_c",
        "vital_signs.has_fever",
        "social.smoking_status",
    ],
    "消化系统": [
        "medical_history.has_peptic_ulcer",
        "medical_history.has_gi_bleeding",
        "social.alcohol_use",
    ],
    "神经系统": [
        "medical_history.has_epilepsy",
        "social.need_operate_machinery",
    ],
    "疼痛": [
        "medical_history.has_peptic_ulcer",
        "medical_history.has_gi_bleeding",
        "medical_history.has_kidney_disease",
    ],
    "皮肤": [
        "allergies.drug_allergies",
        "allergies.food_allergies",
    ],
    "泌尿系统": [
        "medical_history.has_kidney_disease",
    ],
}

# 症状关键词 → 生理系统映射
SYMPTOM_TO_SYSTEM: Dict[str, List[str]] = {
    "发热": ["全身症状"], "发烧": ["全身症状"], "乏力": ["全身症状"],
    "盗汗": ["全身症状"], "寒战": ["全身症状"],
    "咳嗽": ["呼吸系统"], "咳痰": ["呼吸系统"], "咽痛": ["呼吸系统"],
    "喉咙痛": ["呼吸系统"], "流鼻涕": ["呼吸系统"], "鼻塞": ["呼吸系统"],
    "呼吸困难": ["呼吸系统"], "气喘": ["呼吸系统"],
    "腹痛": ["消化系统"], "腹泻": ["消化系统"], "恶心": ["消化系统"],
    "呕吐": ["消化系统"], "胃痛": ["消化系统"], "胃酸": ["消化系统"],
    "反酸": ["消化系统"], "便秘": ["消化系统"], "腹胀": ["消化系统"],
    "头痛": ["神经系统", "疼痛"], "头疼": ["神经系统", "疼痛"],
    "头晕": ["神经系统"], "眩晕": ["神经系统"], "失眠": ["神经系统"],
    "肌肉酸痛": ["疼痛"], "关节痛": ["疼痛"], "背痛": ["疼痛"],
    "皮疹": ["皮肤"], "皮痒": ["皮肤"], "湿疹": ["皮肤"],
    "荨麻疹": ["皮肤"],
    "尿频": ["泌尿系统"], "尿痛": ["泌尿系统"], "尿急": ["泌尿系统"],
}

# 风险条件 → 需采集的额外字段
# 每条：(条件描述, 检查函数, 字段列表)
RiskCondition = Tuple[str, str, List[str]]
# ^ (label for prompt, field_name_to_check, required_fields_if_true)

RISK_TRIGGERED_FIELDS: List[RiskCondition] = [
    ("年龄<12岁", "patient.age < 12", ["patient.weight_kg"]),
    ("年龄>75岁", "patient.age > 75", ["medical_history.has_liver_disease", "medical_history.has_kidney_disease"]),
    ("女性", "gender_female", ["patient.pregnant"]),
    ("有慢性病史", "chronic_diseases_not_empty", ["current_medications", "long_term_medications"]),
    ("需操作机械/驾驶", "social.need_operate_machinery", ["social.occupation"]),
]

# 字段 → 可点击选项映射（用于 Round 3+ 追问）
FIELD_OPTIONS: Dict[str, Dict[str, Any]] = {
    "patient.gender": {"options": ["男", "女", "不愿透露"], "type": "single", "allow_custom": False},
    "patient.pregnant": {"options": ["是", "否", "未知", "哺乳期"], "type": "single", "allow_custom": False},
    "vital_signs.has_fever": {"options": ["是", "否"], "type": "single", "allow_custom": False},
    "social.smoking_status": {"options": ["从不吸烟", "已戒烟", "偶尔吸烟", "每天吸烟"], "type": "single", "allow_custom": True},
    "social.alcohol_use": {"options": ["不饮酒", "偶尔饮酒", "每天饮酒"], "type": "single", "allow_custom": True},
    "social.need_operate_machinery": {"options": ["是", "否"], "type": "single", "allow_custom": False},
    "medical_history.has_peptic_ulcer": {"options": ["是", "否"], "type": "single", "allow_custom": False},
    "medical_history.has_gi_bleeding": {"options": ["是", "否"], "type": "single", "allow_custom": False},
    "medical_history.has_kidney_disease": {"options": ["是", "否"], "type": "single", "allow_custom": False},
    "medical_history.has_liver_disease": {"options": ["是", "否"], "type": "single", "allow_custom": False},
    "medical_history.has_epilepsy": {"options": ["是", "否"], "type": "single", "allow_custom": False},
    "medical_history.has_glaucoma": {"options": ["是", "否"], "type": "single", "allow_custom": False},
    "medical_history.has_prostate_hyperplasia": {"options": ["是", "否"], "type": "single", "allow_custom": False},
    "medical_history.has_thyroid_disease": {"options": ["是", "否"], "type": "single", "allow_custom": False},
    "medical_history.has_heart_failure": {"options": ["是", "否"], "type": "single", "allow_custom": False},
    "medical_history.has_arrhythmia": {"options": ["是", "否"], "type": "single", "allow_custom": False},
    "medical_history.has_bleeding_disorder": {"options": ["是", "否"], "type": "single", "allow_custom": False},
    "red_flags.high_fever": {"options": ["是", "否"], "type": "single", "allow_custom": False},
    "red_flags.severe_headache": {"options": ["是", "否"], "type": "single", "allow_custom": False},
    "red_flags.chest_pain": {"options": ["是", "否"], "type": "single", "allow_custom": False},
    "red_flags.dyspnea": {"options": ["是", "否"], "type": "single", "allow_custom": False},
    "red_flags.altered_mental": {"options": ["是", "否"], "type": "single", "allow_custom": False},
    "red_flags.bleeding": {"options": ["是", "否"], "type": "single", "allow_custom": False},
    "red_flags.anaphylaxis": {"options": ["是", "否"], "type": "single", "allow_custom": False},
    "medical_history.chronic_diseases": {
        "options": ["高血压", "糖尿病", "肝病", "肾病", "胃溃疡", "癫痫", "青光眼", "甲状腺病", "心脏病", "以上都没有"],
        "type": "multiple", "allow_custom": True,
    },
}

# 基础必填字段是否已收集
def basics_are_filled(form: Optional[ConsultationForm]) -> bool:
    """检查基础信息（Round 1 表单）是否已填写"""
    if form is None:
        return False
    for field in BASICS_REQUIRED_FIELDS:
        if field not in form.filled_fields:
            return False
    return True


# ==================== 问卷式基础信息采集 ====================

BASICS_QUESTIONS = [
    {
        "field": "patient.gender",
        "text": "请问您的性别是？",
        "options": [
            {"label": "男", "value": "男"},
            {"label": "女", "value": "女"},
        ],
        "allow_custom": False,
    },
    {
        "field": "patient.age",
        "text": "请问您的年龄是？",
        "options": [],
        "allow_custom": True,
    },
    {
        "field": "patient.weight_kg",
        "text": "请问您的体重是多少公斤？（如您知道斤数，可在数字后加单位，如\"70公斤\"或\"140斤\"）",
        "options": [],
        "allow_custom": True,
    },
    {
        "field": "allergies.drug_allergies",
        "text": "请问您是否有药物过敏史？",
        "options": [
            {"label": "无过敏", "value": ""},
            {"label": "有过敏，请填写", "value": "__custom__"},
        ],
        "allow_custom": True,
    },
    {
        "field": "current_medications",
        "text": "请问您目前是否在服用其他药物？",
        "options": [
            {"label": "无用药", "value": ""},
            {"label": "有用药，请填写", "value": "__custom__"},
        ],
        "allow_custom": True,
    },
]


def generate_basics_question(form: ConsultationForm) -> Optional[Question]:
    """返回下一个未填写的基础信息问题，全部填完则返回 None"""
    for q_def in BASICS_QUESTIONS:
        field = q_def["field"]
        if field not in form.filled_fields:
            return Question(
                text=q_def["text"],
                field=field,
                options=q_def.get("options", []),
                allow_multiple=q_def.get("allow_multiple", False),
                allow_custom=q_def.get("allow_custom", False),
            )
    return None


# ==================== 风险条件检查函数 ====================

def _check_risk_condition(condition_key: str, form: ConsultationForm) -> bool:
    """检查风险条件是否满足"""
    if condition_key == "patient.age < 12":
        return form.patient.age is not None and form.patient.age < 12
    elif condition_key == "patient.age > 75":
        return form.patient.age is not None and form.patient.age > 75
    elif condition_key == "gender_female":
        return form.patient.gender == "女"
    elif condition_key == "chronic_diseases_not_empty":
        return len(form.medical_history.chronic_diseases) > 0
    elif condition_key == "social.need_operate_machinery":
        return form.social.need_operate_machinery is True
    return False


# ==================== 字段路径访问工具 ====================

def get_field_value(form: ConsultationForm, field_path: str) -> Any:
    """按点号路径访问表单字段值，如 'patient.age'、'red_flags.high_fever'"""
    parts = field_path.split(".")
    obj = form
    for part in parts:
        if part.endswith("[]"):
            # 列表字段：检查是否有元素
            lst = getattr(obj, part[:-2], [])
            if not lst:
                return None
        if hasattr(obj, part):
            obj = getattr(obj, part)
        else:
            return None
    return obj


def is_field_filled(form: ConsultationForm, field_path: str) -> bool:
    """判断字段是否已填写"""
    # 在 filled_fields 中直接查找
    if field_path in form.filled_fields:
        return True

    # 特殊：症状核心字段检查是否有至少一个症状被完整记录
    if field_path in SYMPTOM_CORE_FIELDS and form.symptoms:
        for s in form.symptoms:
            val = _get_symptom_field(s, field_path)
            if val is not None and val != []:
                return True
        return False

    # 特殊：红色警报字段全部检查
    if field_path == "red_flags.*":
        return all(is_field_filled(form, rf) for rf in RED_FLAG_FIELDS)

    # 通用路径检查
    val = get_field_value(form, field_path)
    if val is None or val == [] or val == "" or val is False:
        return False
    return True


def _get_symptom_field(symptom: SymptomEntry, field_path: str) -> Any:
    """从 SymptomEntry 获取字段值"""
    mapping = {
        "symptoms[].location": symptom.location,
        "symptoms[].quality": symptom.quality,
        "symptoms[].severity_0_10": symptom.severity_0_10,
        "symptoms[].onset_time": symptom.onset_time,
        "symptoms[].duration": symptom.duration,
    }
    return mapping.get(field_path)


# ==================== 系统分析 ====================

def analyze_chief_complaint(chief_complaint: Optional[str], symptoms: List[SymptomEntry]) -> List[str]:
    """根据主诉和症状判断涉及的生理系统"""
    affected = set()

    text = (chief_complaint or "").lower()

    # 从症状条目中提取关键词
    for s in symptoms:
        if s.location:
            text += " " + s.location.lower()
        if s.quality:
            text += " " + s.quality.lower()
        if s.accompanying_symptoms:
            text += " " + " ".join(s.accompanying_symptoms)

    # 关键词匹配
    for keyword, systems in SYMPTOM_TO_SYSTEM.items():
        if keyword in text:
            affected.update(systems)

    return list(affected)


def any_red_flag_active(form: ConsultationForm) -> bool:
    """检查是否有红色警报被触发"""
    return form.red_flags.any_active()


# ==================== 完整性检查 ====================

def check_form_completeness(form: ConsultationForm) -> Dict[str, Any]:
    """检查表单完整性，返回缺失字段信息"""
    result: Dict[str, Any] = {
        "complete": False,
        "missing_global": [],
        "missing_symptom_core": [],
        "missing_conditional": [],
        "phase": "continue",  # continue | needs_confirmation | red_flag
    }

    # 1. 红色警报检查
    if any_red_flag_active(form):
        result["phase"] = "red_flag"
        return result

    # 2. 全局必填字段检查
    for field in GLOBAL_REQUIRED_FIELDS:
        if not is_field_filled(form, field):
            result["missing_global"].append(field)

    # 3. 症状核心字段检查（如果有主诉或症状）
    if form.chief_complaint or form.symptoms:
        for field in SYMPTOM_CORE_FIELDS:
            if not is_field_filled(form, field):
                result["missing_symptom_core"].append(field)

    # 4. 条件必填 - 按生理系统
    affected_systems = analyze_chief_complaint(form.chief_complaint, form.symptoms)
    for system in affected_systems:
        for field in SYSTEM_TRIGGERED_FIELDS.get(system, []):
            if field not in form.filled_fields:
                val = get_field_value(form, field)
                if val is None or val == []:
                    result["missing_conditional"].append(field)

    # 5. 风险触发字段
    for _, condition_key, fields in RISK_TRIGGERED_FIELDS:
        if _check_risk_condition(condition_key, form):
            for field in fields:
                if not is_field_filled(form, field):
                    result["missing_conditional"].append(field)

    # 6. 红色警报字段检查（核心警示信号至少问过）
    for field in RED_FLAG_FIELDS:
        if not is_field_filled(form, field):
            result["missing_conditional"].append(field)

    # 去重
    result["missing_conditional"] = list(set(result["missing_conditional"]))

    # 7. 判断阶段
    if not result["missing_global"] and not result["missing_symptom_core"]:
        result["complete"] = True
        result["phase"] = "needs_confirmation"

    return result


# ==================== 追问生成 ====================

FIELD_QUESTIONS: Dict[str, str] = {
    "patient.age": "请问您的年龄是多少？",
    "patient.weight_kg": "请问您的体重是多少公斤（或斤）？",
    "patient.gender": "请问您的性别是？",
    "patient.pregnant": "请问您是否怀孕或处于哺乳期？",
    "allergies.drug_allergies": "您是否有药物过敏史？",
    "current_medications": "您近期有在服用其他药物吗（包括处方药、非处方药或保健品）？",
    "chief_complaint": "请描述您最主要的症状是什么？",
    "symptoms[].location": "具体是哪个部位不舒服？",
    "symptoms[].quality": "这种不适感是什么性质的（如钝痛、刺痛、烧灼感、瘙痒等）？",
    "symptoms[].severity_0_10": "如果用0到10分来描述，您的不适程度是几分（0分无症状，10分最严重）？",
    "symptoms[].onset_time": "这些症状是什么时候开始的？",
    "vital_signs.temperature_c": "您最近测量过体温吗？多少度？",
    "vital_signs.has_fever": "您是否发烧？",
    "vital_signs.fever_duration_days": "发烧持续几天了？",
    "social.smoking_status": "您有吸烟的习惯吗？",
    "social.alcohol_use": "您有饮酒习惯吗？",
    "medical_history.has_peptic_ulcer": "您有胃溃疡或消化道溃疡的病史吗？",
    "medical_history.has_gi_bleeding": "您有过消化道出血的经历吗？",
    "medical_history.has_kidney_disease": "您有肾脏疾病史吗？",
    "medical_history.has_liver_disease": "您有肝脏疾病史吗？",
    "medical_history.has_epilepsy": "您有癫痫病史吗？",
    "social.need_operate_machinery": "您的职业是否需要操作机械或驾驶车辆？",
    "allergies.food_allergies": "您是否有食物过敏史？",
    "red_flags.high_fever": "您有高烧（体温≥39.5℃）持续超过48小时的情况吗？",
    "red_flags.severe_headache": "您是否有剧烈头痛伴有颈部僵硬或呕吐？",
    "red_flags.chest_pain": "您是否有胸痛并放射到左肩或下巴？",
    "red_flags.dyspnea": "您是否有呼吸困难、嘴唇发紫或无法完整说话的情况？",
    "red_flags.altered_mental": "您是否有意识模糊、嗜睡或胡言乱语的情况？",
    "red_flags.bleeding": "您是否有呕血、黑便、咳血或大片瘀斑？",
    "red_flags.anaphylaxis": "您是否有皮疹迅速扩散、喉头水肿或声音嘶哑的情况？",
    "red_flags.child_or_elderly_frail": "患者是儿童（<3岁）或高龄老人（>75岁）且一般情况较差吗？",
    "red_flags.pregnancy_with_alarm": "如果是孕妇，是否伴有严重症状？",
}


def generate_follow_up(
    form: ConsultationForm,
    missing_global: List[str],
    missing_symptom: List[str],
    missing_conditional: List[str],
    llm_client=None,
) -> Dict[str, Any]:
    """生成追问文本 + 可点击选项

    返回结构：
    {
        "text": "追问文本...",
        "questions": [{"text": "...", "field": "...", "options": [...], ...}]
    }
    策略：
    - 优先追问全局必填缺失（每次1-2项）
    - 其次追问症状核心字段
    - 最后追问条件必填（优先使用可点击选项）
    - 已收集的信息在追问中自然引用
    """
    summary = form.to_summary()
    has_collected = bool(summary.strip() and summary != "暂无已收集信息")

    candidates = []

    if missing_global:
        priority = ["patient.age", "patient.weight_kg", "patient.gender",
                     "patient.pregnant", "allergies.drug_allergies",
                     "current_medications", "chief_complaint"]
        for p in priority:
            if p in missing_global:
                candidates.append(p)
                if len(candidates) >= 2:
                    break

    if not candidates and missing_symptom:
        priority = ["symptoms[].location", "symptoms[].quality",
                     "symptoms[].severity_0_10", "symptoms[].onset_time"]
        for p in priority:
            if p in missing_symptom:
                candidates.append(p)
                if len(candidates) >= 2:
                    break

    if not candidates and missing_conditional:
        priority = [
            "red_flags.high_fever", "red_flags.dyspnea", "red_flags.chest_pain",
            "vital_signs.temperature_c",
            "medical_history.has_peptic_ulcer",
            "social.smoking_status",
        ]
        for p in priority:
            if p in missing_conditional:
                candidates.append(p)
                break
        if not candidates:
            candidates = missing_conditional[:1]

    if not candidates:
        return {"text": "请提供更多关于您症状的信息。", "questions": []}

    # 构造追问
    parts = []
    if has_collected:
        parts.append(f"已收集到以下信息：\n{summary}\n")

    questions_data = []
    for field in candidates:
        question_text = FIELD_QUESTIONS.get(field, f"请提供您的{field}信息：")
        parts.append(question_text)
        # 如果该字段有预定义选项，生成可点击 Question
        if field in FIELD_OPTIONS:
            opts = FIELD_OPTIONS[field]
            q = Question(
                text=question_text,
                field=field,
                options=opts["options"],
                allow_multiple=(opts.get("type") == "multiple"),
                allow_custom=opts.get("allow_custom", False),
            )
            questions_data.append(q.to_dict())

    return {
        "text": "\n".join(parts),
        "questions": questions_data,
    }


# ==================== 总结报告生成 ====================

def generate_form_summary(form: ConsultationForm) -> str:
    """生成结构化总结报告供用户确认"""
    lines = ["━━━━━━━━━━━━━━━━━━━━━━", "📋 诊断信息汇总", ""]

    # 患者信息
    p = form.patient
    patient_info = []
    if p.age is not None:
        unit = p.age_unit or "岁"
        patient_info.append(f"年龄：{p.age}{unit}")
    if p.gender:
        patient_info.append(f"性别：{p.gender}")
    if p.weight_kg is not None:
        patient_info.append(f"体重：{p.weight_kg}kg")
    if p.pregnant:
        patient_info.append(f"怀孕/哺乳：{p.pregnant}")
    if patient_info:
        lines.append("👤 患者信息")
        for info in patient_info:
            lines.append(f"  · {info}")
        lines.append("")

    # 症状信息
    if form.chief_complaint:
        lines.append("🩺 主诉")
        lines.append(f"  · {form.chief_complaint}")
        lines.append("")

    if form.symptoms:
        lines.append("🩺 症状详情")
        for i, s in enumerate(form.symptoms):
            desc = []
            if s.location:
                desc.append(f"部位：{s.location}")
            if s.quality:
                desc.append(f"性质：{s.quality}")
            if s.severity_0_10 is not None:
                desc.append(f"程度：{s.severity_0_10}/10分")
            if s.duration:
                desc.append(f"持续：{s.duration}")
            if s.onset_time:
                desc.append(f"起病：{s.onset_time}")
            if s.accompanying_symptoms:
                desc.append(f"伴随症状：{'、'.join(s.accompanying_symptoms)}")
            if s.pattern:
                desc.append(f"模式：{s.pattern}")
            if desc:
                lines.append(f"  [{i+1}] {'，'.join(desc)}")
        lines.append("")

    # 过敏史
    if form.allergies.drug_allergies or "allergies.drug_allergies" in form.filled_fields:
        lines.append("💊 过敏史")
        if form.allergies.drug_allergies:
            lines.append(f"  · 药物过敏：{'、'.join(form.allergies.drug_allergies)}")
        else:
            lines.append("  · 药物过敏：无已知过敏")
        lines.append("")

    # 用药情况
    if form.current_medications:
        lines.append("💊 当前用药")
        for m in form.current_medications:
            if m.is_valid():
                lines.append(f"  · {m.medication_name}")
        lines.append("")

    # 既往病史
    mh = form.medical_history
    if mh.chronic_diseases:
        lines.append("📋 既往病史")
        lines.append(f"  · 慢性病：{'、'.join(mh.chronic_diseases)}")
        lines.append("")

    # 生命体征
    vs = form.vital_signs
    if vs.temperature_c is not None or vs.heart_rate_bpm is not None:
        lines.append("📊 生命体征")
        if vs.temperature_c is not None:
            lines.append(f"  · 体温：{vs.temperature_c}℃")
        if vs.heart_rate_bpm is not None:
            lines.append(f"  · 心率：{vs.heart_rate_bpm}bpm")
        lines.append("")

    # 缺失信息提示
    completeness = check_form_completeness(form)
    if completeness["missing_global"] or completeness["missing_symptom_core"] or completeness["missing_conditional"]:
        lines.append("⚠️ 以下信息尚未收集（不影响确认，但可能影响推荐准确性）：")
        for f in completeness["missing_conditional"]:
            label = FIELD_QUESTIONS.get(f, f)
            lines.append(f"  · {label}")
        lines.append("")

    # 确认提示
    lines.extend([
        "━━━━━━━━━━━━━━━━━━━━━━",
        "请确认以上信息是否准确？",
        "  · 如正确，请回复「确认」或「正确」",
        "  · 如需修改，请指出需要修改的项目",
        "━━━━━━━━━━━━━━━━━━━━━━",
    ])

    return "\n".join(lines)


# ==================== 增量提取器 ====================

EXTRACTION_SYSTEM_PROMPT = """你是一名医疗信息提取专家。

当前患者的诊断表单中已有以下信息（已确认的内容，请勿重复提取）：
{form_summary}

请从患者的最新回复中提取新增或修改的医疗信息。
如果某字段在已有信息中已被确认、且最新回复没有修改它，请返回 null。

重要规则：只提取患者明确提到的信息。不要猜测、推断或默认填充任何患者未说出的值。
例如：患者没有提及性别时，gender 必须返回 null，不能默认填"男"。
同样适用于年龄、体重、过敏史等所有字段——未提及则返回 null。

请严格按照以下 JSON 格式返回结果（未获取的信息返回 null）：

{{
    "patient": {{
        "age": 数值或null,
        "age_unit": "岁/月/天"或null,
        "weight_kg": 数值或null（如用户说"斤"，请÷2转换为公斤）,
        "gender": "男/女/不愿透露"或null,
        "pregnant": "是/否/未知/哺乳期"或null,
        "gestational_weeks": 数值或null,
        "breastfeeding": true/false或null
    }},
    "chief_complaint": "主诉文本"或null,
    "symptoms": [
        {{
            "location": "部位"或null,
            "quality": "性质"或null,
            "severity_0_10": 数值或null,
            "onset_time": "起病时间"或null,
            "duration": "持续时间"或null,
            "pattern": "时间模式"或null,
            "trigger_factors": "诱发因素"或null,
            "relieving_factors": "缓解因素"或null,
            "accompanying_symptoms": ["伴随症状1", "伴随症状2"]或null
        }}
    ],
    "vital_signs": {{
        "temperature_c": 数值或null,
        "has_fever": "是/否"或null,
        "fever_duration_days": 数值或null,
        "blood_pressure_systolic": 数值或null,
        "blood_pressure_diastolic": 数值或null,
        "heart_rate_bpm": 数值或null,
        "respiratory_rate": 数值或null,
        "oxygen_saturation": 数值或null,
        "skin_rash": "是/否"或null,
        "rash_description": "描述"或null
    }},
    "medical_history": {{
        "chronic_diseases": ["慢性病1", "慢性病2"]或null,
        "has_liver_disease": "是/否"或null,
        "has_kidney_disease": "是/否"或null,
        "has_peptic_ulcer": "是/否"或null,
        "has_gi_bleeding": "是/否"或null,
        "has_epilepsy": "是/否"或null,
        "has_glaucoma": "是/否"或null,
        "has_prostate_hyperplasia": "是/否"或null,
        "has_thyroid_disease": "是/否"或null,
        "has_heart_failure": "是/否"或null,
        "has_arrhythmia": "是/否"或null,
        "has_bleeding_disorder": "是/否"或null,
        "recent_surgery": "是/否 + 部位"或null
    }},
    "current_medications": [
        {{"medication_name": "药名", "dosage": "剂量", "frequency": "频率", "indication": "用途"}}
    ],
    "self_medicated": [
        {{"medication_name": "药名", "dosage": "剂量", "frequency": "频率", "effectiveness": "效果"}}
    ],
    "long_term_medications": [
        {{"medication_name": "药名", "dosage": "剂量", "frequency": "频率"}}
    ],
    "allergies": {{
        "drug_allergies": ["青霉素，皮疹", "阿司匹林，哮喘"]或null,
        "food_allergies": ["花生", "牛奶"]或null,
        "excipient_allergies": ["乳糖"]或null,
        "other_intolerances": ["酒精"]或null
    }},
    "social": {{
        "occupation": "职业"或null,
        "need_operate_machinery": true/false或null,
        "alcohol_use": "不饮酒/偶尔/每日"或null,
        "smoking_status": "从不/既往/当前"或null
    }},
    "expectation": {{
        "patient_goal": "患者希望解决的问题"或null,
        "preferred_drug_type": "偏好药物类型"或null,
        "preferred_formulation": "偏好剂型"或null,
        "cost_constraint": "费用敏感度"或null
    }},
    "red_flags": {{
        "high_fever": true/false或null,
        "severe_headache": true/false或null,
        "chest_pain": true/false或null,
        "dyspnea": true/false或null,
        "altered_mental": true/false或null,
        "bleeding": true/false或null,
        "anaphylaxis": true/false或null,
        "child_or_elderly_frail": true/false或null,
        "pregnancy_with_alarm": true/false或null,
        "other_red_flags": "描述"或null
    }}
}}

注意：
- symptoms 是一个列表，每条记录一个症状的完整描述
- current_medications/self_medicated/long_term_medications 的每项必须有 medication_name
- 如果患者明确说"没有过敏"或"无过敏"，请在 drug_allergies 中返回空列表 []
- 如果患者明确说"没吃药"或"没有用药"，请在 current_medications 中返回空列表 []
- 只返回 JSON，不要其他内容。"""


class IncrementalExtractor:
    """增量提取器 - 包装现有 SymptomExtractor，增加合并逻辑"""

    def __init__(self, llm_client=None):
        self.llm_client = llm_client

    def extract_and_merge(self, form: ConsultationForm, user_message: str) -> ConsultationForm:
        """从用户新消息中提取信息并合并到现有表单"""
        if not user_message or not user_message.strip():
            return form

        try:
            extracted = self._llm_extract(user_message, form)
            if extracted:
                # 快照合并前的 filled_fields，用于判断哪些字段是本轮新增的
                prev_filled = set(form.filled_fields)
                self._merge(extracted, form)
                newly_set = form.filled_fields - prev_filled
                # 后处理校验：只校验本轮新增字段，不碰之前已确认的字段
                self._validate_no_inference(form, user_message, newly_set)

                # Fallback: LLM 检测到症状（symptoms 非空）但未提取 chief_complaint
                # → 用原始消息作为主诉（避免无限追问 chief_complaint）
                if (not form.chief_complaint
                        and "chief_complaint" not in form.filled_fields
                        and extracted.get("symptoms")):
                    form.chief_complaint = user_message
                    form.filled_fields.add("chief_complaint")
                    logger.info("Fallback: set chief_complaint='%s' from symptom detection",
                                user_message[:60])
        except Exception as e:
            logger.warning(f"LLM增量提取失败，降级处理: {e}")
            # 降级：使用旧的规则提取器提取基本信息
            self._fallback_extract(user_message, form)

        return form

    @staticmethod
    def _validate_no_inference(form: ConsultationForm, user_message: str, newly_set_fields: set = None) -> None:
        """校验本轮新增字段：如果值在用户消息中没有明确提及，移除推断值

        Args:
            newly_set_fields: 本轮合并中新添加的 filled_fields 集合。
                只校验这些字段，避免清除之前轮次已确认的值。
        """
        if not newly_set_fields:
            return

        msg = user_message.lower()

        # 性别：必须包含"男"/"女"字眼
        if "patient.gender" in newly_set_fields:
            mentioned = any(kw in msg for kw in ["男", "女", "男性", "女性", "性别"])
            if not mentioned:
                form.patient.gender = None
                form.filled_fields.discard("patient.gender")
                logger.info("Removed inferred gender (not mentioned in user message)")

        # 年龄：必须有数字+"岁"/"月"
        if "patient.age" in newly_set_fields:
            mentioned = bool(re.search(r'\d+\s*[岁月]', msg))
            if not mentioned:
                form.patient.age = None
                form.patient.age_unit = None
                form.filled_fields.discard("patient.age")
                form.filled_fields.discard("patient.age_unit")
                logger.info("Removed inferred age (not mentioned in user message)")

        # 体重：必须有数字+"kg"/"公斤"/"斤"
        if "patient.weight_kg" in newly_set_fields:
            mentioned = any(kw in msg for kw in ["kg", "公斤", "斤", "千克", "体重"])
            if not mentioned:
                form.patient.weight_kg = None
                form.filled_fields.discard("patient.weight_kg")
                logger.info("Removed inferred weight (not mentioned in user message)")

        # 过敏史：必须提到"过敏"或"无"+"过敏"
        if "allergies.drug_allergies" in newly_set_fields:
            mentioned_allergy = any(kw in msg for kw in ["过敏", "过敏史"])
            if not mentioned_allergy:
                form.allergies.drug_allergies = []
                form.filled_fields.discard("allergies.drug_allergies")
                logger.info("Removed inferred allergy info (not mentioned in user message)")

    def _llm_extract(self, message: str, form: ConsultationForm) -> Optional[Dict[str, Any]]:
        """调用 LLM 从消息中提取结构化信息"""
        if not self.llm_client:
            return None

        summary = form.to_summary()
        prompt = EXTRACTION_SYSTEM_PROMPT.format(form_summary=summary if summary else "暂无已收集信息")

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"患者最新回复：{message}"},
        ]

        response = self.llm_client.chat(messages)
        content = response.get("content", "")
        return self._parse_json_response(content)

    def _parse_json_response(self, content: str) -> Optional[Dict[str, Any]]:
        """从 LLM 响应中解析 JSON"""
        if not content:
            return None
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                return None
        return None

    def _merge(self, extracted: Dict[str, Any], form: ConsultationForm) -> None:
        """将提取的数据合并到现有表单（新值覆盖旧值，列表去重追加）"""
        _merge_patient(extracted.get("patient"), form)
        _merge_symptoms(extracted.get("symptoms"), form)
        _merge_chief_complaint(extracted.get("chief_complaint"), form)
        _merge_vital_signs(extracted.get("vital_signs"), form)
        _merge_medical_history(extracted.get("medical_history"), form)
        _merge_medications(extracted.get("current_medications"), form.current_medications, "current_medications", form)
        _merge_medications(extracted.get("self_medicated"), form.self_medicated, "self_medicated", form)
        _merge_medications(extracted.get("long_term_medications"), form.long_term_medications, "long_term_medications", form)
        _merge_allergies(extracted.get("allergies"), form)
        _merge_social(extracted.get("social"), form)
        _merge_expectation(extracted.get("expectation"), form)
        _merge_red_flags(extracted.get("red_flags"), form)

    def _fallback_extract(self, message: str, form: ConsultationForm) -> None:
        """降级提取：使用规则提取器提取基本信息"""
        try:
            from agent.subagents.symptom_extractor import SymptomExtractor
            extractor = SymptomExtractor(use_llm=False)
            structured = extractor.extract(message)

            # 合并基本信息
            if structured.chief_complaint and not form.chief_complaint:
                form.chief_complaint = structured.chief_complaint
                form.filled_fields.add("chief_complaint")

            if structured.patient_info.age is not None and form.patient.age is None:
                form.patient.age = float(structured.patient_info.age)
                form.filled_fields.add("patient.age")

            if structured.patient_info.weight is not None and form.patient.weight_kg is None:
                form.patient.weight_kg = structured.patient_info.weight
                form.filled_fields.add("patient.weight_kg")

            if structured.patient_info.gender and not form.patient.gender:
                gender_map = {"M": "男", "F": "女", "other": "不愿透露"}
                form.patient.gender = gender_map.get(structured.patient_info.gender)
                form.filled_fields.add("patient.gender")

            if structured.patient_info.allergies and not form.allergies.drug_allergies:
                form.allergies.drug_allergies = structured.patient_info.allergies
                form.filled_fields.add("allergies.drug_allergies")

            if structured.symptoms and not form.symptoms:
                for s in structured.symptoms:
                    entry = SymptomEntry(location=s)
                    form.symptoms.append(entry)

            if structured.signs:
                vs = form.vital_signs
                if "体温" in structured.signs and vs.temperature_c is None:
                    vs.temperature_c = float(structured.signs["体温"])
                    form.filled_fields.add("vital_signs.temperature_c")
                if "心率" in structured.signs and vs.heart_rate_bpm is None:
                    vs.heart_rate_bpm = int(structured.signs["心率"])
                if "血压" in structured.signs:
                    bp = structured.signs["血压"]
                    if isinstance(bp, str) and "/" in bp:
                        parts = bp.split("/")
                        vs.blood_pressure_systolic = int(parts[0])
                        vs.blood_pressure_diastolic = int(parts[1])

        except Exception as e:
            logger.warning(f"降级提取也失败: {e}")


# ==================== 合并辅助函数 ====================

def _merge_patient(data: Optional[Dict[str, Any]], form: ConsultationForm) -> None:
    if not data:
        return
    p = form.patient
    changes = {
        "patient.age": ("age", lambda v: float(v) if v is not None else None),
        "patient.age_unit": ("age_unit", None),
        "patient.weight_kg": ("weight_kg", lambda v: float(v) if v is not None else None),
        "patient.gender": ("gender", None),
        "patient.pregnant": ("pregnant", None),
        "patient.gestational_weeks": ("gestational_weeks", lambda v: int(v) if v is not None else None),
        "patient.breastfeeding": ("breastfeeding", None),
    }
    for field_path, (attr, converter) in changes.items():
        if attr in data and data[attr] is not None:
            val = converter(data[attr]) if converter else data[attr]
            if val != getattr(p, attr):
                setattr(p, attr, val)
                form.filled_fields.add(field_path)


def _merge_symptoms(data: Optional[List[Dict[str, Any]]], form: ConsultationForm) -> None:
    if not data:
        return
    extracted_count = len(data)
    existing_count = len(form.symptoms)

    for i, s_data in enumerate(data):
        if not any(k in s_data and s_data[k] is not None for k in
                    ["location", "quality", "severity_0_10", "onset_time",
                     "pattern", "duration", "trigger_factors", "accompanying_symptoms"]):
            continue

        if i < existing_count:
            target = form.symptoms[i]
        else:
            target = SymptomEntry()
            form.symptoms.append(target)

        if s_data.get("location") is not None:
            target.location = s_data["location"]
        if s_data.get("quality") is not None:
            target.quality = s_data["quality"]
        if s_data.get("severity_0_10") is not None:
            target.severity_0_10 = int(s_data["severity_0_10"])
        if s_data.get("onset_time") is not None:
            target.onset_time = s_data["onset_time"]
        if s_data.get("duration") is not None:
            target.duration = s_data["duration"]
        if s_data.get("pattern") is not None:
            target.pattern = s_data["pattern"]
        if s_data.get("trigger_factors") is not None:
            target.trigger_factors = s_data["trigger_factors"]
        if s_data.get("relieving_factors") is not None:
            target.relieving_factors = s_data["relieving_factors"]
        if s_data.get("accompanying_symptoms") is not None:
            existing_acc = set(target.accompanying_symptoms)
            for acc in s_data["accompanying_symptoms"]:
                if acc not in existing_acc:
                    target.accompanying_symptoms.append(acc)

    if extracted_count > 0:
        # 只将实际有值的核心字段标记为已填，避免 LLM 返回空条目时误标
        for s_data in data:
            if s_data.get("location") is not None:
                form.filled_fields.add("symptoms[].location")
            if s_data.get("quality") is not None:
                form.filled_fields.add("symptoms[].quality")
            if s_data.get("severity_0_10") is not None:
                form.filled_fields.add("symptoms[].severity_0_10")
            if s_data.get("onset_time") is not None:
                form.filled_fields.add("symptoms[].onset_time")


def _merge_chief_complaint(data: Optional[str], form: ConsultationForm) -> None:
    if data and data.strip():
        form.chief_complaint = data.strip()
        form.filled_fields.add("chief_complaint")


def _merge_vital_signs(data: Optional[Dict[str, Any]], form: ConsultationForm) -> None:
    if not data:
        return
    vs = form.vital_signs
    mappings = [
        ("vital_signs.temperature_c", "temperature_c", lambda v: float(v)),
        ("vital_signs.has_fever", "has_fever", None),
        ("vital_signs.fever_duration_days", "fever_duration_days", lambda v: float(v)),
        ("vital_signs.blood_pressure_systolic", "blood_pressure_systolic", lambda v: int(v)),
        ("vital_signs.blood_pressure_diastolic", "blood_pressure_diastolic", lambda v: int(v)),
        ("vital_signs.heart_rate_bpm", "heart_rate_bpm", lambda v: int(v)),
        ("vital_signs.respiratory_rate", "respiratory_rate", lambda v: int(v)),
        ("vital_signs.oxygen_saturation", "oxygen_saturation", lambda v: float(v)),
        ("vital_signs.skin_rash", "skin_rash", None),
        ("vital_signs.rash_description", "rash_description", None),
    ]
    for field_path, attr, converter in mappings:
        if attr in data and data[attr] is not None:
            val = converter(data[attr]) if converter else data[attr]
            if val != getattr(vs, attr):
                setattr(vs, attr, val)
                form.filled_fields.add(field_path)


def _merge_medical_history(data: Optional[Dict[str, Any]], form: ConsultationForm) -> None:
    if not data:
        return
    mh = form.medical_history
    mappings = [
        ("medical_history.has_liver_disease", "has_liver_disease"),
        ("medical_history.has_kidney_disease", "has_kidney_disease"),
        ("medical_history.has_peptic_ulcer", "has_peptic_ulcer"),
        ("medical_history.has_gi_bleeding", "has_gi_bleeding"),
        ("medical_history.has_epilepsy", "has_epilepsy"),
        ("medical_history.has_glaucoma", "has_glaucoma"),
        ("medical_history.has_prostate_hyperplasia", "has_prostate_hyperplasia"),
        ("medical_history.has_thyroid_disease", "has_thyroid_disease"),
        ("medical_history.has_heart_failure", "has_heart_failure"),
        ("medical_history.has_arrhythmia", "has_arrhythmia"),
        ("medical_history.has_bleeding_disorder", "has_bleeding_disorder"),
        ("medical_history.recent_surgery", "recent_surgery"),
    ]
    for field_path, attr in mappings:
        if attr in data and data[attr] is not None:
            if data[attr] != getattr(mh, attr):
                setattr(mh, attr, data[attr])
                form.filled_fields.add(field_path)

    if data.get("chronic_diseases") is not None:
        existing = set(mh.chronic_diseases)
        for d in data["chronic_diseases"]:
            if d not in existing:
                mh.chronic_diseases.append(d)
        if data["chronic_diseases"]:
            form.filled_fields.add("medical_history.chronic_diseases")


def _merge_medications(
    data: Optional[List[Dict[str, Any]]],
    target_list: List[MedicationRecord],
    field_prefix: str,
    form: ConsultationForm,
) -> None:
    if data is None:
        return
    # 空列表表示明确说没有用药
    if data == []:
        if not target_list:
            form.filled_fields.add(field_prefix)
        return

    existing_names = {m.medication_name for m in target_list if m.is_valid()}
    for item in data:
        name = item.get("medication_name", "").strip()
        if name and name not in existing_names:
            record = MedicationRecord(
                medication_name=name,
                route=item.get("route"),
                dosage=item.get("dosage"),
                frequency=item.get("frequency"),
                indication=item.get("indication"),
                start_date=item.get("start_date"),
                end_date=item.get("end_date"),
                effectiveness=item.get("effectiveness"),
                adverse_reaction=item.get("adverse_reaction"),
            )
            target_list.append(record)
            existing_names.add(name)

    if target_list:
        form.filled_fields.add(field_prefix)


def _merge_allergies(data: Optional[Dict[str, Any]], form: ConsultationForm) -> None:
    if not data:
        return
    a = form.allergies
    for field in ["drug_allergies", "food_allergies", "excipient_allergies", "other_intolerances"]:
        val = data.get(field)
        if val is not None:
            existing = set(getattr(a, field))
            for item in val:
                if item not in existing:
                    getattr(a, field).append(item)
            form.filled_fields.add(f"allergies.{field}")


def _merge_social(data: Optional[Dict[str, Any]], form: ConsultationForm) -> None:
    if not data:
        return
    s = form.social
    mappings = [
        ("social.occupation", "occupation"),
        ("social.need_operate_machinery", "need_operate_machinery"),
        ("social.alcohol_use", "alcohol_use"),
        ("social.smoking_status", "smoking_status"),
        ("social.special_diet", "special_diet"),
    ]
    for field_path, attr in mappings:
        if attr in data and data[attr] is not None:
            if data[attr] != getattr(s, attr):
                setattr(s, attr, data[attr])
                form.filled_fields.add(field_path)


def _merge_expectation(data: Optional[Dict[str, Any]], form: ConsultationForm) -> None:
    if not data:
        return
    e = form.expectation
    mappings = [
        ("expectation.patient_goal", "patient_goal"),
        ("expectation.preferred_drug_type", "preferred_drug_type"),
        ("expectation.preferred_formulation", "preferred_formulation"),
        ("expectation.cost_constraint", "cost_constraint"),
    ]
    for field_path, attr in mappings:
        if attr in data and data[attr] is not None:
            if data[attr] != getattr(e, attr):
                setattr(e, attr, data[attr])
                form.filled_fields.add(field_path)


def _merge_red_flags(data: Optional[Dict[str, Any]], form: ConsultationForm) -> None:
    if not data:
        return
    rf = form.red_flags
    fields = [
        "high_fever", "severe_headache", "chest_pain", "dyspnea",
        "altered_mental", "bleeding", "anaphylaxis",
        "child_or_elderly_frail", "pregnancy_with_alarm", "other_red_flags",
    ]
    for attr in fields:
        if attr in data and data[attr] is not None:
            if data[attr] != getattr(rf, attr):
                setattr(rf, attr, data[attr])
                form.filled_fields.add(f"red_flags.{attr}")


# ==================== 基础信息规则提取（不调用 LLM） ====================


def rule_extract_basics(form: ConsultationForm, message: str, target_field: str) -> None:
    """用规则从用户消息中提取基础信息并填入表单，不调用 LLM

    Args:
        form: 当前表单
        message: 用户原始消息
        target_field: BASICS_QUESTIONS 中定义的 field 路径，如 "patient.gender"
    """
    msg = message.strip()
    if not msg:
        return

    if target_field == "patient.gender":
        if "男" in msg:
            form.patient.gender = "男"
        elif "女" in msg:
            form.patient.gender = "女"
        elif "不愿透露" in msg:
            form.patient.gender = "不愿透露"
        else:
            return

    elif target_field == "patient.age":
        m = re.search(r"(\d+)\s*(岁|月|天)?", msg)
        if m:
            form.patient.age = float(m.group(1))
            form.patient.age_unit = m.group(2) or "岁"
        else:
            return

    elif target_field == "patient.weight_kg":
        m = re.search(r"(\d+(?:\.\d+)?)\s*(公斤|kg|斤|千克)?", msg, re.IGNORECASE)
        if m:
            val = float(m.group(1))
            unit = (m.group(2) or "").lower()
            if unit == "斤":
                form.patient.weight_kg = val / 2.0
            else:
                form.patient.weight_kg = val
        else:
            return

    elif target_field == "allergies.drug_allergies":
        if not msg or any(kw in msg for kw in ["无", "没"]):
            form.allergies.drug_allergies = []
        else:
            parts = re.split(r"[,，、\s]+", msg)
            form.allergies.drug_allergies = [p.strip() for p in parts if p.strip()]

    elif target_field == "current_medications":
        if not msg or any(kw in msg for kw in ["无", "没"]):
            form.current_medications = []
        else:
            parts = re.split(r"[,，、\s]+", msg)
            form.current_medications = [
                MedicationRecord(medication_name=p.strip())
                for p in parts if p.strip()
            ]
    else:
        return

    form.filled_fields.add(target_field)
