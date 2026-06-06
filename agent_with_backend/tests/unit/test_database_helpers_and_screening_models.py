from datetime import date, datetime
from types import SimpleNamespace

import pytest

from common.config import Config
from database import connection, helpers
from screening.models.screening_config_model import ScreeningConfig
from screening.models.screening_history_model import ScreeningHistory
from screening.models.symptom_model import Symptom, SymptomSynonym


def test_database_initialization_and_helper_queries(tmp_path, monkeypatch):
    db_path = tmp_path / "pharmacy.db"
    monkeypatch.setattr(Config, "DATABASE_PATH", str(db_path))

    connection.init_database()
    connection.init_database()

    conn = connection.get_db_connection()
    conn.execute(
        """
        INSERT INTO inventory
        (drug_id, name, quantity, expiry_date, shelf_x, shelf_y, shelve_id)
        VALUES (1, 'Aspirin', 10, 30, 1, 2, 3)
        """
    )
    conn.execute(
        """
        INSERT INTO inventory
        (drug_id, name, quantity, expiry_date, shelf_x, shelf_y, shelve_id)
        VALUES (2, 'Cold Relief', 1, 0, 1, 2, 3)
        """
    )
    conn.commit()
    connection.close_db_connection(conn)

    assert helpers.query_drug(1)["name"] == "Aspirin"
    assert helpers.query_drug(999) is None
    assert helpers.validate_and_get_drug(1, 2)[1] is None
    assert "not found" in helpers.validate_and_get_drug(999, 1)[1]
    assert "expired" in helpers.validate_and_get_drug(2, 1)[1]
    assert "Insufficient" in helpers.validate_and_get_drug(1, 20)[1]
    assert helpers.find_drug_id_by_name("Aspirin") == 1
    assert helpers.find_drug_id_by_name("Cold-Relief") == 2
    assert helpers.find_drug_id_by_name("Aspir") == 1
    assert helpers.find_drug_id_by_name(" ") is None
    assert helpers.find_drug_id_by_name("x" * 101) is None
    assert helpers.find_drug_id_by_name("bad;name") is None


def test_database_migration_helpers_and_serializer(tmp_path, monkeypatch):
    db_path = tmp_path / "migration.db"
    monkeypatch.setattr(Config, "DATABASE_PATH", str(db_path))
    conn = connection.get_db_connection()
    conn.execute("CREATE TABLE sample (id INTEGER)")

    connection._add_column_if_not_exists(conn, "sample", "name", "TEXT DEFAULT ''")
    connection._add_column_if_not_exists(conn, "sample", "name", "TEXT DEFAULT ''")
    connection._add_index_if_not_exists(
        conn, "idx_sample_id", "CREATE INDEX idx_sample_id ON sample(id)"
    )
    connection._add_index_if_not_exists(
        conn, "idx_sample_id", "CREATE INDEX idx_sample_id ON sample(id)"
    )

    assert connection.json_serializer(date(2026, 6, 7)) == "2026-06-07"
    assert connection.json_serializer(datetime(2026, 6, 7, 8, 9)).startswith(
        "2026-06-07T08:09"
    )
    with pytest.raises(TypeError):
        connection.json_serializer(object())
    connection.close_db_connection(conn)
    connection.close_db_connection(None)


def test_screening_models_serialize_values():
    created = datetime(2026, 6, 7, 8, 0)
    synonym = SimpleNamespace(
        id=2,
        symptom_id=1,
        synonym_name="head pain",
        priority=8,
        created_at=created,
    )
    symptom = SimpleNamespace(
        id=1,
        standard_name="headache",
        category="neurology",
        description="pain",
        severity_levels="mild,severe",
        related_drugs_count=2,
        created_at=created,
    )
    symptom.synonyms = [synonym]

    assert Symptom.to_dict(symptom)["synonyms"] == ["head pain"]
    assert "headache" in Symptom.__repr__(symptom)
    assert SymptomSynonym.to_dict(synonym)["created_at"] == created.isoformat()
    assert "head pain" in SymptomSynonym.__repr__(synonym)

    history = SimpleNamespace(
        id=3,
        user_id=9,
        input_symptoms=["headache"],
        input_text="pain",
        patient_info={"age": 20},
        filters={"limit": 5},
        result_drugs=[{"id": 1}],
        result_count=1,
        confidence_scores=[0.9],
        execution_time=0.1,
        status="success",
        request_id="req-1",
        created_at=created,
        error_message=None,
    )
    assert ScreeningHistory.to_dict(history)["request_id"] == "req-1"
    assert "result_count=1" in ScreeningHistory.__repr__(history)

    config = SimpleNamespace(
        id=4,
        config_name="default",
        description="default config",
        algorithm_type="hybrid",
        confidence_threshold=0.7,
        max_results=10,
        min_symptom_match_rate=0.4,
        enable_synonym_expansion=True,
        enable_llm_synonym=False,
        max_synonym_attempts=2,
        enable_cache=True,
        cache_ttl=60,
        cache_strategy="lru",
        timeout_seconds=2.0,
        batch_max_size=20,
        extra_params={"weight": 2},
        is_active=True,
        version=2,
        created_at=created,
        updated_at=created,
    )
    data = ScreeningConfig.to_dict(config)
    assert data["confidence_threshold"] == 0.7
    assert data["extra_params"] == {"weight": 2}
    assert "default" in ScreeningConfig.__repr__(config)
