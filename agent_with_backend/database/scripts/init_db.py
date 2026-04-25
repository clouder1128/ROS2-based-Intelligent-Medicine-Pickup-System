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
    c = conn.cursor()

    # ========== 建表 ==========

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
