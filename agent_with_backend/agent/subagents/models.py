"""数据模型定义 - 症状提取子代理的数据类"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum


class Gender(Enum):
    MALE = "M"
    FEMALE = "F"
    OTHER = "other"


@dataclass
class PatientInfo:
    age: Optional[int] = None
    weight: Optional[float] = None
    gender: Optional[str] = None
    allergies: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "age": self.age,
            "weight": self.weight,
            "gender": self.gender,
            "allergies": self.allergies or []
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PatientInfo":
        return cls(
            age=data.get("age"),
            weight=data.get("weight"),
            gender=data.get("gender"),
            allergies=data.get("allergies")
        )


@dataclass
class StructuredSymptoms:
    chief_complaint: str
    symptoms: List[str] = field(default_factory=list)
    severity: Dict[str, str] = field(default_factory=dict)
    signs: Dict[str, Any] = field(default_factory=dict)
    patient_info: PatientInfo = field(default_factory=PatientInfo)
    medical_history: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chief_complaint": self.chief_complaint,
            "symptoms": self.symptoms,
            "severity": self.severity,
            "signs": self.signs,
            "patient_info": self.patient_info.to_dict(),
            "medical_history": self.medical_history
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StructuredSymptoms":
        return cls(
            chief_complaint=data.get("chief_complaint", ""),
            symptoms=data.get("symptoms", []),
            severity=data.get("severity", {}),
            signs=data.get("signs", {}),
            patient_info=PatientInfo.from_dict(data.get("patient_info", {})),
            medical_history=data.get("medical_history")
        )
