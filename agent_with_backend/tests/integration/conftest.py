from __future__ import annotations

import pytest
from flask import Flask

from tests.api_helpers import auth_headers, init_test_db, login


@pytest.fixture
def integration_app(tmp_path, monkeypatch):
    db_path = tmp_path / "integration.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_path))
    monkeypatch.setenv("APPROVAL_DB_PATH", str(db_path))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "pytest-dummy")
    monkeypatch.setenv("ENABLE_ROS2", "false")

    init_test_db(str(db_path))

    from common.config import Config
    from common.utils import get_drug_cache
    import database.approval_manager as approval_manager
    from ros_integration.state_store import RosStateStore

    Config.DATABASE_PATH = str(db_path)
    approval_manager._singleton = None
    get_drug_cache().clear()

    store = RosStateStore()
    store._car_states.clear()
    store._task_states.clear()
    store._cabinet_states.clear()

    from api.approval_controller import approval_bp
    from api.category_controller import category_bp
    from api.drug_controller import drug_bp
    from api.health_controller import health_bp
    from api.order_controller import order_bp
    from api.ros_state_controller import ros_state_bp
    from auth import auth_bp
    from screening.routes import create_screening_blueprint

    app = Flask(__name__)
    app.config.update(TESTING=True)
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(drug_bp)
    app.register_blueprint(category_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(approval_bp)
    app.register_blueprint(create_screening_blueprint())
    app.register_blueprint(ros_state_bp)

    yield app

    get_drug_cache().clear()
    approval_manager._singleton = None
    store._car_states.clear()
    store._task_states.clear()
    store._cabinet_states.clear()


@pytest.fixture
def client(integration_app):
    with integration_app.test_client() as test_client:
        yield test_client


@pytest.fixture
def admin_token(client):
    return login(client, "admin1", "123456")


@pytest.fixture
def doctor_token(client):
    return login(client, "doctor1", "123456")


@pytest.fixture
def patient_token(client):
    return login(client, "patient1", "123456")


@pytest.fixture
def admin_headers(admin_token):
    return auth_headers(admin_token)


@pytest.fixture
def doctor_headers(doctor_token):
    return auth_headers(doctor_token)


@pytest.fixture
def patient_headers(patient_token):
    return auth_headers(patient_token)
