"""
数据库连接与初始化工具 - 与 database/connection.py 保持同步
"""

import sqlite3
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
    _add_column_if_not_exists(conn, "inventory", "generic_name", "TEXT DEFAULT ''")
    _add_column_if_not_exists(conn, "inventory", "description", "TEXT DEFAULT ''")
    _add_column_if_not_exists(conn, "inventory", "manufacturer", "TEXT DEFAULT ''")
    _add_column_if_not_exists(conn, "inventory", "specification", "TEXT DEFAULT ''")
    _add_column_if_not_exists(conn, "inventory", "dosage_form", "TEXT DEFAULT ''")
    _add_column_if_not_exists(conn, "inventory", "unit", "TEXT DEFAULT ''")
    _add_column_if_not_exists(conn, "inventory", "pack_size", "TEXT DEFAULT ''")
    _add_column_if_not_exists(conn, "inventory", "approval_number", "TEXT DEFAULT ''")
    _add_column_if_not_exists(conn, "inventory", "barcode", "TEXT DEFAULT ''")
    _add_column_if_not_exists(conn, "inventory", "storage_condition", "TEXT DEFAULT ''")
    _add_column_if_not_exists(conn, "inventory", "usage_dosage", "TEXT DEFAULT ''")
    _add_column_if_not_exists(conn, "inventory", "contraindications", "TEXT DEFAULT ''")
    _add_column_if_not_exists(conn, "inventory", "side_effects", "TEXT DEFAULT ''")
    _add_column_if_not_exists(conn, "inventory", "interaction_warning", "TEXT DEFAULT ''")
    _add_column_if_not_exists(conn, "inventory", "pregnancy_category", "TEXT DEFAULT ''")
    _add_column_if_not_exists(conn, "inventory", "pediatric_caution", "TEXT DEFAULT ''")
    _add_column_if_not_exists(conn, "inventory", "supplier", "TEXT DEFAULT ''")
    _add_column_if_not_exists(conn, "inventory", "country_of_origin", "TEXT DEFAULT ''")
    _add_column_if_not_exists(conn, "inventory", "cost_price", "REAL DEFAULT 0")
    _add_column_if_not_exists(conn, "inventory", "min_stock_alert", "INTEGER DEFAULT 0")
    _add_column_if_not_exists(conn, "inventory", "image_url", "TEXT DEFAULT ''")
    _add_column_if_not_exists(conn, "inventory", "is_deleted", "INTEGER DEFAULT 0")
    _add_column_if_not_exists(conn, "inventory", "created_at", "TEXT DEFAULT ''")
    _add_column_if_not_exists(conn, "inventory", "updated_at", "TEXT DEFAULT ''")
    # 第一周：药品表扩展字段迁移
    _add_column_if_not_exists(conn, "inventory", "strength", "TEXT DEFAULT ''")
    _add_column_if_not_exists(conn, "inventory", "drug_interactions", "TEXT DEFAULT '[]'")
    _add_column_if_not_exists(conn, "inventory", "age_restrictions", "TEXT DEFAULT '{}'")
    _add_column_if_not_exists(conn, "inventory", "min_stock_level", "INTEGER DEFAULT 10")
    _add_column_if_not_exists(conn, "inventory", "max_stock_level", "INTEGER DEFAULT 500")
    _add_column_if_not_exists(conn, "inventory", "purchase_price", "REAL DEFAULT 0.0")

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

    # --- categories（药品分类，树形结构） ---
    # name 与 inventory.category 字段的字符串值保持一致，JOIN 条件为 inventory.category = categories.name
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL UNIQUE,
            description TEXT    DEFAULT '',
            parent_id   INTEGER DEFAULT NULL,
            sort_order  INTEGER DEFAULT 0,
            created_at  TEXT    DEFAULT '',
            FOREIGN KEY (parent_id) REFERENCES categories(id)
        )
    """)
    _add_index_if_not_exists(conn, "idx_categories_name",
        "CREATE INDEX idx_categories_name ON categories(name)")
    _add_index_if_not_exists(conn, "idx_categories_parent_id",
        "CREATE INDEX idx_categories_parent_id ON categories(parent_id)")
    # 迁移：已有数据库补 description 列
    _add_column_if_not_exists(conn, "categories", "description", "TEXT DEFAULT ''")

    # --- inventory_transactions（库存调整审计记录） ---
    # 组件1 第2周：记录每次库存变化，供组件2的库存调整API写入
    # transaction_type: 'in'=入库, 'out'=出库, 'adjust'=手动调整, 'expire'=过期报废
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory_transactions (
            transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            drug_id INTEGER NOT NULL,
            quantity_change INTEGER NOT NULL,
            transaction_type TEXT NOT NULL DEFAULT 'adjust',
            before_quantity INTEGER DEFAULT 0,
            after_quantity INTEGER DEFAULT 0,
            reason TEXT DEFAULT '',
            operator TEXT DEFAULT '',
            created_at TEXT DEFAULT '',
            FOREIGN KEY (drug_id) REFERENCES inventory(drug_id)
        )
    """)
    _add_index_if_not_exists(conn, "idx_inv_tx_drug_id",
        "CREATE INDEX idx_inv_tx_drug_id ON inventory_transactions(drug_id)")
    _add_index_if_not_exists(conn, "idx_inv_tx_created_at",
        "CREATE INDEX idx_inv_tx_created_at ON inventory_transactions(created_at)")
    _add_index_if_not_exists(conn, "idx_inv_tx_transaction_type",
        "CREATE INDEX idx_inv_tx_transaction_type ON inventory_transactions(transaction_type)")

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

    # --- screening_history（智能筛选历史） ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS screening_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            input_symptoms TEXT NOT NULL,
            patient_info TEXT DEFAULT '{}',
            filters TEXT DEFAULT '{}',
            result_drugs TEXT DEFAULT '[]',
            result_count INTEGER DEFAULT 0,
            confidence_scores TEXT DEFAULT '{}',
            execution_time REAL DEFAULT 0.0,
            status TEXT DEFAULT 'success',
            request_id TEXT,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    _add_index_if_not_exists(conn, "idx_sh_user_id",
        "CREATE INDEX idx_sh_user_id ON screening_history(user_id)")
    _add_index_if_not_exists(conn, "idx_sh_created_at",
        "CREATE INDEX idx_sh_created_at ON screening_history(created_at)")

    # --- screening_config（智能筛选配置） ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS screening_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            config_name TEXT NOT NULL UNIQUE,
            config_json TEXT NOT NULL DEFAULT '{}',
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
