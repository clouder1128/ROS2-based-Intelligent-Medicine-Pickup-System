"""
数据库初始化脚本
创建 inventory（药品表）、drug_indications（适应症表）、
symptom_synonyms（症状同义词表）、order_log（订单表）、
app_meta（元数据表），并插入基础数据。
"""

import os
import sqlite3
from datetime import date
from common.config import Config

DB_PATH = Config.DATABASE_PATH


def _add_column_if_not_exists(conn, table, column, col_type_with_default):
    """安全添加列（SQLite 不支持 IF NOT EXISTS for ADD COLUMN）"""
    cursor = conn.execute(f"PRAGMA table_info({table})")
    existing = {row[1] for row in cursor.fetchall()}
    if column not in existing:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type_with_default}")


def _add_index_if_not_exists(conn, index_name, sql):
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='index' AND name=?", (index_name,))
    if not cursor.fetchone():
        conn.execute(sql)


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")   # 启用外键约束（SQLite 默认关闭）
    c = conn.cursor()

    # ========== 建表 ==========
    # 注：认证相关表（auth_users / auth_roles / auth_permissions 等）
    # 由 auth.schema.ensure_auth_schema() 负责建立，main.py 启动时自动调用，
    # 无需在本脚本中重复。users 视图亦在 ensure_auth_schema() 中创建。

    c.execute("""
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

    # 兼容迁移：已有表时补充新列
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

    c.execute("""
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

    c.execute("""
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
    c.execute("""
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
    # transaction_type: 'in'=入库, 'out'=出库, 'adjust'=手动调整, 'expire'=过期报废
    c.execute("""
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

    # --- approvals（处方审批） ---
    c.execute("""
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

    c.execute("""
        CREATE TABLE IF NOT EXISTS order_log (
            task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            status TEXT NOT NULL,
            target_drug_id INTEGER,
            quantity INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (target_drug_id) REFERENCES inventory(drug_id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS app_meta (
            k TEXT PRIMARY KEY,
            v TEXT NOT NULL
        )
    """)

    conn.commit()

    # ========== 基础种子数据 ==========

    # 仅在 inventory 为空时写入基础数据
    c.execute("SELECT COUNT(*) FROM inventory")
    if c.fetchone()[0] == 0:
        base_drugs = [
            (1, '阿莫西林', 50, 365, 1, 1, 1, '抗生素', 1, 25.0),
            (2, '布洛芬', 30, 180, 1, 2, 1, '解热镇痛抗炎药', 0, 15.0),
            (3, '维生素C', 100, 0, 2, 1, 2, '维生素矿物质', 0, 5.0),
        ]
        for d in base_drugs:
            c.execute("""
                INSERT INTO inventory (drug_id, name, quantity, expiry_date,
                    shelf_x, shelf_y, shelve_id, category, is_prescription, retail_price)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, d)

        conn.commit()

    # 基础适应症
    c.execute("SELECT COUNT(*) FROM drug_indications")
    if c.fetchone()[0] == 0:
        base_indications = [
            (1, '感冒'), (1, '发热'), (1, '发烧'), (1, '呼吸道感染'),
            (1, '扁桃体炎'), (1, '中耳炎'),
            (2, '头痛'), (2, '头疼'), (2, '牙痛'), (2, '关节痛'),
            (2, '痛经'), (2, '发热'), (2, '发烧'), (2, '肌肉痛'),
            (3, '免疫力低下'), (3, '坏血病'),
        ]
        c.executemany(
            "INSERT INTO drug_indications (drug_id, indication) VALUES (?, ?)",
            base_indications
        )
        conn.commit()

    # 基础同义词
    c.execute("SELECT COUNT(*) FROM symptom_synonyms")
    if c.fetchone()[0] == 0:
        base_synonyms = [
            ('头痛', '头疼', 'similar'),
            ('头痛', '偏头痛', 'related'),
            ('头痛', '脑袋疼', 'related'),
            ('头痛', '头部胀痛', 'related'),
            ('发热', '发烧', 'similar'),
            ('发热', '体温高', 'related'),
            ('发热', '身体发烫', 'related'),
            ('腹泻', '拉肚子', 'similar'),
            ('腹泻', '拉稀', 'similar'),
            ('腹痛', '肚子痛', 'similar'),
            ('腹痛', '胃痛', 'related'),
            ('恶心', '想吐', 'similar'),
            ('呕吐', '吐了', 'similar'),
            ('失眠', '睡不着', 'similar'),
            ('失眠', '入睡困难', 'similar'),
            ('咳嗽', '咳', 'similar'),
            ('咳嗽', '干咳', 'similar'),
            ('便秘', '排便困难', 'similar'),
            ('头晕', '眩晕', 'related'),
            ('头晕', '头昏', 'similar'),
            ('过敏', '皮肤过敏', 'related'),
            ('过敏', '起疹子', 'related'),
            ('瘙痒', '皮肤痒', 'similar'),
            ('关节痛', '关节疼', 'similar'),
            ('肌肉痛', '肌肉酸痛', 'similar'),
            ('咽喉痛', '喉咙痛', 'similar'),
            ('咽喉痛', '嗓子疼', 'similar'),
            ('咽喉痛', '喉咙发炎', 'related'),
            ('流鼻涕', '流鼻水', 'similar'),
            ('鼻塞', '鼻子不通', 'similar'),
        ]
        c.executemany(
            "INSERT INTO symptom_synonyms (standard_term, synonym, match_type) VALUES (?, ?, ?)",
            base_synonyms
        )
        conn.commit()

    # 基础分类（与 inventory.category 字段值完全对齐）
    # INSERT OR IGNORE：重复运行安全，不会破坏已有数据
    base_categories = [
        # (name, parent_id, sort_order)
        ('解热镇痛抗炎药',  None, 1),
        ('抗生素抗感染药',  None, 2),
        ('消化系统药',      None, 3),
        ('心血管药',        None, 4),
        ('呼吸系统药',      None, 5),
        ('神经系统药',      None, 6),
        ('维生素矿物质',    None, 7),
        ('外用药皮肤科',    None, 8),
        ('内分泌代谢药',    None, 9),
        ('抗过敏药',        None, 10),
        ('中成药感冒类',    None, 11),
        ('其他专科药',      None, 12),
        # init_db.py base seed 中阿莫西林用的是'抗生素'，单独保留以兼容旧数据
        ('抗生素',          None, 13),
    ]
    c.executemany(
        "INSERT OR IGNORE INTO categories (name, parent_id, sort_order) VALUES (?, ?, ?)",
        base_categories
    )
    conn.commit()

    # ========== app_meta ==========

    sweep_anchor = date.today().isoformat()
    c.execute(
        "INSERT OR REPLACE INTO app_meta (k, v) VALUES ('expiry_sweep_date', ?)",
        (sweep_anchor,),
    )

    conn.commit()
    conn.close()
    print("Database initialized successfully")
    print(f"Expiry sweep baseline: {sweep_anchor}")


if __name__ == "__main__":
    init_db()
    print(f"Database file: {DB_PATH}")
