"""测试症状同义词扩展和药品数据库查询中的库存与删除状态过滤。"""

from common.utils import database
from common.utils import symptom_db_service as service


def seed_symptom_data(db_path, monkeypatch):
    monkeypatch.setattr(database.Config, "DATABASE_PATH", str(db_path))
    database.init_database()
    conn = database.get_db_connection()
    conn.executemany(
        """
        INSERT INTO inventory
        (drug_id, name, quantity, expiry_date, shelf_x, shelf_y, shelve_id, is_deleted)
        VALUES (?, ?, ?, ?, 1, 1, 1, ?)
        """,
        [
            (1, "Available", 10, 30, 0),
            (2, "Empty", 0, 30, 0),
            (3, "Deleted", 5, 30, 1),
        ],
    )
    conn.executemany(
        """
        INSERT INTO symptom_synonyms (standard_term, synonym)
        VALUES (?, ?)
        """,
        [
            ("headache", "head pain"),
            ("headache", "migraine"),
            ("fever", "high temperature"),
        ],
    )
    conn.executemany(
        """
        INSERT INTO drug_indications (drug_id, indication)
        VALUES (?, ?)
        """,
        [
            (1, "headache relief"),
            (1, "migraine"),
            (2, "head pain"),
            (3, "headache"),
        ],
    )
    conn.commit()
    conn.close()


def test_synonym_lookup_and_expansion(tmp_path, monkeypatch):
    seed_symptom_data(tmp_path / "symptoms.db", monkeypatch)

    synonyms = service.get_all_synonyms()
    assert synonyms["headache"] == ["head pain", "migraine"]
    assert service.find_standard_term("headache") == "headache"
    assert service.find_standard_term("head pain") == "headache"
    assert service.find_standard_term("pain") == "headache"
    assert service.find_standard_term(" ") is None
    assert service.find_standard_term("unknown") is None

    expanded = set(service.expand_symptom_list(["head pain", "unknown"]))
    assert {"headache", "head pain", "migraine", "unknown"} <= expanded
    assert service.expand_symptom_list([]) == []
    assert service._like_escape(r"a\b%c_d") == r"a\\b\%c\_d"


def test_drug_lookup_respects_stock_and_deleted_filters(tmp_path, monkeypatch):
    seed_symptom_data(tmp_path / "symptoms.db", monkeypatch)

    available = service.get_drugs_by_symptom("head pain")
    assert [drug["drug_id"] for drug in available] == [1]
    assert available[0]["indications"] == ["headache relief", "migraine"]

    all_matches = service.get_drugs_by_symptom(
        "headache", include_deleted=True, include_zero_stock=True
    )
    assert [drug["drug_id"] for drug in all_matches] == [1, 2, 3]
    assert service.get_drugs_by_symptom(" ") == []
    assert service.get_drugs_by_symptom("unknown") == []
    assert service.get_drug_indications(1) == ["headache relief", "migraine"]
