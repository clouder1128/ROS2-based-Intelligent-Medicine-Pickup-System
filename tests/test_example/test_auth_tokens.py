# JWT 令牌测试
# 验证 auth.tokens 中访问令牌的创建、解码、刷新令牌 ID 生成和过期时间逻辑。

import os
from datetime import datetime, timezone

import pytest
from auth.tokens import create_access_token, create_refresh_jti, decode_access_token, refresh_token_expiry_utc


def test_create_and_decode_access_token(monkeypatch):
    monkeypatch.setenv("AUTH_JWT_SECRET", "pytest-secret-token")
    token = create_access_token(
        user_id=42,
        username="pytest-user",
        role_code="admin",
        permissions=["read:drug", "write:drug"],
    )

    payload = decode_access_token(token)
    assert payload["sub"] == "42"
    assert payload["username"] == "pytest-user"
    assert payload["role"] == "admin"
    assert payload["permissions"] == ["read:drug", "write:drug"]
    assert payload["type"] == "access"
    assert payload["exp"] > payload["iat"]


def test_decode_access_token_invalid(monkeypatch):
    monkeypatch.setenv("AUTH_JWT_SECRET", "pytest-secret-token")
    with pytest.raises(Exception):
        decode_access_token("not-a-valid-token")


def test_create_refresh_jti_and_expiry():
    jti_a = create_refresh_jti()
    jti_b = create_refresh_jti()
    assert jti_a != jti_b

    expiry = refresh_token_expiry_utc()
    assert isinstance(expiry, datetime)
    assert expiry > datetime.now(timezone.utc)
