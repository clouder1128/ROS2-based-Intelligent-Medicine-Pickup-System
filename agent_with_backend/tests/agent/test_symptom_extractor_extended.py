import asyncio
import json
from unittest.mock import MagicMock

import pytest

from agent.subagents.exceptions import ExtractionError
from agent.subagents.extractor import SymptomExtractor
from agent.subagents.models import PatientInfo, StructuredSymptoms


def test_rule_extraction_collects_patient_symptoms_signs_and_history(monkeypatch):
    from common.config import Config

    monkeypatch.setattr(Config, "NEGATION_WORDS", ["无", "没有", "不"])
    extractor = SymptomExtractor(use_llm=False)

    result = extractor.extract(
        "35岁男性，体重70kg，头痛、发热和浮肿，体温39.2C，"
        "心率110次，血压140/90mmHg，对青霉素过敏，有高血压和糖尿病。"
    )

    assert result.chief_complaint.startswith("35岁男性")
    assert {"头痛", "发热", "浮肿"}.issubset(result.symptoms)
    assert result.signs == {
        "体温": 39.2,
        "心率": 110,
        "血压": "140/90",
        "水肿": True,
    }
    assert result.patient_info.age == 35
    assert result.patient_info.weight == 70.0
    assert result.patient_info.gender == "M"
    assert "青霉素" in result.patient_info.allergies
    assert result.medical_history == {"高血压": True, "糖尿病": True}


def test_rule_extraction_honors_negation_and_extracts_alternate_sign_formats(monkeypatch):
    from common.config import Config

    monkeypatch.setattr(Config, "NEGATION_WORDS", ["无", "没有", "不"])
    extractor = SymptomExtractor(use_llm=False)

    result = extractor.extract(
        "女性，年龄28，60kg，没有头痛。咳嗽，温度38.5，脉搏88，"
        "120/80mmHg，并有黄疸。过敏于花粉，。"
    )

    assert "头痛" not in result.symptoms
    assert "咳嗽" in result.symptoms
    assert result.patient_info.age == 28
    assert result.patient_info.gender == "F"
    assert result.signs["体温"] == 38.5
    assert result.signs["心率"] == 88
    assert result.signs["血压"] == "120/80"
    assert result.signs["黄疸"] is True


def test_llm_extraction_cleans_degree_words_and_parses_embedded_json():
    payload = {
        "chief_complaint": "头痛",
        "symptoms": ["重度头痛", "持续性 恶心", "轻微"],
        "severity": {"头痛": "重度"},
        "signs": {},
        "patient_info": {"age": 40, "gender": "F"},
    }
    client = MagicMock()
    client.chat.return_value = {"content": f"分析如下：{json.dumps(payload, ensure_ascii=False)} 完毕"}

    result = SymptomExtractor(client).extract("我头痛")

    assert result.symptoms == ["头痛", "恶心"]
    assert result.patient_info.age == 40
    assert client.chat.call_args.args[0][0]["role"] == "system"


def test_llm_failure_and_missing_client_fall_back_to_rules(monkeypatch):
    from common.config import Config

    monkeypatch.setattr(Config, "NEGATION_WORDS", [])
    failing_client = MagicMock()
    failing_client.chat.side_effect = RuntimeError("offline")

    assert "头痛" in SymptomExtractor(failing_client).extract("头痛").symptoms

    extractor = SymptomExtractor(use_llm=False)
    extractor.use_llm = True
    assert "咳嗽" in extractor._extract_with_llm("咳嗽").symptoms


def test_async_extraction_supports_rule_and_llm_modes(monkeypatch):
    from common.config import Config

    monkeypatch.setattr(Config, "NEGATION_WORDS", [])
    rule_result = asyncio.run(SymptomExtractor(use_llm=False).extract_async("发热"))

    client = MagicMock()
    client.chat.return_value = {
        "content": json.dumps(
            {
                "chief_complaint": "咳嗽",
                "symptoms": ["轻度咳嗽"],
                "patient_info": {},
            },
            ensure_ascii=False,
        )
    }
    llm_result = asyncio.run(SymptomExtractor(client).extract_async("咳嗽"))

    assert rule_result.symptoms == ["发热"]
    assert llm_result.symptoms == ["咳嗽"]


@pytest.mark.parametrize("value", ["", "   ", None])
def test_empty_input_is_rejected(value):
    extractor = SymptomExtractor(use_llm=False)

    with pytest.raises(ExtractionError, match="不能为空"):
        extractor.extract(value)
    with pytest.raises(ExtractionError, match="不能为空"):
        asyncio.run(extractor.extract_async(value))


def test_validation_reports_each_invalid_shape():
    extractor = SymptomExtractor(use_llm=False)

    valid = StructuredSymptoms("头痛", ["头痛"], patient_info=PatientInfo(age=30, weight=60))
    assert extractor.validate_symptoms(valid) == (True, None)
    assert extractor.validate_symptoms(StructuredSymptoms("", ["头痛"]))[1] == "主诉不能为空"
    assert extractor.validate_symptoms(StructuredSymptoms("不适"))[1] == "至少需要症状或体征信息"
    assert "年龄无效" in extractor.validate_symptoms(
        StructuredSymptoms("不适", ["头痛"], patient_info=PatientInfo(age=180))
    )[1]
    assert "体重无效" in extractor.validate_symptoms(
        StructuredSymptoms("不适", ["头痛"], patient_info=PatientInfo(weight=0.5))
    )[1]


def test_helpers_cover_cleaning_prompt_and_json_errors():
    assert SymptomExtractor._clean_symptoms(
        ["重度持续性头痛", " 轻微恶心 ", "", "普通咳嗽"]
    ) == ["头痛", "轻微恶心", "普通咳嗽"]
    assert "患者描述：" in SymptomExtractor._build_extraction_prompt("头痛")
    assert SymptomExtractor._extract_json_from_response('prefix {"a": 1} suffix') == '{"a": 1}'

    with pytest.raises(ExtractionError, match="无法从响应"):
        SymptomExtractor._extract_json_from_response("not json")
