"""
初始用户种子脚本 - 创建演示用户（patient1/doctor1/admin1）
在已有 auth 表结构（auth_users / auth_roles）中插入数据，
可安全重复运行（INSERT OR IGNORE）。

用法：
    python3 -m database.scripts.seed_users
    # 或在 init_db 之后运行
"""

import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash

# 查找数据库路径
_DB_PATH = (
    Path(__file__).resolve().parent.parent.parent / "pharmacy.db"
)


def _get_role_id(conn: sqlite3.Connection, code: str) -> int | None:
    row = conn.execute(
        "SELECT id FROM auth_roles WHERE code = ?", (code,)
    ).fetchone()
    return row[0] if row else None


def seed_users(db_path: str | Path = _DB_PATH) -> None:
    if not Path(db_path).exists():
        print(f"[seed_users] 数据库文件不存在: {db_path}")
        print("[seed_users] 请先运行 python3 -m database.scripts.init_db")
        return

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        admin_id = _get_role_id(conn, "admin")
        doctor_id = _get_role_id(conn, "doctor")
        patient_id = _get_role_id(conn, "patient")

        if not all([admin_id, doctor_id, patient_id]):
            print("[seed_users] 角色数据不完整，请先执行 init_db / auth schema 初始化")
            return

        # 如果已有用户则跳过（安全可重复运行通过 OR IGNORE 处理 username 冲突）
        users = [
            ("admin1", "admin1@local", "陈管理员", admin_id, "active"),
            ("doctor1", "doctor1@local", "王医生", doctor_id, "active"),
            ("doctor2", "doctor2@local", "赵医生", doctor_id, "active"),
            ("patient1", "patient1@local", "张患者", patient_id, "active"),
            ("patient2", "patient2@local", "李患者", patient_id, "active"),
        ]

        password = generate_password_hash("123456")
        inserted = 0
        for username, email, display_name, role_id, status in users:
            try:
                conn.execute(
                    """
                    INSERT INTO auth_users (username, email, password_hash, display_name, role_id, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (username, email, password, display_name, role_id, status),
                )
                inserted += 1
            except sqlite3.IntegrityError:
                pass  # 用户名已存在，跳过

        conn.commit()
        print(f"[seed_users] 完成: 新增 {inserted} 用户（已存在则跳过）")
        print(f"[seed_users] 演示账号: patient1/doctor1/admin1  密码: 123456")

    finally:
        conn.close()


if __name__ == "__main__":
    seed_users()
    print("[seed_users] 数据库文件:", _DB_PATH)
