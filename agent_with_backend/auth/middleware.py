"""Flask：认证与权限装饰器（供本模块及其他蓝图复用）。"""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable, Iterable, Optional, TypeVar, cast

from flask import Request, jsonify, request

from auth.audit import write_audit
from auth.db import get_db_connection
from auth.schema import permission_codes_for_user
from auth.tokens import decode_access_token

F = TypeVar("F", bound=Callable[..., Any])


def _err(
    message: str, error_code: str, status: int, details: Optional[dict] = None
):
    body: dict[str, Any] = {
        "success": False,
        "error_code": error_code,
        "message": message,
    }
    if details is not None:
        body["details"] = details
    return jsonify(body), status


def get_bearer_token(req: Request) -> Optional[str]:
    h = req.headers.get("Authorization", "")
    if h.lower().startswith("bearer "):
        return h[7:].strip()
    return None


def get_current_user_from_token(token: str) -> Optional[dict[str, Any]]:
    try:
        payload = decode_access_token(token)
    except Exception:
        return None
    if payload.get("type") != "access":
        return None
    try:
        uid = int(payload["sub"])
    except (KeyError, ValueError, TypeError):
        return None
    return {
        "id": uid,
        "username": payload.get("username"),
        "role": payload.get("role"),
        "permissions": payload.get("permissions") or [],
    }


def require_auth(f: F) -> F:
    @wraps(f)
    def wrapped(*args, **kwargs):
        tok = get_bearer_token(request)
        if not tok:
            return _err("未提供访问令牌", "AUTH_001", 401)
        user = get_current_user_from_token(tok)
        if not user:
            return _err("令牌无效或已过期", "AUTH_002", 401)
        conn = get_db_connection()
        try:
            row = conn.execute(
                "SELECT id, username, status, role_id FROM auth_users WHERE id = ?",
                (user["id"],),
            ).fetchone()
            if not row or row["status"] != "active":
                return _err("用户不可用", "AUTH_003", 401)
            fresh_perms = permission_codes_for_user(conn, user["id"])
        finally:
            conn.close()
        request.auth_user = {**user, "permissions": fresh_perms}  # type: ignore[attr-defined]
        return f(*args, **kwargs)

    return cast(F, wrapped)


def require_permissions(*needed: str) -> Callable[[F], F]:
    needed_set = set(needed)

    def decorator(f: F) -> F:
        @wraps(f)
        def wrapped(*args, **kwargs):
            tok = get_bearer_token(request)
            if not tok:
                return _err("未提供访问令牌", "AUTH_001", 401)
            user = get_current_user_from_token(tok)
            if not user:
                return _err("令牌无效或已过期", "AUTH_002", 401)
            conn = get_db_connection()
            try:
                row = conn.execute(
                    "SELECT id, status FROM auth_users WHERE id = ?",
                    (user["id"],),
                ).fetchone()
                if not row or row["status"] != "active":
                    return _err("用户不可用", "AUTH_003", 401)
                perms = set(permission_codes_for_user(conn, user["id"]))
            finally:
                conn.close()
            if not needed_set.issubset(perms):
                write_audit(
                    user_id=user["id"],
                    username=str(user.get("username")),
                    action="forbidden",
                    resource=request.path,
                    details={"needed": list(needed_set), "have": sorted(perms)},
                    ip=request.remote_addr,
                )
                return _err("权限不足", "AUTH_403", 403)
            request.auth_user = {**user, "permissions": sorted(perms)}  # type: ignore[attr-defined]
            return f(*args, **kwargs)

        return cast(F, wrapped)

    return decorator


def require_permission(operation_code: str) -> Callable[[F], F]:
    """单权限装饰器（与分工文档 `require_permission('create:drug')` 用法一致）。"""
    return require_permissions(operation_code)


def user_has_any_permission(perms: Iterable[str], need: Iterable[str]) -> bool:
    return bool(set(need).intersection(set(perms)))
