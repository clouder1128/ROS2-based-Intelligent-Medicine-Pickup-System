# 智能筛选服务测试
# 验证 SymptomService 中的症状标准化、相似度计算、同义词扩展和分类逻辑。

import pytest
from screening.services.symptom_service import SymptomService


def test_standardize_symptom_exact_and_fuzzy():
    service = SymptomService()

    assert service.standardize_symptom("头疼") == "头痛"
    assert service.standardize_symptom("发热") == "发热"
    assert service.standardize_symptom("咳嗽") == "咳嗽"

    score = service.calculate_symptom_similarity("头痛", "头疼")
    assert score >= 0.5


def test_standardize_symptoms_with_unmatched_entries():
    service = SymptomService()
    result = service.standardize_symptoms(["头疼", "腹泻", "未知症状"])

    assert result["matched_count"] == 2
    assert result["unmatched_count"] == 1
    assert set(result["standardized_symptoms"]) == {"头痛", "腹泻"}
    assert result["unmatched"] == ["未知症状"]
    assert result["confidence"] == pytest.approx(2 / 3)


def test_get_synonyms_and_expand_symptoms():
    service = SymptomService()
    synonyms = service.get_synonyms("头痛")
    assert "头疼" in synonyms
    assert "头痛" in synonyms

    expanded = service.expand_symptoms_with_synonyms(["发热"])
    assert "发热" in expanded
    assert "发烧" in expanded


def test_get_symptom_categories_returns_expected_keys():
    service = SymptomService()
    categories = service.get_symptom_categories()

    assert "呼吸道" in categories
    assert "腹泻" in categories["消化道"]
