"""P3模块测试框架 - symptom_extractor.py单元测试"""

import pytest
import asyncio
from subagents import (
    PatientInfo,
    StructuredSymptoms,
    SymptomExtractor,
    ExtractionError,
    extract_symptoms,
    extract_symptoms_async,
    extract_symptoms_sync
)


class TestPatientInfo:
    """PatientInfo 数据类测试"""
    
    def test_create_patient_info(self):
        """测试创建患者信息"""
        info = PatientInfo(
            age=30,
            weight=60.5,
            gender="F",
            allergies=["青霉素", "磺胺类"]
        )
        
        assert info.age == 30
        assert info.weight == 60.5
        assert info.gender == "F"
        assert len(info.allergies) == 2
    
    def test_to_dict_and_from_dict(self):
        """测试序列化和反序列化"""
        original = PatientInfo(
            age=30,
            weight=60.5,
            gender="F",
            allergies=["青霉素"]
        )
        
        data = original.to_dict()
        restored = PatientInfo.from_dict(data)
        
        assert restored.age == original.age
        assert restored.weight == original.weight
        assert restored.gender == original.gender
        assert restored.allergies == original.allergies


class TestStructuredSymptoms:
    """StructuredSymptoms 数据类测试"""
    
    def test_create_structured_symptoms(self):
        """测试创建结构化症状"""
        symptoms = StructuredSymptoms(
            chief_complaint="头痛3天",
            symptoms=["头痛", "发热"],
            signs={"体温": 38.5},
            patient_info=PatientInfo(age=30)
        )
        
        assert symptoms.chief_complaint == "头痛3天"
        assert "头痛" in symptoms.symptoms
        assert symptoms.signs["体温"] == 38.5
        assert symptoms.patient_info.age == 30
    
    def test_serialization(self):
        """测试序列化"""
        original = StructuredSymptoms(
            chief_complaint="头痛",
            symptoms=["头痛", "发热"],
            patient_info=PatientInfo(age=30, allergies=["青霉素"])
        )
        
        data = original.to_dict()
        restored = StructuredSymptoms.from_dict(data)
        
        assert restored.chief_complaint == original.chief_complaint
        assert restored.symptoms == original.symptoms
        assert restored.patient_info.age == original.patient_info.age


class TestSymptomExtractorRules:
    """症状提取器 - 规则提取模式测试"""
    
    @pytest.fixture
    def extractor(self):
        """创建规则模式提取器"""
        return SymptomExtractor(use_llm=False)
    
    def test_extract_chief_complaint(self, extractor):
        """测试提取主诉"""
        text = "我头很痛，还有点发烧。已经三天了。"
        complaint = extractor.extract_chief_complaint(text)
        
        assert "头" in complaint or "痛" in complaint
    
    def test_extract_patient_info_age(self, extractor):
        """测试提取年龄"""
        text = "我是30岁的患者"
        info = extractor.extract_patient_info(text)
        
        assert info.age == 30
    
    def test_extract_patient_info_weight(self, extractor):
        """测试提取体重"""
        text = "体重60kg"
        info = extractor.extract_patient_info(text)
        
        assert info.weight == 60.0
    
    def test_extract_patient_info_gender(self, extractor):
        """测试提取性别"""
        text1 = "我是女性患者"
        info1 = extractor.extract_patient_info(text1)
        assert info1.gender == "F"
        
        text2 = "我是男性患者"
        info2 = extractor.extract_patient_info(text2)
        assert info2.gender == "M"
    
    def test_extract_patient_info_allergies(self, extractor):
        """测试提取过敏史"""
        text = "我对青霉素过敏，磺胺类药物也过敏"
        info = extractor.extract_patient_info(text)
        
        assert info.allergies is not None
        assert "青霉素" in info.allergies or len(info.allergies) > 0
    
    def test_extract_symptoms(self, extractor):
        """测试提取症状"""
        text = "头痛、发烧、咳嗽三天"
        symptoms = extractor.extract_symptoms(text)
        
        assert "头痛" in symptoms
        assert "咳嗽" in symptoms
    
    def test_extract_signs_temperature(self, extractor):
        """测试提取体温体征"""
        text = "体温38.5°C"
        signs = extractor.extract_signs(text)
        
        assert "体温" in signs
        assert signs["体温"] == 38.5
    
    def test_extract_signs_blood_pressure(self, extractor):
        """测试提取血压体征"""
        text = "血压120/80 mmHg"
        signs = extractor.extract_signs(text)
        
        assert "血压" in signs
    
    def test_full_extraction(self, extractor):
        """测试完整提取流程"""
        text = """
        我是30岁的女性患者，体重60kg。
        最近一周头很痛，体温38.5°C，还有咳嗽。
        我对青霉素过敏。
        既往有高血压病史。
        """
        
        result = extractor.extract(text)
        
        assert result.chief_complaint != ""
        assert result.patient_info.age == 30
        assert result.patient_info.weight == 60.0
        assert result.patient_info.gender == "F"
        assert "头痛" in result.symptoms or "痛" in result.symptoms
        assert len(result.signs) > 0
    
    def test_validate_symptoms_valid(self, extractor):
        """测试验证有效症状"""
        symptoms = StructuredSymptoms(
            chief_complaint="头痛",
            symptoms=["头痛"],
            patient_info=PatientInfo(age=30)
        )
        
        is_valid, error = extractor.validate_symptoms(symptoms)
        assert is_valid is True
        assert error is None
    
    def test_validate_symptoms_invalid_age(self, extractor):
        """测试验证无效年龄"""
        symptoms = StructuredSymptoms(
            chief_complaint="头痛",
            symptoms=["头痛"],
            patient_info=PatientInfo(age=200)
        )
        
        is_valid, error = extractor.validate_symptoms(symptoms)
        assert is_valid is False
        assert error is not None
    
    def test_validate_symptoms_missing_complaint(self, extractor):
        """测试验证缺少主诉"""
        symptoms = StructuredSymptoms(
            chief_complaint="",
            symptoms=[]
        )
        
        is_valid, error = extractor.validate_symptoms(symptoms)
        assert is_valid is False


class TestSymptomExtractorConvenience:
    """症状提取便捷函数测试"""
    
    def test_extract_symptoms_function(self):
        """测试 extract_symptoms 函数"""
        text = "我30岁，头痛3天，体温38度"
        result = extract_symptoms(text)
        
        assert isinstance(result, StructuredSymptoms)
        assert result.chief_complaint != ""
        assert result.patient_info.age == 30
    
    def test_extract_symptoms_sync_function(self):
        """测试 extract_symptoms_sync 函数"""
        text = "我头痛"
        result = extract_symptoms_sync(text)
        
        assert isinstance(result, StructuredSymptoms)
        assert "头" in result.chief_complaint or "痛" in result.chief_complaint
    
    def test_extract_empty_input(self):
        """测试空输入"""
        with pytest.raises(ExtractionError):
            extract_symptoms("")
        
        with pytest.raises(ExtractionError):
            extract_symptoms("   ")
    
    @pytest.mark.asyncio
    async def test_extract_symptoms_async(self):
        """测试异步症状提取"""
        text = "我头痛，有点发烧"
        result = await extract_symptoms_async(text)
        
        assert isinstance(result, StructuredSymptoms)
        assert result.chief_complaint != ""


class TestSymptomExtractorEdgeCases:
    """症状提取器 - 边界情况测试"""
    
    def test_extract_minimal_input(self):
        """测试最小输入"""
        text = "头痛"
        result = extract_symptoms(text)
        
        assert result.chief_complaint == "头痛"
    
    def test_extract_no_patient_info(self):
        """测试没有患者信息"""
        text = "我感觉不太好"
        result = extract_symptoms(text)
        
        assert result.patient_info.age is None
        assert result.patient_info.weight is None
    
    def test_extract_multiple_allergies(self):
        """测试多个过敏"""
        text = "我对青霉素、头孢类、磺胺类都过敏"
        extractor = SymptomExtractor(use_llm=False)
        info = extractor.extract_patient_info(text)
        
        assert info.allergies is not None
        assert len(info.allergies) > 0
    
    def test_extract_with_special_characters(self):
        """测试特殊字符"""
        text = "我头痛！！！体温38.5°C...还有咳嗽>"
        result = extract_symptoms(text)
        
        assert result.chief_complaint != ""
        assert "体温" in result.signs or len(result.symptoms) > 0
    
    def test_extract_medical_history(self):
        """测试既往史提取"""
        text = "我有高血压和糖尿病病史，最近又开始头痛"
        extractor = SymptomExtractor(use_llm=False)
        history = extractor.extract_medical_history(text)
        
        assert history is not None
        if "高血压" in str(text).lower():
            assert len(history) > 0


class TestSymptomExtractorConsistency:
    """症状提取器 - 一致性测试"""
    
    def test_extract_idempotent(self):
        """测试提取幂等性"""
        text = "30岁女性，头痛，体温38度"
        
        result1 = extract_symptoms(text)
        result2 = extract_symptoms(text)
        
        assert result1.chief_complaint == result2.chief_complaint
        assert result1.symptoms == result2.symptoms
        assert result1.patient_info.age == result2.patient_info.age
    
    def test_dict_serialization_round_trip(self):
        """测试字典序列化往返"""
        text = "30岁女性，头痛"
        result = extract_symptoms(text)
        
        data = result.to_dict()
        restored = StructuredSymptoms.from_dict(data)
        
        assert result.chief_complaint == restored.chief_complaint
        assert result.symptoms == restored.symptoms
        assert result.patient_info.age == restored.patient_info.age


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
