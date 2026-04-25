"""
数据库连接模块 - 提供统一的数据库连接和初始化功能
"""

import sqlite3
import json
import os
from datetime import date, datetime
from typing import Any, Dict, Optional, Union

from common.config import Config


def get_db_connection() -> sqlite3.Connection:
    """获取数据库连接"""
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _add_column_if_not_exists(conn, table, column, col_type_with_default):
    cursor = conn.execute(f"PRAGMA table_info({table})")
    existing = {row[1] for row in cursor.fetchall()}
    if column not in existing:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type_with_default}")


def _add_index_if_not_exists(conn, index_name, sql):
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='index' AND name=?", (index_name,))
    if not cursor.fetchone():
        conn.execute(sql)


def init_database() -> None:
    """初始化数据库表结构"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # --- inventory（药品库存） ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            drug_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            expiry_date INTEGER NOT NULL,
            shelf_x INTEGER NOT NULL,
            shelf_y INTEGER NOT NULL,
            shelve_id INTEGER NOT NULL
        )
    """)
    _add_column_if_not_exists(conn, "inventory", "category", "TEXT DEFAULT ''")
    _add_column_if_not_exists(conn, "inventory", "is_prescription", "INTEGER DEFAULT 0")
    _add_column_if_not_exists(conn, "inventory", "retail_price", "REAL DEFAULT 0.0")
    _add_column_if_not_exists(conn, "inventory", "stock", "INTEGER DEFAULT 0")

    # --- drug_indications（药品适应症） ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS drug_indications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            drug_id INTEGER NOT NULL,
            indication TEXT NOT NULL,
            FOREIGN KEY (drug_id) REFERENCES inventory(drug_id)
        )
    """)
    _add_index_if_not_exists(conn, "idx_di_drug_id",
        "CREATE INDEX idx_di_drug_id ON drug_indications(drug_id)")
    _add_index_if_not_exists(conn, "idx_di_indication",
        "CREATE INDEX idx_di_indication ON drug_indications(indication)")

    # --- symptom_synonyms（症状同义词） ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS symptom_synonyms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            standard_term TEXT NOT NULL,
            synonym TEXT NOT NULL,
            match_type TEXT DEFAULT 'similar',
            UNIQUE(standard_term, synonym)
        )
    """)
    _add_index_if_not_exists(conn, "idx_ss_synonym",
        "CREATE INDEX idx_ss_synonym ON symptom_synonyms(synonym)")

    # --- order_log（订单日志） ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_log (
            task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            status TEXT NOT NULL,
            target_drug_id INTEGER,
            quantity INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (target_drug_id) REFERENCES inventory(drug_id)
        )
    """)

    # --- approvals（审批表） ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS approvals (
            id TEXT PRIMARY KEY,
            patient_name TEXT NOT NULL,
            patient_age INTEGER,
            patient_weight REAL,
            symptoms TEXT,
            advice TEXT NOT NULL,
            drug_name TEXT,
            drug_type TEXT,
            quantity INTEGER DEFAULT 1,
            status TEXT NOT NULL,
            doctor_id TEXT,
            reject_reason TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            approved_at DATETIME
        )
    """)

    # --- app_meta（元数据） ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS app_meta (
            k TEXT PRIMARY KEY,
            v TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()
    print("Database initialized successfully")


def json_serializer(obj: Any) -> str:
    """JSON 序列化辅助函数"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def close_db_connection(conn: sqlite3.Connection) -> None:
    """关闭数据库连接"""
    if conn:
        conn.close()
