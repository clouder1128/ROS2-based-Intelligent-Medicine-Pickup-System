"""建表、种子数据（角色/权限）。"""

from __future__ import annotations

import os
import sqlite3

from werkzeug.security import generate_password_hash

from auth.constants import (
    ROLE_ADMIN,
    ROLE_DOCTOR,
    ROLE_PHARMACIST,
    ROLE_PERMISSION_MAP,
    ROLE_USER,
)
from auth.db import get_db_connection


def ensure_auth_schema(conn: sqlite3.Connection | None = None) -> None:
    own = conn is None
    if own:
        conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS auth_roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT
            )
            """
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS auth_permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                description TEXT
            )
            """
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS auth_role_permissions (
                role_id INTEGER NOT NULL,
                permission_id INTEGER NOT NULL,
                PRIMARY KEY (role_id, permission_id),
                FOREIGN KEY (role_id) REFERENCES auth_roles(id) ON DELETE CASCADE,
                FOREIGN KEY (permission_id) REFERENCES auth_permissions(id) ON DELETE CASCADE
            )
            """
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS auth_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL COLLATE NOCASE,
                email TEXT COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                role_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (role_id) REFERENCES auth_roles(id)
            )
            """
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS auth_refresh_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                jti TEXT UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                revoked INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES auth_users(id) ON DELETE CASCADE
            )
            """
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS auth_audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                action TEXT NOT NULL,
                resource TEXT,
                details TEXT,
                ip TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        c.execute(
            "CREATE INDEX IF NOT EXISTS idx_audit_user ON auth_audit_logs(user_id)"
        )
        c.execute(
            "CREATE INDEX IF NOT EXISTS idx_audit_created ON auth_audit_logs(created_at)"
        )
        conn.commit()
        _seed_rbac_if_empty(conn)
        _ensure_default_admin_if_configured(conn)
    finally:
        if own:
            conn.close()


def _seed_rbac_if_empty(conn: sqlite3.Connection) -> None:
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM auth_roles")
    if c.fetchone()[0] > 0:
        return

    roles = [
        (ROLE_ADMIN, "管理员", "系统管理员，全部权限"),
        (ROLE_PHARMACIST, "药剂师", "药品与库存维护"),
        (ROLE_DOCTOR, "医生", "药品查询"),
        (ROLE_USER, "普通用户", "基础查询"),
    ]
    c.executemany(
        "INSERT INTO auth_roles (code, name, description) VALUES (?, ?, ?)", roles
    )

    perm_rows = [
        ("read:drug", "读取药品"),
        ("create:drug", "创建药品"),
        ("update:drug", "更新药品"),
        ("delete:drug", "删除药品"),
        ("read:inventory", "读取库存"),
        ("update:inventory", "调整库存"),
        ("read:users", "查询用户"),
        ("write:users", "维护用户"),
        ("read:audit", "审计日志"),
    ]
    c.executemany(
        "INSERT INTO auth_permissions (code, description) VALUES (?, ?)",
        perm_rows,
    )

    code_to_pid = {
        r[0]: r[1]
        for r in c.execute("SELECT code, id FROM auth_permissions").fetchall()
    }
    code_to_rid = {
        r[0]: r[1] for r in c.execute("SELECT code, id FROM auth_roles").fetchall()
    }

    rp_pairs: list[tuple[int, int]] = []
    for role_code, perms in ROLE_PERMISSION_MAP.items():
        rid = code_to_rid[role_code]
        for p in perms:
            rp_pairs.append((rid, code_to_pid[p]))
    c.executemany(
        "INSERT INTO auth_role_permissions (role_id, permission_id) VALUES (?, ?)",
        rp_pairs,
    )
    conn.commit()


def _ensure_default_admin_if_configured(conn: sqlite3.Connection) -> None:
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM auth_users")
    if c.fetchone()[0] > 0:
        return
    pwd = os.environ.get("AUTH_DEFAULT_ADMIN_PASSWORD", "").strip()
    if not pwd:
        return
    row = c.execute(
        "SELECT id FROM auth_roles WHERE code = ?", (ROLE_ADMIN,)
    ).fetchone()
    if not row:
        return
    c.execute(
        """
        INSERT INTO auth_users (username, email, password_hash, role_id, status)
        VALUES (?, ?, ?, ?, 'active')
        """,
        (
            os.environ.get("AUTH_DEFAULT_ADMIN_USER", "admin"),
            os.environ.get("AUTH_DEFAULT_ADMIN_EMAIL", "admin@local"),
            generate_password_hash(pwd),
            row[0],
        ),
    )
    conn.commit()


def permission_codes_for_user(conn: sqlite3.Connection, user_id: int) -> list[str]:
    cur = conn.execute(
        """
        SELECT DISTINCT ap.code
        FROM auth_users u
        JOIN auth_role_permissions rp ON rp.role_id = u.role_id
        JOIN auth_permissions ap ON ap.id = rp.permission_id
        WHERE u.id = ? AND u.status = 'active'
        ORDER BY ap.code
        """,
        (user_id,),
    )
    return [r[0] for r in cur.fetchall()]
