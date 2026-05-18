"""JWT：访问令牌 24h、刷新令牌 7d（与接口清单一致）。"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

ACCESS_TTL_SECONDS = int(os.environ.get("AUTH_ACCESS_TTL_SEC", str(24 * 3600)))
REFRESH_TTL_SECONDS = int(os.environ.get("AUTH_REFRESH_TTL_SEC", str(7 * 24 * 3600)))
JWT_ALG = "HS256"


def _secret() -> str:
    s = os.environ.get("AUTH_JWT_SECRET", "")
    if not s:
        s = os.environ.get("FLASK_SECRET_KEY", "dev-insecure-change-me")
    return s


def create_access_token(
    user_id: int, username: str, role_code: str, permissions: list[str]
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role_code,
        "permissions": permissions,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(seconds=ACCESS_TTL_SECONDS),
    }
    return jwt.encode(payload, _secret(), algorithm=JWT_ALG)


def decode_access_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, _secret(), algorithms=[JWT_ALG])


def create_refresh_jti() -> str:
    return str(uuid.uuid4())


def refresh_token_expiry_utc() -> datetime:
    return datetime.now(timezone.utc) + timedelta(seconds=REFRESH_TTL_SECONDS)
