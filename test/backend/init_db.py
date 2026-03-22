"""
数据库初始化脚本
创建 inventory（药品表）和 order_log（任务/订单表），并插入示例数据

expiry_date: 倒计时（剩余天数），为 0 或负数表示已过期
"""
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), 'pharmacy.db')


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 药品表（expiry_date = 剩余天数，0 或负数表示已过期）
    c.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            drug_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            expiry_date INTEGER NOT NULL,
            shelf_x INTEGER NOT NULL,
            shelf_y INTEGER NOT NULL,
            shelve_id INTEGER NOT NULL
        )
    ''')

    # 任务/订单表
    c.execute('''
        CREATE TABLE IF NOT EXISTS order_log (
            task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            status TEXT NOT NULL,
            target_drug_id INTEGER,
            quantity INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (target_drug_id) REFERENCES inventory(drug_id)
        )
    ''')

    conn.commit()

    # 清空并插入示例数据（expiry_date = 剩余天数）
    c.execute('DELETE FROM order_log')
    c.execute('DELETE FROM inventory')

    c.execute('''
        INSERT INTO inventory (drug_id, name, quantity, expiry_date, shelf_x, shelf_y, shelve_id)
        VALUES (1, '阿莫西林', 50, 365, 1, 1, 1)
    ''')
    c.execute('''
        INSERT INTO inventory (drug_id, name, quantity, expiry_date, shelf_x, shelf_y, shelve_id)
        VALUES (2, '布洛芬', 30, 180, 1, 2, 1)
    ''')
    c.execute('''
        INSERT INTO inventory (drug_id, name, quantity, expiry_date, shelf_x, shelf_y, shelve_id)
        VALUES (3, '维生素C', 100, 0, 2, 1, 2)
    ''')  # expiry_date=0 已过期，用于测试

    conn.commit()
    conn.close()
    print('数据库初始化成功')


if __name__ == '__main__':
    init_db()
    print(f'数据库文件: {DB_PATH}')
