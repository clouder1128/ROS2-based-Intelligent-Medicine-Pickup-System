"""Flask API 测试辅助：隔离数据库、登录、创建药品。"""

from __future__ import annotations

import importlib
import json
import os
import sys
from typing import Any

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


def reload_config():
    import common.config as cc

    return importlib.reload(cc)


def _apply_db_path(db_path: str) -> None:
    """确保 ORM/连接模块使用临时库路径（避免已 import 模块缓存旧 Config）。"""
    cc = reload_config()
    cc.Config.DATABASE_PATH = str(db_path)
    importlib.reload(importlib.import_module("common.utils.database"))
    importlib.reload(importlib.import_module("auth.db"))


def init_test_db(db_path: str) -> None:
    from auth.schema import ensure_auth_schema
    from common.utils.database import init_database
    from database.scripts.seed_users import seed_users

    _apply_db_path(db_path)
    init_database()
    ensure_auth_schema()
    seed_users(db_path)


def create_test_app():
    from flask import Flask

    from api.category_controller import category_bp
    from api.drug_controller import drug_bp
    from auth import auth_bp

    app = Flask(__name__)
    app.config["TESTING"] = True
    app.register_blueprint(auth_bp)
    app.register_blueprint(drug_bp)
    app.register_blueprint(category_bp)
    return app


def json_body(response) -> dict[str, Any]:
    return json.loads(response.get_data(as_text=True))


def login(client, username: str = "admin1", password: str = "123456") -> str:
    resp = client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
    )
    data = json_body(resp)
    assert resp.status_code == 200, data
    assert data.get("success") is True
    token = data.get("access_token") or data.get("token")
    assert token
    return token


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def drug_payload(**overrides) -> dict[str, Any]:
    base = {
        "name": "测试药品",
        "quantity": 50,
        "expiry_date": 180,
        "shelf_x": 1,
        "shelf_y": 2,
        "shelve_id": 1,
        "category": "维生素矿物质",
        "indications": ["测试适应症"],
    }
    base.update(overrides)
    return base


def create_drug(client, token: str, **overrides) -> int:
    resp = client.post(
        "/api/drugs",
        json=drug_payload(**overrides),
        headers=auth_headers(token),
    )
    data = json_body(resp)
    assert resp.status_code == 201, data
    drug_id = data["data"]["drug_id"]
    return int(drug_id)
