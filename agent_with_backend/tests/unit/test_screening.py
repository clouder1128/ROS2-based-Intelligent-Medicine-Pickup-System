"""测试症状标准化、药品筛选排序、历史记录和筛选配置服务。"""

from datetime import datetime, timedelta

import pytest

from screening.services.config_service import ConfigService
from screening.services.history_service import HistoryService
from screening.services.ranking_engine import RankingEngine, rank_drugs
from screening.services.screening_service import ScreeningService
from screening.services.symptom_service import SymptomService


def test_symptom_service_standardizes_expands_and_scores(monkeypatch):
    monkeypatch.setattr(
        SymptomService,
        "STANDARD_SYMPTOMS",
        {"headache": ["head pain", "headache"], "fever": ["high temp", "fever"]},
    )
    service = SymptomService()

    assert service.standardize_symptom(" Head Pain ") == "headache"
    result = service.standardize_symptoms(["head pain", "unknown", "headache"])
    assert result["standardized_symptoms"] == ["headache"]
    assert result["matched_count"] == 2
    assert result["unmatched"] == ["unknown"]
    assert set(service.expand_symptoms_with_synonyms(["fever"])) == {
        "fever",
        "high temp",
    }
    assert service.calculate_symptom_similarity("Pain", " pain ") == 1.0


def test_screening_query_matches_filters_ranks_and_limits(monkeypatch):
    monkeypatch.setattr(
        ScreeningService,
        "SAMPLE_DRUGS",
        [
            {
                "id": 1,
                "name": "Cheap",
                "category": "pain",
                "suitable_symptoms": ["headache"],
                "effectiveness": 0.8,
                "price": 5,
            },
            {
                "id": 2,
                "name": "Expensive",
                "category": "pain",
                "suitable_symptoms": ["headache"],
                "effectiveness": 0.95,
                "price": 80,
            },
        ],
    )
    service = ScreeningService()

    result = service.screening_query(
        ["headache"],
        filters={"price_range": [0, 20], "max_results": 1},
        request_id="req-1",
    )

    assert result["success"] is True
    assert result["request_id"] == "req-1"
    assert result["total_count"] == 1
    assert result["results"][0]["drug_name"] == "Cheap"


def test_screening_query_rejects_empty_symptoms():
    result = ScreeningService().screening_query([], request_id="empty")

    assert result["success"] is False
    assert result["request_id"] == "empty"


def test_batch_screening_returns_one_result_per_query(monkeypatch):
    service = ScreeningService()
    monkeypatch.setattr(
        service,
        "screening_query",
        lambda **kwargs: {"success": True, "request_id": kwargs["request_id"]},
    )

    result = service.batch_screening(
        [{"symptoms": ["a"]}, {"symptoms": ["b"]}], batch_id="batch"
    )

    assert result["total_queries"] == 2
    assert result["successful_queries"] == 2
    assert [r["request_id"] for r in result["results"]] == ["batch-0", "batch-1"]


def test_ranking_engine_applies_stock_allergy_age_and_sorting():
    candidates = [
        {
            "name": "safe",
            "match_ratio": 1,
            "price": 10,
            "quantity": 10,
            "contraindications": "",
            "age_restrictions": '{"min_age": 18, "max_age": 80}',
        },
        {
            "name": "allergy",
            "match_ratio": 1,
            "price": 1,
            "quantity": 10,
            "contraindications": "penicillin",
            "age_restrictions": "{}",
        },
        {
            "name": "out-of-stock",
            "match_ratio": 1,
            "price": 1,
            "quantity": 0,
            "contraindications": "",
            "age_restrictions": "{}",
        },
    ]

    ranked = RankingEngine().rank(
        candidates, {"age": 30, "allergies": ["penicillin"]}
    )

    assert ranked[0]["name"] == "safe"
    allergy = next(item for item in ranked if item["name"] == "allergy")
    assert allergy["excluded"] is True
    assert ranked[0]["confidence_score"] > ranked[-1]["confidence_score"]
    assert rank_drugs([candidates[0]])[0]["name"] == "safe"


def test_history_service_crud_filter_and_statistics():
    service = HistoryService()
    first = service.save_history(
        {
            "user_id": 1,
            "input_symptoms": ["headache"],
            "request_id": "r1",
            "execution_time": 0.2,
            "status": "success",
        }
    )
    service.save_history(
        {
            "user_id": 1,
            "input_symptoms": ["headache", "fever"],
            "request_id": "r2",
            "execution_time": 0.4,
            "status": "error",
        }
    )

    assert first["history_id"] == 1
    assert service.get_history(1, limit=1)["count"] == 1
    assert service.get_history_detail(1)["detail"]["request_id"] == "r1"
    assert service.get_history_by_request_id("r2")["success"] is True

    stats = service.get_user_statistics(1)
    assert stats["total_queries"] == 2
    assert stats["successful_queries"] == 1
    assert stats["failed_queries"] == 1
    assert stats["average_execution_time"] == pytest.approx(0.3)
    assert stats["most_common_symptoms"][0] == "headache"

    service._memory_storage[0]["created_at"] = (
        datetime.utcnow() - timedelta(days=40)
    ).isoformat()
    assert service.clear_old_history(days=30)["deleted_count"] == 1
    assert service.delete_history(2)["success"] is True


def test_config_service_validation_without_database_initialization():
    service = ConfigService.__new__(ConfigService)
    service._config_cache = {"default": ConfigService.DEFAULT_CONFIG.copy()}

    assert service.get_active_config()["max_results"] == 20
    assert service.get_config("missing") is None
    assert service.delete_config("default")["success"] is False

    valid = service._validate_config_fields(
        {
            "confidence_threshold": 0.8,
            "max_results": 50,
            "algorithm_type": "hybrid",
            "cache_strategy": "lru",
        }
    )
    invalid = service._validate_config_fields(
        {
            "confidence_threshold": 2,
            "max_results": 0,
            "algorithm_type": "unknown",
        }
    )
    assert valid["valid"] is True
    assert invalid["valid"] is False
    assert len(invalid["errors"]) == 3
