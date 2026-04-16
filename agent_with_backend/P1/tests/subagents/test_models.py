"""测试subagents/models.py中的数据类"""

import sys
import os
import unittest
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 导入将被测试的模块
from subagents.models import Gender, PatientInfo, StructuredSymptoms


class TestGender(unittest.TestCase):
    """测试Gender枚举类"""

    def test_gender_enum(self):
        """测试Gender枚举值"""
        assert Gender.MALE.value == "M"
        assert Gender.FEMALE.value == "F"
        assert Gender.OTHER.value == "other"

        # 测试枚举成员
        assert Gender("M") == Gender.MALE
        assert Gender("F") == Gender.FEMALE
        assert Gender("other") == Gender.OTHER


class TestPatientInfo(unittest.TestCase):
    """测试PatientInfo数据类"""

    def test_patient_info_creation(self):
        """测试PatientInfo创建"""
        # 测试完整创建
        patient = PatientInfo(
            age=30,
            weight=70.5,
            gender="M",
            allergies=["penicillin", "aspirin"]
        )

        assert patient.age == 30
        assert patient.weight == 70.5
        assert patient.gender == "M"
        assert patient.allergies == ["penicillin", "aspirin"]

        # 测试部分创建
        patient2 = PatientInfo(age=25)
        assert patient2.age == 25
        assert patient2.weight is None
        assert patient2.gender is None
        assert patient2.allergies is None

    def test_patient_info_to_dict(self):
        """测试PatientInfo到字典转换"""
        patient = PatientInfo(
            age=30,
            weight=70.5,
            gender="M",
            allergies=["penicillin", "aspirin"]
        )

        result = patient.to_dict()

        assert result["age"] == 30
        assert result["weight"] == 70.5
        assert result["gender"] == "M"
        assert result["allergies"] == ["penicillin", "aspirin"]

        # 测试空过敏史
        patient2 = PatientInfo(age=30, allergies=None)
        result2 = patient2.to_dict()
        assert result2["allergies"] == []

    def test_patient_info_from_dict(self):
        """测试从字典创建PatientInfo"""
        data = {
            "age": 30,
            "weight": 70.5,
            "gender": "M",
            "allergies": ["penicillin", "aspirin"]
        }

        patient = PatientInfo.from_dict(data)

        assert patient.age == 30
        assert patient.weight == 70.5
        assert patient.gender == "M"
        assert patient.allergies == ["penicillin", "aspirin"]

        # 测试部分数据
        data2 = {"age": 25}
        patient2 = PatientInfo.from_dict(data2)
        assert patient2.age == 25
        assert patient2.weight is None
        assert patient2.gender is None
        assert patient2.allergies is None


class TestStructuredSymptoms(unittest.TestCase):
    """测试StructuredSymptoms数据类"""

    def test_structured_symptoms_creation(self):
        """测试StructuredSymptoms创建"""
        patient_info = PatientInfo(age=30, gender="M")

        symptoms = StructuredSymptoms(
            chief_complaint="头痛",
            symptoms=["头晕", "恶心"],
            signs={"体温": 37.5, "血压": "120/80"},
            patient_info=patient_info,
            medical_history={"高血压": "3年"}
        )

        assert symptoms.chief_complaint == "头痛"
        assert symptoms.symptoms == ["头晕", "恶心"]
        assert symptoms.signs == {"体温": 37.5, "血压": "120/80"}
        assert symptoms.patient_info == patient_info
        assert symptoms.medical_history == {"高血压": "3年"}

        # 测试默认值
        symptoms2 = StructuredSymptoms(chief_complaint="咳嗽")
        assert symptoms2.chief_complaint == "咳嗽"
        assert symptoms2.symptoms == []
        assert symptoms2.signs == {}
        assert isinstance(symptoms2.patient_info, PatientInfo)
        assert symptoms2.medical_history is None

    def test_structured_symptoms_to_dict(self):
        """测试StructuredSymptoms到字典转换"""
        patient_info = PatientInfo(age=30, gender="M")

        symptoms = StructuredSymptoms(
            chief_complaint="头痛",
            symptoms=["头晕", "恶心"],
            signs={"体温": 37.5},
            patient_info=patient_info,
            medical_history={"高血压": "3年"}
        )

        result = symptoms.to_dict()

        assert result["chief_complaint"] == "头痛"
        assert result["symptoms"] == ["头晕", "恶心"]
        assert result["signs"] == {"体温": 37.5}
        assert result["patient_info"] == patient_info.to_dict()
        assert result["medical_history"] == {"高血压": "3年"}

        # 测试无既往史
        symptoms2 = StructuredSymptoms(
            chief_complaint="咳嗽",
            patient_info=patient_info
        )

        result2 = symptoms2.to_dict()
        assert result2["medical_history"] is None


if __name__ == "__main__":
    """直接运行测试"""
    # 运行所有测试
    unittest.main(verbosity=2)