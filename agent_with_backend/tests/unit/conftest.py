import pytest

from tests.api_helpers import create_test_app, init_test_db, login


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "unit_test.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_path))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "pytest-dummy")
    init_test_db(str(db_path))

    app = create_test_app()
    with app.test_client() as c:
        yield c


@pytest.fixture
def admin_token(client):
    return login(client, "admin1", "123456")
