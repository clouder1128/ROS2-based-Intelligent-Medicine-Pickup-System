"""测试访问令牌、认证中间件、权限判断及认证表初始化逻辑。"""

import sqlite3

import jwt
import pytest
from flask import Flask, request

from auth.constants import PERM_READ_DRUG, ROLE_ADMIN, ROLE_PATIENT
from auth.middleware import (
    get_bearer_token,
    get_current_user_from_token,
    require_auth,
    user_has_any_permission,
)
from auth.schema import ensure_auth_schema, permission_codes_for_user
from auth.tokens import (
    create_access_token,
    create_refresh_jti,
    decode_access_token,
    refresh_token_expiry_utc,
)

JWT_SECRET = "unit-test-secret-at-least-32-bytes"


def test_access_token_round_trip(monkeypatch):
    monkeypatch.setenv("AUTH_JWT_SECRET", JWT_SECRET)

    token = create_access_token(7, "alice", ROLE_PATIENT, [PERM_READ_DRUG])
    payload = decode_access_token(token)

    assert payload["sub"] == "7"
    assert payload["username"] == "alice"
    assert payload["role"] == ROLE_PATIENT
    assert payload["permissions"] == [PERM_READ_DRUG]
    assert payload["type"] == "access"


def test_invalid_access_token_is_rejected(monkeypatch):
    monkeypatch.setenv("AUTH_JWT_SECRET", JWT_SECRET)

    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token("not-a-token")


def test_refresh_helpers_return_unique_future_values():
    first = create_refresh_jti()
    second = create_refresh_jti()

    assert first != second
    assert refresh_token_expiry_utc().timestamp() > 0


def test_get_bearer_token_and_current_user(monkeypatch):
    monkeypatch.setenv("AUTH_JWT_SECRET", JWT_SECRET)
    app = Flask(__name__)
    token = create_access_token(3, "bob", ROLE_PATIENT, [PERM_READ_DRUG])

    with app.test_request_context(headers={"Authorization": f"Bearer {token}"}):
        assert get_bearer_token(request) == token
        user = get_current_user_from_token(token)

    assert user == {
        "id": 3,
        "username": "bob",
        "role": ROLE_PATIENT,
        "permissions": [PERM_READ_DRUG],
    }


def test_non_access_or_malformed_subject_is_rejected(monkeypatch):
    monkeypatch.setenv("AUTH_JWT_SECRET", JWT_SECRET)
    refresh_like = jwt.encode(
        {"sub": "1", "type": "refresh"}, JWT_SECRET, algorithm="HS256"
    )
    bad_subject = jwt.encode(
        {"sub": "abc", "type": "access"}, JWT_SECRET, algorithm="HS256"
    )

    assert get_current_user_from_token(refresh_like) is None
    assert get_current_user_from_token(bad_subject) is None


def test_auth_schema_seeds_roles_permissions_and_view(monkeypatch):
    monkeypatch.delenv("AUTH_DEFAULT_ADMIN_PASSWORD", raising=False)
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    ensure_auth_schema(conn)

    roles = {row["code"] for row in conn.execute("SELECT code FROM auth_roles")}
    assert {ROLE_ADMIN, ROLE_PATIENT}.issubset(roles)

    patient_role_id = conn.execute(
        "SELECT id FROM auth_roles WHERE code = ?", (ROLE_PATIENT,)
    ).fetchone()["id"]
    conn.execute(
        """
        INSERT INTO auth_users
            (username, password_hash, display_name, role_id, status)
        VALUES (?, ?, ?, ?, ?)
        """,
        ("patient-unit", "hash", "Patient Unit", patient_role_id, "active"),
    )
    user_id = conn.execute(
        "SELECT id FROM auth_users WHERE username = ?", ("patient-unit",)
    ).fetchone()["id"]
    conn.commit()

    assert permission_codes_for_user(conn, user_id) == [PERM_READ_DRUG]
    assert conn.execute("SELECT username FROM users").fetchone()["username"] == "patient-unit"
    conn.close()


def test_require_auth_returns_401_without_token():
    app = Flask(__name__)

    @app.get("/protected")
    @require_auth
    def protected():
        return {"ok": True}

    response = app.test_client().get("/protected")

    assert response.status_code == 401
    assert response.get_json()["error_code"] == "AUTH_001"


@pytest.mark.parametrize(
    ("perms", "needed", "expected"),
    [
        (["read:drug"], ["read:drug"], True),
        (["read:drug"], ["write:users"], False),
        ([], [], False),
    ],
)
def test_user_has_any_permission(perms, needed, expected):
    assert user_has_any_permission(perms, needed) is expected
