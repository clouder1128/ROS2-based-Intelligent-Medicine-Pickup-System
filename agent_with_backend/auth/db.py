"""SQLite 连接：与 common.config / 主业务库共用 DATABASE_PATH。"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from common.config import Config


def get_database_path() -> str:
    return Config.DATABASE_PATH


def get_db_connection() -> sqlite3.Connection:
    path = Path(get_database_path())
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
