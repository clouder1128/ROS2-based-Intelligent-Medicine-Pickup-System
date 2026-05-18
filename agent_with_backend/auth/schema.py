"""建表、种子数据（角色/权限）。"""

from __future__ import annotations

import os
import sqlite3

from werkzeug.security import generate_password_hash

from auth.constants import (
    ALL_PERMISSION_CODES,
    PERMISSION_DESCRIPTIONS,
    ROLE_ADMIN,
    ROLE_DOCTOR,
    ROLE_PATIENT,
    ROLE_PHARMACIST,
    ROLE_PERMISSION_MAP,
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
                display_name TEXT NOT NULL DEFAULT '',
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
        _migrate_legacy_auth(conn)
        _seed_rbac_if_empty(conn)
        _sync_permissions_and_role_mappings(conn)
        _ensure_default_admin_if_configured(conn)
    finally:
        if own:
            conn.close()


def _migrate_legacy_auth(conn: sqlite3.Connection) -> None:
    """兼容旧库：补 display_name；角色 code user→patient；文档对齐视图 users。"""
    c = conn.cursor()
    cols = {r[1] for r in c.execute("PRAGMA table_info(auth_users)").fetchall()}
    if "display_name" not in cols:
        c.execute(
            "ALTER TABLE auth_users ADD COLUMN display_name TEXT NOT NULL DEFAULT ''"
        )
        conn.commit()
    c.execute(
        """
        UPDATE auth_users
        SET display_name = username
        WHERE display_name IS NULL OR trim(display_name) = ''
        """
    )
    row = c.execute(
        "SELECT id FROM auth_roles WHERE code = ?", ("user",)
    ).fetchone()
    if row:
        c.execute(
            """
            UPDATE auth_roles
            SET code = ?, name = ?, description = ?
            WHERE code = 'user'
            """,
            (ROLE_PATIENT, "患者", "患者/普通用户"),
        )
        conn.commit()
    c.execute("DROP VIEW IF EXISTS users")
    c.execute(
        """
        CREATE VIEW users AS
        SELECT
            u.id AS id,
            u.username AS username,
            u.password_hash AS password_hash,
            r.code AS role,
            u.display_name AS display_name,
            u.created_at AS created_at
        FROM auth_users u
        JOIN auth_roles r ON r.id = u.role_id
        WHERE r.code IN ('admin', 'doctor', 'pharmacist', 'patient')
        """
    )
    conn.commit()


def _sync_permissions_and_role_mappings(conn: sqlite3.Connection) -> None:
    """补齐权限码并按 ROLE_PERMISSION_MAP 同步角色—权限（与分工文档矩阵一致）。"""
    c = conn.cursor()
    for code in ALL_PERMISSION_CODES:
        desc = PERMISSION_DESCRIPTIONS.get(code, code)
        c.execute(
            "INSERT OR IGNORE INTO auth_permissions (code, description) VALUES (?, ?)",
            (code, desc),
        )
    conn.commit()

    code_to_pid = {
        r[0]: r[1] for r in c.execute("SELECT code, id FROM auth_permissions").fetchall()
    }

    for role_code, perm_codes in ROLE_PERMISSION_MAP.items():
        row = c.execute(
            "SELECT id FROM auth_roles WHERE code = ?", (role_code,)
        ).fetchone()
        if not row:
            continue
        rid = row[0]
        want_pids = []
        for pc in perm_codes:
            pid = code_to_pid.get(pc)
            if pid is not None:
                want_pids.append(pid)
        want_set = set(want_pids)

        existing = c.execute(
            "SELECT permission_id FROM auth_role_permissions WHERE role_id = ?",
            (rid,),
        ).fetchall()
        for (epid,) in existing:
            if epid not in want_set:
                c.execute(
                    "DELETE FROM auth_role_permissions WHERE role_id = ? AND permission_id = ?",
                    (rid, epid),
                )
        for pid in want_pids:
            c.execute(
                "INSERT OR IGNORE INTO auth_role_permissions (role_id, permission_id) VALUES (?, ?)",
                (rid, pid),
            )
    conn.commit()


def _seed_rbac_if_empty(conn: sqlite3.Connection) -> None:
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM auth_roles")
    if c.fetchone()[0] > 0:
        return

    roles = [
        (ROLE_ADMIN, "管理员", "系统管理员，全部权限"),
        (ROLE_PHARMACIST, "药剂师", "药品与库存维护"),
        (ROLE_DOCTOR, "医生", "药品查询"),
        (ROLE_PATIENT, "患者", "患者/普通用户"),
    ]
    c.executemany(
        "INSERT INTO auth_roles (code, name, description) VALUES (?, ?, ?)", roles
    )

    perm_rows = [
        (code, PERMISSION_DESCRIPTIONS[code]) for code in ALL_PERMISSION_CODES
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
        INSERT INTO auth_users (username, email, password_hash, display_name, role_id, status)
        VALUES (?, ?, ?, ?, ?, 'active')
        """,
        (
            os.environ.get("AUTH_DEFAULT_ADMIN_USER", "admin"),
            os.environ.get("AUTH_DEFAULT_ADMIN_EMAIL", "admin@local"),
            generate_password_hash(pwd),
            (
                os.environ.get("AUTH_DEFAULT_ADMIN_DISPLAY_NAME", "").strip()
                or os.environ.get("AUTH_DEFAULT_ADMIN_USER", "admin")
            ),
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
