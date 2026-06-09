"""单元测试共享夹具：提供隔离的测试数据库、Flask 客户端和管理员令牌。"""

import pytest

from tests.api_helpers import create_test_app, init_test_db, login


@pytest.fixture
def client(tmp_path, monkeypatch):
    """为每个用例创建使用临时数据库的独立测试客户端。"""

    db_path = tmp_path / "unit_test.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_path))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "pytest-dummy")
    monkeypatch.setenv("AUTH_JWT_SECRET", "pytest-unit-secret-at-least-32-bytes")
    init_test_db(str(db_path))

    app = create_test_app()
    with app.test_client() as c:
        yield c


@pytest.fixture
def admin_token(client):
    """登录默认管理员账户并返回接口鉴权令牌。"""

    return login(client, "admin1", "123456")
