import sqlite3

conn = sqlite3.connect('test.db')

c=conn.cursor()
#药房表,每一行代表一种药品
c.execute('''CREATE TABLE IF NOT EXISTS pharmacy  
            (id INT PRIMARY KEY NOT NULL,
            shelf_x INT NOT NULL,
            shelf_y INT NOT NULL
            )''')
#药品库存表，每一行代表一盒药
c.execute('''CREATE TABLE IF NOT EXISTS drug_stock 
            (stock_id INTEGER PRIMARY KEY AUTOINCREMENT,
            drug_id INT NOT NULL,
            rest_days INT,
            FOREIGN KEY (drug_id) REFERENCES pharmacy(id)
            )''')

conn.commit()

c.execute("DELETE FROM drug_stock")
c.execute("DELETE FROM pharmacy")

c.execute("INSERT INTO pharmacy (id, shelf_x, shelf_y) \
      VALUES (1, 1, 1)")
c.execute("INSERT INTO pharmacy (id, shelf_x, shelf_y) \
      VALUES (2, 1, 2)")
c.execute("INSERT INTO drug_stock (drug_id, rest_days) VALUES (1, 30)")
c.execute("INSERT INTO drug_stock (drug_id, rest_days) VALUES (2, 20)")

conn.commit()
print ("数据库初始化成功")
conn.close()
