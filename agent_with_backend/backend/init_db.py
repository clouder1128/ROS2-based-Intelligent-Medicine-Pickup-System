"""
数据库初始化脚本
创建 inventory（药品表）和 order_log（任务/订单表），并插入示例数据
"""

import os
import sqlite3
import sys
from datetime import date
from config.settings import Config

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

    # 初始化筛选系统表（组件3）
    try:
        # 将 project root 加入 sys.path 以导入 common 模块
        _script_dir = os.path.dirname(os.path.abspath(__file__))
        _project_root = os.path.abspath(os.path.join(_script_dir, ".."))
        if _project_root not in os.sys.path:
            os.sys.path.insert(0, _project_root)
        from common.utils.database import init_database as init_screening_db
        init_screening_db()
    except Exception as e:
        print(f"筛选系统表初始化略过: {e}")

    # 写入筛选演示种子数据
    try:
        _seed_script = os.path.join(_project_root, "scripts", "seed_screening_data.py")
        if os.path.exists(_seed_script):
            import subprocess
            subprocess.run([sys.executable, _seed_script], cwd=_project_root, check=True)
    except Exception as e:
        print(f"种子数据写入略过: {e}")


if __name__ == "__main__":
    init_db()
    print(f"数据库文件: {DB_PATH}")
