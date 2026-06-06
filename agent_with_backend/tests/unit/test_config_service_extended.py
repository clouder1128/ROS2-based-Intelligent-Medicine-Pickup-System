import json

from common.utils import database
from screening.services.config_service import ConfigService


def setup_database(tmp_path, monkeypatch):
    monkeypatch.setattr(
        database.Config, "DATABASE_PATH", str(tmp_path / "config.db")
    )
    database.init_database()


def test_config_service_loads_valid_and_ignores_invalid_rows(tmp_path, monkeypatch):
    setup_database(tmp_path, monkeypatch)
    conn = database.get_db_connection()
    conn.execute(
        """
        INSERT INTO screening_config (config_name, config_json, is_active)
        VALUES (?, ?, 1)
        """,
        ("custom", json.dumps({"max_results": 7})),
    )
    conn.execute(
        """
        INSERT INTO screening_config (config_name, config_json, is_active)
        VALUES (?, ?, 1)
        """,
        ("broken", "{"),
    )
    conn.commit()
    conn.close()

    service = ConfigService()

    assert service.get_config("custom")["max_results"] == 7
    assert service.get_config("broken") is None
    assert service.get_active_config()["config_name"] == "default"
    assert len(service.list_configs()) == 2

    config = service.get_config("custom")
    config["max_results"] = 999
    assert service.get_config("custom")["max_results"] == 7


def test_config_service_create_update_delete_round_trip(tmp_path, monkeypatch):
    setup_database(tmp_path, monkeypatch)
    service = ConfigService()

    assert service.create_config({})["success"] is False
    created = service.create_config(
        {
            "config_name": "fast",
            "max_results": 5,
            "algorithm_type": "hybrid",
        },
        created_by="tester",
    )
    assert created["success"] is True
    assert created["config"]["version"] == 1
    assert service.create_config({"config_name": "fast"})["success"] is False

    invalid = service.update_config(
        "fast",
        {
            "confidence_threshold": 2,
            "min_symptom_match_rate": -1,
            "max_results": 0,
            "timeout_seconds": 0,
            "cache_ttl": 0,
            "algorithm_type": "bad",
            "cache_strategy": "bad",
        },
    )
    assert invalid["success"] is False
    assert len(invalid["error"]) == 7
    assert service.update_config("missing", {})["success"] is False

    updated = service.update_config(
        "fast",
        {
            "confidence_threshold": 0.8,
            "min_symptom_match_rate": 0.4,
            "max_results": 10,
            "timeout_seconds": 10,
            "cache_ttl": 60,
            "algorithm_type": "ml",
            "cache_strategy": "fifo",
        },
        updated_by="tester",
    )
    assert updated["success"] is True
    assert updated["config"]["version"] == 2
    assert updated["config"]["updated_by"] == "tester"

    conn = database.get_db_connection()
    row = conn.execute(
        "SELECT version, config_json FROM screening_config WHERE config_name='fast'"
    ).fetchone()
    conn.close()
    assert row["version"] == 2
    assert json.loads(row["config_json"])["max_results"] == 10

    assert service.delete_config("default")["success"] is False
    assert service.delete_config("missing")["success"] is False
    assert service.delete_config("fast")["success"] is True
    assert service.get_config("fast") is None


def test_config_service_database_failures(monkeypatch):
    import common.utils.database as database_module

    monkeypatch.setattr(
        database_module,
        "get_db_connection",
        lambda: (_ for _ in ()).throw(RuntimeError("offline")),
    )
    service = ConfigService()
    assert service.get_config("default") is not None
    assert service.create_config({"config_name": "new"})["success"] is False

    service._config_cache["temp"] = {"config_name": "temp"}
    assert service.delete_config("temp")["success"] is False

