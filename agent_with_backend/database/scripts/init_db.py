"""
数据库初始化脚本
创建 inventory（药品表）和 order_log（任务/订单表），并插入示例数据
"""

import os
import sqlite3
from datetime import date
from common.config import Config

DB_PATH = Config.DATABASE_PATH


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

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

    c.execute("DELETE FROM order_log")
    c.execute("DELETE FROM inventory")

    c.execute("""
        INSERT INTO inventory (drug_id, name, quantity, expiry_date, shelf_x, shelf_y, shelve_id)
        VALUES (1, '阿莫西林', 50, 365, 1, 1, 1)
    """)
    c.execute("""
        INSERT INTO inventory (drug_id, name, quantity, expiry_date, shelf_x, shelf_y, shelve_id)
        VALUES (2, '布洛芬', 30, 180, 1, 2, 1)
    """)
    c.execute("""
        INSERT INTO inventory (drug_id, name, quantity, expiry_date, shelf_x, shelf_y, shelve_id)
        VALUES (3, '维生素C', 100, 0, 2, 1, 2)
    """)

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
