"""数据模型定义 - 症状提取子代理的数据类"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum


class Gender(Enum):
    """性别枚举"""
    MALE = "M"
    FEMALE = "F"
    OTHER = "other"


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