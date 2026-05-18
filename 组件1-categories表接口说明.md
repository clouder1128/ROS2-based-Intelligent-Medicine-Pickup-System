# 组件1 → 组件2 对接说明：categories 表

**版本**：1.2  
**日期**：2026-05-08（修订：`drug_helpers` 与列表/统计一致的软删除语义）  
**负责人**：组件1  
**读者**：组件2（药品管理 API）、组件3（智能筛选系统）

---

## ⚡ 与接口清单的已知差异（组件2开发前必读）

| # | 差异点 | 接口清单约定 | 实际实现 | 状态 |
|---|---|---|---|---|
| 1 | `categories` 表 `description` 列 | POST 请求含 `description` 参数 | ~~表中无此列~~ → 已补列 | ✅ 已解决 |
| 2 | POST 响应格式 | `{success, category_id}` 扁平 | `{success, data: {id, name}, ...}` 嵌套 | ⚠️ 统一用嵌套格式，组件5按 `data.id` 取值 |
| 3 | GET 响应的数据 key | `{success, categories[]}` | `{success, data: [...], ...}` | ⚠️ 统一用 `data` key（与 /api/drugs 格式一致） |

---

## 一、本次交付内容

在以下两个文件中新增了 `categories`（药品分类）表，**组件2可直接开始写分类管理 API**：

| 文件 | 修改内容 |
|------|---------|
| `common/utils/database.py` | `init_database()` 中添加建表语句 + 2 个索引 + description 迁移 |
| `database/connection.py` | 与 database.py 完全同步（部分旧代码路径使用此入口） |
| `database/scripts/init_db.py` | `init_db()` 中添加建表语句 + 13 条种子分类数据 + description 迁移 |

同时修复了 `init_db.py` 缺少 `approvals` 表的历史遗留问题（三个文件现在完全同步）。

---

## 二、表结构

```sql
CREATE TABLE IF NOT EXISTS categories (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,  -- 分类名称（与 inventory.category 字段值一致）
    description TEXT    DEFAULT '',       -- 分类描述（接口清单约定字段）
    parent_id   INTEGER DEFAULT NULL,     -- 父级分类 ID，顶级分类为 NULL
    sort_order  INTEGER DEFAULT 0,        -- 排序权重，越小越靠前
    created_at  TEXT    DEFAULT '',       -- 创建时间，写入时填 UTC ISO8601 字符串
    FOREIGN KEY (parent_id) REFERENCES categories(id)
)
```

**已建索引：**

| 索引名 | 目标列 | 用途 |
|--------|--------|------|
| `idx_categories_name` | `name` | 按名称查找分类（JOIN / 精确查询） |
| `idx_categories_parent_id` | `parent_id` | 查询子分类列表 |

---

## 三、关键约定：inventory.category 与 categories.name 的关联方式

> **不使用外键 ID**，通过**字符串名称**关联，减少迁移风险。

```
inventory.category  =  categories.name
```

### 查询示例

**获取某分类下的所有药品：**

```sql
SELECT i.*
FROM inventory i
JOIN categories c ON c.name = i.category
WHERE c.id = ?
  AND i.is_deleted = 0
```

**获取分类列表（附带各分类的药品数量）：**

```sql
SELECT c.id, c.name, c.parent_id, c.sort_order,
       COUNT(i.drug_id) AS drug_count
FROM categories c
LEFT JOIN inventory i ON i.category = c.name AND i.is_deleted = 0
GROUP BY c.id
ORDER BY c.sort_order
```

---

## 四、种子分类数据（13 条）

运行 `python3 -m database.scripts.init_db` 后，`categories` 表自动包含以下顶级分类：

| id | name | sort_order | 说明 |
|----|------|-----------|------|
| 1 | 解热镇痛抗炎药 | 1 | 对应布洛芬等 |
| 2 | 抗生素抗感染药 | 2 | seed_drugs.py 主分类 |
| 3 | 消化系统药 | 3 | |
| 4 | 心血管药 | 4 | |
| 5 | 呼吸系统药 | 5 | |
| 6 | 神经系统药 | 6 | |
| 7 | 维生素矿物质 | 7 | 对应维生素C等 |
| 8 | 外用药皮肤科 | 8 | |
| 9 | 内分泌代谢药 | 9 | |
| 10 | 抗过敏药 | 10 | |
| 11 | 中成药感冒类 | 11 | |
| 12 | 其他专科药 | 12 | |
| 13 | 抗生素 | 13 | 兼容 base seed 中阿莫西林的旧分类值 |

> `INSERT OR IGNORE` 写入，重复运行 `init_db` 不会报错、不会重置 ID。

---

## 五、组件2 API 实现指引

### 文件规划

```
api/category_controller.py     ← 新建
database/models/category.py    ← 新建
```

注册 Blueprint 到 `main.py`（由组件2负责）：

```python
from api.category_controller import category_bp
app.register_blueprint(category_bp)
```

### GET /api/categories — 获取分类列表（含药品数量）

**请求参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `parent_id` | int \| null | — | 不传返回全部；传 `null` 返回顶级 |
| `with_count` | bool | false | 是否附带各分类药品数量 |

**响应示例（`with_count=true`）：**

```json
{
  "success": true,
  "data": [
    { "id": 1, "name": "解热镇痛抗炎药", "description": "", "parent_id": null, "sort_order": 1, "drug_count": 18 },
    { "id": 2, "name": "抗生素抗感染药", "description": "", "parent_id": null, "sort_order": 2, "drug_count": 23 }
  ],
  "pagination": null,
  "error": null
}
```

**最简实现骨架：**

```python
from flask import Blueprint, request
from common.utils.database import get_db_connection
from common.utils.response import success_response, error_response

category_bp = Blueprint("category", __name__, url_prefix="/api")

@category_bp.route("/categories", methods=["GET"])
def list_categories():
    with_count = request.args.get("with_count", "false").lower() == "true"
    parent_id  = request.args.get("parent_id")

    conn = get_db_connection()
    try:
        where = "1=1"
        params = []
        if parent_id is not None:
            if parent_id.lower() == "null":
                where += " AND c.parent_id IS NULL"
            else:
                where += " AND c.parent_id = ?"
                params.append(int(parent_id))

        if with_count:
            sql = f"""
                SELECT c.id, c.name, c.description, c.parent_id, c.sort_order,
                       COUNT(i.drug_id) AS drug_count
                FROM categories c
                LEFT JOIN inventory i ON i.category = c.name AND i.is_deleted = 0
                WHERE {where}
                GROUP BY c.id
                ORDER BY c.sort_order
            """
        else:
            sql = f"""
                SELECT id, name, description, parent_id, sort_order
                FROM categories c
                WHERE {where}
                ORDER BY sort_order
            """

        rows = conn.execute(sql, params).fetchall()
        return success_response([dict(r) for r in rows])
    finally:
        conn.close()
```

### POST /api/categories — 创建分类

**请求体（含接口清单约定的全部字段）：**

```json
{ "name": "眼科用药", "description": "用于眼部疾病的药品", "parent_id": null, "sort_order": 14 }
```

> `description` 字段已在 `categories` 表中，可直接存储。

**响应（与接口清单对齐，`data` 中含 `id`）：**

```json
{
  "success": true,
  "data": { "id": 14, "name": "眼科用药", "description": "用于眼部疾病的药品" },
  "pagination": null,
  "error": null
}
```

> 接口清单原文写的响应是 `{success, category_id}`（扁平格式），与 `response.py` 的嵌套 `data` 格式不同。  
> **建议统一使用 `data` 嵌套格式**（与 GET /api/categories、GET /api/drugs 等保持一致），组件5前端按 `data.id` 取值即可。

**约束检查：**
- `name` 必填且不能重复（数据库层有 `UNIQUE` 约束，捕获 `sqlite3.IntegrityError` 返回 `CATEGORY_EXISTS` 错误）
- `parent_id` 若传值，必须是已存在的分类 ID

---

## 六、组件3 注意事项

筛选 API `POST /api/screening/query` 中，`category` 参数统一**传分类名称字符串**（不传 ID），组件2 的搜索接口 `GET /api/drugs/search?category=解热镇痛抗炎药` 同理。

```json
// 请求示例
{
  "symptoms": "头痛发热",
  "category": "解热镇痛抗炎药"
}
```

组件3 无需维护 ID 映射，直接将字符串透传给组件2即可。

---

## 七、初始化命令

新环境从零搭建，**只需运行一条命令**：

```bash
cd agent_with_backend
python3 -m database.scripts.init_db
```

运行后数据库包含：
- 全部建表结构（包含 `categories`）
- 3 条基础药品（`inventory`）
- 13 条种子分类（`categories`）
- 症状同义词、适应症等基础数据

之后可选运行 `seed_drugs.py` 填充 116 种完整药品数据：

```bash
python3 -m database.scripts.seed_drugs
```

---

## 八、与 inventory 的关联约定（重要）

### 不使用外键，用字符串匹配

`inventory.category` 保持 TEXT 字符串（如 `"解热镇痛抗炎药"`），**不改为整数 ID**，不加外键约束。

**原因**：
- `inventory` 已有 116 条数据，加外键需要数据迁移，代价大
- SQLite 外键需每次连接手动 `PRAGMA foreign_keys = ON`，容易漏

### 唯一约定：两张表的值保持一致

| 表 | 字段 | 值示例 |
|---|---|---|
| `categories` | `name` | `"解热镇痛抗炎药"` |
| `inventory` | `category` | `"解热镇痛抗炎药"` |

**只要字符串一致，就能关联。** 13 条种子分类的 `name` 已与 116 条药品的 `category` 完全对齐。

### 组件2 常用 SQL

```sql
-- 查某分类下的药品
SELECT * FROM inventory
WHERE category = '解热镇痛抗炎药' AND is_deleted = 0;

-- 分类列表（附各分类药品数量）
SELECT c.name, COUNT(i.drug_id) AS drug_count
FROM categories c
LEFT JOIN inventory i ON i.category = c.name AND i.is_deleted = 0
GROUP BY c.name
ORDER BY c.sort_order;

-- 分类筛选（GET /api/drugs?category=xxx 的核心查询）
SELECT * FROM inventory
WHERE category = ? AND is_deleted = 0
ORDER BY drug_id
LIMIT ? OFFSET ?;
```

### 与下单路径一致的辅助函数（组件1）

`common/utils/drug_helpers.py` 中的 **`query_drug`**、**`find_drug_id_by_name`** 已按 `COALESCE(is_deleted, 0) = 0` 过滤，与上表 SQL 及 `GET /api/drugs` 列表口径一致：已软删除药品不会被子路径 `/api/order`、`/api/pickup`、`/api/dispense` 通过 ID 或名称匹配到。

**`GET /api/drugs/stats`** 的各项计数与总库存 `SUM(quantity)` 亦仅统计未删除记录。

---

## 九、inventory_transactions 表（已交付）

> 第3周写库存 API 时直接使用，表已建好，无需等待。

```sql
CREATE TABLE IF NOT EXISTS inventory_transactions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    drug_id         INTEGER NOT NULL,
    change          INTEGER NOT NULL,        -- 正=入库，负=出库/调减
    change_type     TEXT    NOT NULL,        -- 枚举: 'in' / 'out' / 'adjust' / 'expire'
    before_quantity INTEGER DEFAULT 0,       -- 变更前库存
    after_quantity  INTEGER DEFAULT 0,       -- 变更后库存
    reason          TEXT    DEFAULT '',      -- 变更原因
    operator        TEXT    DEFAULT '',      -- 操作用户名
    created_at      TEXT    DEFAULT ''       -- UTC ISO8601
);
```

**字段说明**：接口清单早期草案里叫 `transaction_id` / `quantity_change` / `transaction_type`，实际字段名为 `id` / `change` / `change_type`，以此为准。

组件2可在 `database/models/inventory.py` 中定义对应 dataclass，直接使用。
