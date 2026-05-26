# 药品控制器单元测试
# 覆盖 drug_controller 中的分页参数解析、导出格式判定、库存视图投影逻辑，以及 list_drugs 端点的错误处理。

import json
from flask import Flask

from api import drug_controller as dc


class DummyDrugCache:
    def get_drug_list(self, symptom_filter, name_filter, category_filter, sort_by, sort_order):
        return [
            {
                "drug_id": 1,
                "name": "测试药品",
                "quantity": 10,
                "expiry_date": 5,
                "shelf_x": 1,
                "shelf_y": 1,
                "shelve_id": 1,
                "category": "测试分类",
                "barcode": "0001",
                "unit": "片",
                "dosage_form": "片剂",
                "specification": "10mg",
                "min_stock_alert": 5,
            }
        ]


def test_parse_pagination_and_validation():
    app = Flask(__name__)

    with app.test_request_context("/api/drugs?page=2&limit=5"):
        assert dc._parse_pagination() == (2, 5, 5)

    with app.test_request_context("/api/drugs?page=-1&limit=0"):
        assert dc._parse_pagination() == (1, 1, 0)

    with app.test_request_context("/api/drugs?page=abc&limit=5"):
        assert dc._parse_pagination() is None


def test_parse_alert_threshold_and_expiring_days():
    app = Flask(__name__)

    with app.test_request_context("/api/drugs?threshold=20"):
        assert dc._parse_alert_threshold() == 20

    with app.test_request_context("/api/drugs?threshold=-2"):
        assert dc._parse_alert_threshold() is None

    with app.test_request_context("/api/drugs?days=7"):
        assert dc._parse_expiring_days() == 7

    with app.test_request_context("/api/drugs?days=0"):
        assert dc._parse_expiring_days() is None


def test_wants_csv_export_by_query_and_accept():
    app = Flask(__name__)

    with app.test_request_context("/api/drugs?format=csv", headers={"Accept": "application/json"}):
        assert dc._wants_csv_export() is True

    with app.test_request_context("/api/drugs?format=json", headers={"Accept": "text/csv"}):
        assert dc._wants_csv_export() is False

    with app.test_request_context("/api/drugs", headers={"Accept": "text/csv"}):
        assert dc._wants_csv_export() is True


def test_inventory_projection_calculates_flags():
    item = {
        "drug_id": 2,
        "name": "库存药品",
        "quantity": 3,
        "expiry_date": 2,
        "shelf_x": 2,
        "shelf_y": 5,
        "shelve_id": 6,
        "min_stock_alert": 4,
    }

    projected = dc._inventory_projection(item, low_threshold=10, expiring_window=7)
    assert projected["location_label"] == "Shelf 6, Position (2, 5)"
    assert projected["needs_restock"] is True
    assert projected["is_expired_stock"] is False
    assert projected["expiring_soon"] is True


def test_list_drugs_returns_success_with_stub_cache(monkeypatch):
    app = Flask(__name__)
    app.register_blueprint(dc.drug_bp)

    monkeypatch.setattr(dc, "get_drug_cache", lambda: DummyDrugCache())

    with app.test_request_context("/api/drugs?sort_by=drug_id&order=asc"):
        response = dc.list_drugs.__wrapped__()

    assert response.status_code == 200
    payload = json.loads(response.get_data(as_text=True))
    assert payload["success"] is True
    assert payload["data"][0]["name"] == "测试药品"


def test_list_drugs_rejects_invalid_sort_parameters():
    app = Flask(__name__)

    with app.test_request_context("/api/drugs?sort_by=invalid&order=down"):
        response = dc.list_drugs.__wrapped__()

    if isinstance(response, tuple):
        response, status = response
        assert status == 400
    else:
        assert response.status_code == 400
