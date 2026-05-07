"""权限认证 REST API（组件4 接口清单）。"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional

import jwt
from flask import Blueprint, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from auth.audit import write_audit
from auth.constants import (
    PERM_READ_AUDIT,
    PERM_READ_USERS,
    PERM_WRITE_USERS,
    ROLE_PATIENT,
)
from auth.db import get_db_connection
from auth.middleware import (
    get_bearer_token,
    get_current_user_from_token,
    require_auth,
    require_permissions,
)
from auth.schema import ensure_auth_schema, permission_codes_for_user
from auth.tokens import (
    ACCESS_TTL_SECONDS,
    JWT_ALG,
    REFRESH_TTL_SECONDS,
    create_access_token,
    create_refresh_jti,
    decode_access_token,
    refresh_token_expiry_utc,
    _secret,
)

auth_bp = Blueprint("auth_system", __name__, url_prefix="/api")


def _pagination_params() -> tuple[int, int]:
    try:
        page = int(request.args.get("page", "1"))
    except ValueError:
        page = 1
    try:
        limit = int(request.args.get("limit", "20"))
    except ValueError:
        limit = 20
    page = max(1, page)
    limit = max(1, min(100, limit))
    return page, limit


def _paginate_meta(total: int, page: int, limit: int) -> dict[str, Any]:
    pages = (total + limit - 1) // limit if limit else 0
    return {
        "page": page,
        "limit": limit,
        "total": total,
        "pages": pages,
        "has_next": page < pages,
        "has_prev": page > 1,
    }


def _issue_tokens(user_row: Any) -> tuple[str, str, list[str]]:
    conn = get_db_connection()
    try:
        role_row = conn.execute(
            "SELECT code FROM auth_roles WHERE id = ?", (user_row["role_id"],)
        ).fetchone()
        role_code = role_row["code"] if role_row else ""
        perms = permission_codes_for_user(conn, int(user_row["id"]))
        access = create_access_token(
            int(user_row["id"]),
            user_row["username"],
            role_code,
            perms,
        )
        jti = create_refresh_jti()
        exp = refresh_token_expiry_utc()
        conn.execute(
            """
            INSERT INTO auth_refresh_tokens (user_id, jti, expires_at, revoked)
            VALUES (?, ?, ?, 0)
            """,
            (int(user_row["id"]), jti, exp.isoformat()),
        )
        conn.commit()
        refresh_payload = {
            "sub": str(user_row["id"]),
            "type": "refresh",
            "jti": jti,
            "iat": datetime.now(timezone.utc),
            "exp": exp,
        }
        refresh = jwt.encode(refresh_payload, _secret(), algorithm=JWT_ALG)
        return access, refresh, perms
    finally:
        conn.close()


def _user_info(conn: Any, user_id: int) -> Optional[dict[str, Any]]:
    row = conn.execute(
        """
        SELECT u.id, u.username, u.email, u.display_name, u.status, r.code AS role
        FROM auth_users u
        JOIN auth_roles r ON r.id = u.role_id
        WHERE u.id = ?
        """,
        (user_id,),
    ).fetchone()
    if not row or row["status"] != "active":
        return None
    disp = (row["display_name"] or "").strip() or row["username"]
    perms = permission_codes_for_user(conn, user_id)
    return {
        "id": int(row["id"]),
        "username": row["username"],
        "email": row["email"],
        "display_name": disp,
        "role": row["role"],
        "permissions": perms,
    }


@auth_bp.route("/auth/register", methods=["POST"])
def register():
    ensure_auth_schema()
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    email = (data.get("email") or "").strip() or None
    display_name = (data.get("display_name") or "").strip() or username
    if not username or len(username) < 2:
        return (
            jsonify(
                {
                    "success": False,
                    "error_code": "AUTH_VAL_001",
                    "message": "用户名过短",
                }
            ),
            400,
        )
    if len(password) < 6:
        return (
            jsonify(
                {
                    "success": False,
                    "error_code": "AUTH_VAL_002",
                    "message": "密码长度至少 6 位",
                }
            ),
            400,
        )
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT id FROM auth_users WHERE username = ?", (username,)).fetchone()
        if row:
            return (
                jsonify(
                    {
                        "success": False,
                        "error_code": "AUTH_VAL_003",
                        "message": "用户名已存在",
                    }
                ),
                409,
            )
        role = conn.execute(
            "SELECT id FROM auth_roles WHERE code = ?", (ROLE_PATIENT,)
        ).fetchone()
        if not role:
            return jsonify({"success": False, "error_code": "AUTH_500", "message": "角色未初始化"}), 500
        conn.execute(
            """
            INSERT INTO auth_users (username, email, password_hash, display_name, role_id, status)
            VALUES (?, ?, ?, ?, ?, 'active')
            """,
            (username, email, generate_password_hash(password), display_name, role["id"]),
        )
        conn.commit()
        uid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        write_audit(
            user_id=int(uid),
            username=username,
            action="register",
            resource="/api/auth/register",
            ip=request.remote_addr,
        )
        return jsonify({"success": True, "user_id": int(uid), "message": "注册成功"})
    finally:
        conn.close()


@auth_bp.route("/auth/login", methods=["POST"])
def login():
    ensure_auth_schema()
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    if not username or not password:
        return (
            jsonify(
                {
                    "success": False,
                    "error_code": "AUTH_VAL_004",
                    "message": "用户名和密码必填",
                }
            ),
            400,
        )
    conn = get_db_connection()
    try:
        row = conn.execute(
            """
            SELECT u.id, u.username, u.email, u.display_name, u.password_hash, u.role_id, u.status, r.code AS role_code
            FROM auth_users u
            JOIN auth_roles r ON r.id = u.role_id
            WHERE u.username = ? COLLATE NOCASE
            """,
            (username,),
        ).fetchone()
        if not row or row["status"] != "active":
            write_audit(
                user_id=None,
                username=username,
                action="login_failed",
                resource="/api/auth/login",
                ip=request.remote_addr,
            )
            return (
                jsonify(
                    {
                        "success": False,
                        "error_code": "AUTH_005",
                        "message": "用户名或密码错误",
                    }
                ),
                401,
            )
        if not check_password_hash(row["password_hash"], password):
            write_audit(
                user_id=int(row["id"]),
                username=username,
                action="login_failed",
                resource="/api/auth/login",
                ip=request.remote_addr,
            )
            return (
                jsonify(
                    {
                        "success": False,
                        "error_code": "AUTH_005",
                        "message": "用户名或密码错误",
                    }
                ),
                401,
            )
        access, refresh, perms = _issue_tokens(row)
        disp = (row["display_name"] or "").strip() or row["username"]
        user_info = {
            "id": int(row["id"]),
            "username": row["username"],
            "email": row["email"],
            "display_name": disp,
            "role": row["role_code"],
            "permissions": perms,
        }
        write_audit(
            user_id=int(row["id"]),
            username=row["username"],
            action="login",
            resource="/api/auth/login",
            ip=request.remote_addr,
        )
        return jsonify(
            {
                "success": True,
                "token": access,
                "token_type": "Bearer",
                "access_token": access,
                "refresh_token": refresh,
                "expires_in": ACCESS_TTL_SECONDS,
                "refresh_expires_in": REFRESH_TTL_SECONDS,
                "user_info": user_info,
            }
        )
    finally:
        conn.close()


@auth_bp.route("/auth/verify", methods=["POST"])
def verify_token():
    """校验 JWT，供前端刷新/路由守卫使用。"""
    ensure_auth_schema()
    data = request.get_json(silent=True) or {}
    tok = (
        get_bearer_token(request)
        or (data.get("token") or data.get("access_token") or "").strip()
    )
    if not tok:
        return (
            jsonify(
                {
                    "success": False,
                    "valid": False,
                    "error_code": "AUTH_001",
                    "message": "未提供访问令牌",
                }
            ),
            401,
        )
    user = get_current_user_from_token(tok)
    if not user:
        return (
            jsonify(
                {
                    "success": False,
                    "valid": False,
                    "error_code": "AUTH_002",
                    "message": "令牌无效或已过期",
                }
            ),
            401,
        )
    conn = get_db_connection()
    try:
        info = _user_info(conn, int(user["id"]))
        if not info:
            return (
                jsonify(
                    {
                        "success": False,
                        "valid": False,
                        "error_code": "AUTH_003",
                        "message": "用户不可用",
                    }
                ),
                401,
            )
        return jsonify({"success": True, "valid": True, "user": info})
    finally:
        conn.close()


@auth_bp.route("/auth/profile", methods=["GET"])
@require_auth
def profile():
    """当前登录用户信息（需 Bearer access token）。"""
    ensure_auth_schema()
    actor = request.auth_user  # type: ignore[attr-defined]
    uid = int(actor["id"])
    conn = get_db_connection()
    try:
        info = _user_info(conn, uid)
        if not info:
            return (
                jsonify(
                    {
                        "success": False,
                        "error_code": "AUTH_003",
                        "message": "用户不可用",
                    }
                ),
                401,
            )
        return jsonify({"success": True, "user": info})
    finally:
        conn.close()


@auth_bp.route("/auth/logout", methods=["POST"])
def logout():
    ensure_auth_schema()
    data = request.get_json(silent=True) or {}
    refresh_tok = data.get("token") or data.get("refresh_token")
    user_id: Optional[int] = None
    username: Optional[str] = None

    if refresh_tok:
        try:
            payload = jwt.decode(refresh_tok, _secret(), algorithms=[JWT_ALG])
            if payload.get("type") == "refresh":
                jti = payload.get("jti")
                user_id = int(payload["sub"]) if payload.get("sub") else None
                if jti and user_id:
                    conn = get_db_connection()
                    try:
                        conn.execute(
                            "UPDATE auth_refresh_tokens SET revoked = 1 WHERE user_id = ? AND jti = ?",
                            (user_id, jti),
                        )
                        conn.commit()
                    finally:
                        conn.close()
        except Exception:
            pass

    tok = get_bearer_token(request)
    if tok:
        try:
            p = decode_access_token(tok)
            user_id = int(p["sub"])
            username = p.get("username")
        except Exception:
            pass

    write_audit(
        user_id=user_id,
        username=username,
        action="logout",
        resource="/api/auth/logout",
        ip=request.remote_addr,
    )
    return jsonify({"success": True, "message": "已登出"})


@auth_bp.route("/auth/refresh", methods=["POST"])
def refresh():
    ensure_auth_schema()
    data = request.get_json(silent=True) or {}
    refresh_tok = data.get("refresh_token") or data.get("token")
    if not refresh_tok:
        return (
            jsonify(
                {
                    "success": False,
                    "error_code": "AUTH_006",
                    "message": "缺少 refresh_token",
                }
            ),
            400,
        )
    try:
        payload = jwt.decode(refresh_tok, _secret(), algorithms=[JWT_ALG])
    except Exception:
        return (
            jsonify(
                {
                    "success": False,
                    "error_code": "AUTH_007",
                    "message": "刷新令牌无效",
                }
            ),
            401,
        )
    if payload.get("type") != "refresh":
        return (
            jsonify(
                {
                    "success": False,
                    "error_code": "AUTH_007",
                    "message": "刷新令牌无效",
                }
            ),
            401,
        )
    user_id = int(payload["sub"])
    jti = payload.get("jti")
    conn = get_db_connection()
    try:
        row = conn.execute(
            """
            SELECT rt.id, rt.revoked, rt.expires_at, u.id AS uid, u.username,
                u.email, u.display_name, u.role_id, u.status, r.code AS role_code
            FROM auth_refresh_tokens rt
            JOIN auth_users u ON u.id = rt.user_id
            JOIN auth_roles r ON r.id = u.role_id
            WHERE rt.user_id = ? AND rt.jti = ?
            """,
            (user_id, jti),
        ).fetchone()
        if not row or row["revoked"]:
            return (
                jsonify(
                    {
                        "success": False,
                        "error_code": "AUTH_008",
                        "message": "刷新令牌已失效",
                    }
                ),
                401,
            )
        if row["status"] != "active":
            return (
                jsonify(
                    {
                        "success": False,
                        "error_code": "AUTH_003",
                        "message": "用户不可用",
                    }
                ),
                401,
            )
        conn.execute("UPDATE auth_refresh_tokens SET revoked = 1 WHERE id = ?", (row["id"],))
        conn.commit()
        access, new_refresh, perms = _issue_tokens(
            {
                "id": row["uid"],
                "username": row["username"],
                "role_id": row["role_id"],
            }
        )
        write_audit(
            user_id=user_id,
            username=row["username"],
            action="token_refresh",
            resource="/api/auth/refresh",
            ip=request.remote_addr,
        )
        return jsonify(
            {
                "success": True,
                "new_token": access,
                "token": access,
                "access_token": access,
                "refresh_token": new_refresh,
                "expires_in": ACCESS_TTL_SECONDS,
                "user_info": {
                    "id": user_id,
                    "username": row["username"],
                    "email": row["email"],
                    "display_name": (row["display_name"] or "").strip()
                    or row["username"],
                    "role": row["role_code"],
                    "permissions": perms,
                },
            }
        )
    finally:
        conn.close()


@auth_bp.route("/users", methods=["GET"])
@require_permissions(PERM_READ_USERS)
def list_users():
    ensure_auth_schema()
    role_filter = request.args.get("role")
    status_filter = request.args.get("status")
    page, limit = _pagination_params()
    offset = (page - 1) * limit
    where = ["1=1"]
    params: list[Any] = []
    if role_filter:
        where.append("r.code = ?")
        params.append(role_filter)
    if status_filter:
        where.append("u.status = ?")
        params.append(status_filter)
    where_sql = " AND ".join(where)
    conn = get_db_connection()
    try:
        total = conn.execute(
            f"SELECT COUNT(*) FROM auth_users u JOIN auth_roles r ON r.id = u.role_id WHERE {where_sql}",
            params,
        ).fetchone()[0]
        rows = conn.execute(
            f"""
            SELECT u.id, u.username, u.email, u.display_name, u.status, u.created_at, r.code AS role
            FROM auth_users u
            JOIN auth_roles r ON r.id = u.role_id
            WHERE {where_sql}
            ORDER BY u.id
            LIMIT ? OFFSET ?
            """,
            (*params, limit, offset),
        ).fetchall()
        users = [dict(r) for r in rows]
        return jsonify(
            {
                "success": True,
                "data": {"users": users},
                "users": users,
                "pagination": _paginate_meta(total, page, limit),
            }
        )
    finally:
        conn.close()


@auth_bp.route("/users/<int:user_id>", methods=["GET"])
@require_auth
def get_user(user_id: int):
    ensure_auth_schema()
    actor = request.auth_user  # type: ignore[attr-defined]
    actor_id = int(actor["id"])
    conn = get_db_connection()
    try:
        perms = set(permission_codes_for_user(conn, actor_id))
        if user_id != actor_id and PERM_READ_USERS not in perms:
            return (
                jsonify(
                    {
                        "success": False,
                        "error_code": "AUTH_403",
                        "message": "权限不足",
                    }
                ),
                403,
            )
        row = conn.execute(
            """
            SELECT u.id, u.username, u.email, u.display_name, u.status, u.created_at, u.updated_at, r.code AS role
            FROM auth_users u
            JOIN auth_roles r ON r.id = u.role_id
            WHERE u.id = ?
            """,
            (user_id,),
        ).fetchone()
        if not row:
            return (
                jsonify(
                    {
                        "success": False,
                        "error_code": "USER_001",
                        "message": "用户不存在",
                    }
                ),
                404,
            )
        return jsonify({"success": True, "user": dict(row)})
    finally:
        conn.close()


@auth_bp.route("/users/<int:user_id>", methods=["PUT"])
@require_auth
def update_user(user_id: int):
    ensure_auth_schema()
    actor = request.auth_user  # type: ignore[attr-defined]
    actor_id = int(actor["id"])
    data = request.get_json(silent=True) or {}
    conn = get_db_connection()
    try:
        perms = set(permission_codes_for_user(conn, actor_id))
        is_admin = PERM_WRITE_USERS in perms
        if user_id != actor_id and not is_admin:
            return (
                jsonify(
                    {
                        "success": False,
                        "error_code": "AUTH_403",
                        "message": "权限不足",
                    }
                ),
                403,
            )
        row = conn.execute(
            "SELECT id, password_hash FROM auth_users WHERE id = ?", (user_id,)
        ).fetchone()
        if not row:
            return (
                jsonify(
                    {
                        "success": False,
                        "error_code": "USER_001",
                        "message": "用户不存在",
                    }
                ),
                404,
            )

        updates: dict[str, Any] = {}
        if "email" in data:
            updates["email"] = data.get("email")
        if "display_name" in data and (
            user_id == actor_id or is_admin
        ):
            dn = (data.get("display_name") or "").strip()
            if dn:
                updates["display_name"] = dn
        if "status" in data and is_admin:
            updates["status"] = data.get("status")
        if "role" in data and is_admin:
            rc = data.get("role")
            rrow = conn.execute(
                "SELECT id FROM auth_roles WHERE code = ?", (rc,)
            ).fetchone()
            if not rrow:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error_code": "USER_VAL_001",
                            "message": "无效角色",
                        }
                    ),
                    400,
                )
            updates["role_id"] = rrow["id"]
        new_pw = data.get("password")
        if new_pw:
            if user_id != actor_id and not is_admin:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error_code": "AUTH_403",
                            "message": "仅管理员可重置他人密码",
                        }
                    ),
                    403,
                )
            updates["password_hash"] = generate_password_hash(str(new_pw))

        if not updates:
            return jsonify({"success": True, "message": "无变更"})

        sets = [f"{k} = ?" for k in updates]
        vals = list(updates.values())
        vals.append(user_id)
        conn.execute(
            f"UPDATE auth_users SET {', '.join(sets)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            vals,
        )
        conn.commit()
        write_audit(
            user_id=actor_id,
            username=str(actor.get("username")),
            action="user_update",
            resource=f"/api/users/{user_id}",
            details={"fields": list(updates.keys())},
            ip=request.remote_addr,
        )
        return jsonify({"success": True, "message": "更新成功"})
    finally:
        conn.close()


@auth_bp.route("/roles", methods=["GET"])
@require_auth
def list_roles():
    ensure_auth_schema()
    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT id, code, name, description FROM auth_roles ORDER BY id"
        ).fetchall()
        return jsonify({"success": True, "roles": [dict(r) for r in rows]})
    finally:
        conn.close()


@auth_bp.route("/permissions", methods=["GET"])
@require_auth
def list_permissions():
    ensure_auth_schema()
    role_id = request.args.get("role_id")
    conn = get_db_connection()
    try:
        if role_id is not None and str(role_id).strip() != "":
            try:
                rid = int(role_id)
            except (TypeError, ValueError):
                return (
                    jsonify(
                        {
                            "success": False,
                            "error_code": "AUTH_VAL_005",
                            "message": "role_id 无效",
                        }
                    ),
                    400,
                )
            rows = conn.execute(
                """
                SELECT p.id, p.code, p.description
                FROM auth_permissions p
                JOIN auth_role_permissions rp ON rp.permission_id = p.id
                WHERE rp.role_id = ?
                ORDER BY p.code
                """,
                (rid,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, code, description FROM auth_permissions ORDER BY code"
            ).fetchall()
        return jsonify({"success": True, "permissions": [dict(r) for r in rows]})
    finally:
        conn.close()


@auth_bp.route("/users/<int:user_id>/permissions", methods=["GET"])
@require_auth
def user_permissions(user_id: int):
    ensure_auth_schema()
    actor = request.auth_user  # type: ignore[attr-defined]
    actor_id = int(actor["id"])
    conn = get_db_connection()
    try:
        perms_actor = set(permission_codes_for_user(conn, actor_id))
        if user_id != actor_id and PERM_READ_USERS not in perms_actor:
            return (
                jsonify(
                    {
                        "success": False,
                        "error_code": "AUTH_403",
                        "message": "权限不足",
                    }
                ),
                403,
            )
        codes = permission_codes_for_user(conn, user_id)
        return jsonify({"success": True, "permissions": [{"code": c} for c in codes]})
    finally:
        conn.close()


@auth_bp.route("/audit/logs", methods=["GET"])
@require_permissions(PERM_READ_AUDIT)
def audit_logs():
    ensure_auth_schema()
    page, limit = _pagination_params()
    offset = (page - 1) * limit
    user_id = request.args.get("user_id")
    action = request.args.get("action")
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    where = ["1=1"]
    params: list[Any] = []
    if user_id:
        where.append("user_id = ?")
        params.append(int(user_id))
    if action:
        where.append("action LIKE ?")
        params.append(f"%{action}%")
    if date_from:
        where.append("created_at >= ?")
        params.append(date_from)
    if date_to:
        where.append("created_at <= ?")
        params.append(date_to)
    where_sql = " AND ".join(where)
    conn = get_db_connection()
    try:
        total = conn.execute(
            f"SELECT COUNT(*) FROM auth_audit_logs WHERE {where_sql}", params
        ).fetchone()[0]
        rows = conn.execute(
            f"""
            SELECT id, user_id, username, action, resource, details, ip, created_at
            FROM auth_audit_logs
            WHERE {where_sql}
            ORDER BY id DESC
            LIMIT ? OFFSET ?
            """,
            (*params, limit, offset),
        ).fetchall()
        logs = []
        for r in rows:
            d = dict(r)
            if d.get("details"):
                try:
                    d["details"] = json.loads(d["details"])
                except json.JSONDecodeError:
                    pass
            logs.append(d)
        return jsonify(
            {
                "success": True,
                "logs": logs,
                "pagination": _paginate_meta(total, page, limit),
            }
        )
    finally:
        conn.close()


@auth_bp.route("/audit/stats", methods=["GET"])
@require_permissions(PERM_READ_AUDIT)
def audit_stats():
    ensure_auth_schema()
    period = request.args.get("period", "7d")
    conn = get_db_connection()
    try:
        cutoff_clause = ""
        if period.endswith("d"):
            try:
                days = int(period[:-1] or "7")
            except ValueError:
                days = 7
            cutoff_clause = f"WHERE created_at >= datetime('now', '-{days} days')"
        total = conn.execute(
            f"SELECT COUNT(*) FROM auth_audit_logs {cutoff_clause}"
        ).fetchone()[0]
        by_action = conn.execute(
            f"""
            SELECT action, COUNT(*) AS c
            FROM auth_audit_logs
            {cutoff_clause}
            GROUP BY action
            ORDER BY c DESC
            LIMIT 20
            """
        ).fetchall()
        return jsonify(
            {
                "success": True,
                "stats": {
                    "period": period,
                    "total_events": total,
                    "by_action": [dict(r) for r in by_action],
                },
            }
        )
    finally:
        conn.close()
