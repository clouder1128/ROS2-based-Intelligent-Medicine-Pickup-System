#!/usr/bin/env python3
"""
数据库初始化脚本
创建 inventory（药品表）和 order_log（任务/订单表），并插入示例数据
"""

import os
import sys
import sqlite3
from datetime import date

# Add project root to Python path to ensure config.settings can be imported
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.config.settings import Config

DB_PATH = Config.DATABASE_PATH


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 药品表（expiry_date = 剩余天数，0 表示已过期）
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

    # 任务/订单表
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

    # 应用元数据（记录过期清扫上次执行日期，避免重复扣减）
    c.execute("""
        CREATE TABLE IF NOT EXISTS app_meta (
            k TEXT PRIMARY KEY,
            v TEXT NOT NULL
        )
    """)

    conn.commit()

    # 清空并插入示例数据（expiry_date = 剩余天数）
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
    """)  # expiry_date=0 已过期，用于测试

    # 过期清扫从本次初始化当日为「基准日」；次日及以后由后端按日期差扣减剩余天数
    sweep_anchor = date.today().isoformat()
    c.execute(
        "INSERT OR REPLACE INTO app_meta (k, v) VALUES ('expiry_sweep_date', ?)",
        (sweep_anchor,),
    )

    conn.commit()
    conn.close()
    print("数据库初始化成功")
    print(f"过期清扫基准日（从 init_db 起算）: {sweep_anchor}")


if __name__ == "__main__":
    init_db()
    print(f"数据库文件: {DB_PATH}")