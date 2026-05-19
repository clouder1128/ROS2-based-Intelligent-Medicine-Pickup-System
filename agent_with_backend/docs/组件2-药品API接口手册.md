# 组件2 — 药品 API 接口手册

> **用途**：供组件3 编写自动化/手测用例、组件5 联调。  
> **实现位置**：`agent_with_backend/api/drug_controller.py`、`category_controller.py`  
> **版本**：与 `demo0425` 分支代码对齐（无 OpenAPI/Swagger，以本文档为准）

---

## 1. 基本信息

| 项 | 说明 |
|---|---|
| 服务启动 | 在 `agent_with_backend` 目录执行 `python3 main.py` |
| Base URL | `http://127.0.0.1:8001/api`（可通过环境变量 `PORT` 修改端口） |
| Content-Type | 请求体为 JSON 时使用 `Content-Type: application/json` |
| 字符编码 | UTF-8 |
| 数据库 | SQLite `pharmacy.db`（表 `inventory`、`drug_indications`、`categories`、`inventory_transactions` 等由组件1 DDL 提供） |

---

## 2. 认证与权限

除健康检查等公开路由外，**药品与分类接口均需 JWT**。

### 2.1 获取 Token

```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin1",
  "password": "123456"
}
```

**成功响应（200）示例：**

```json
{
  "success": true,
  "token": "<access_token>",
  "token_type": "Bearer",
  "access_token": "<access_token>",
  "refresh_token": "<refresh_token>",
  "expires_in": 3600,
  "user": {
    "id": 1,
    "username": "admin1",
    "role": "admin",
    "permissions": ["read:drug", "create:drug", "..."]
  }
}
```

演示账号（需先执行 `python3 -m database.scripts.init_db` 与 `python3 -m database.scripts.seed_users`）：

| 用户名 | 密码 | 角色 | 药品相关权限摘要 |
|---|---|---|---|
| `admin1` | `123456` | admin | 全部（含删除、批量导入） |
| `doctor1` | `123456` | doctor | 读药品、读库存、读订单 |
| `patient1` | `123456` | patient | 仅读药品 |

### 2.2 请求头

后续请求携带：

```http
Authorization: Bearer <access_token>
```

### 2.3 权限码与角色矩阵

| 权限码 | 说明 | admin | pharmacist | doctor | patient |
|---|---|:---:|:---:|:---:|:---:|
| `read:drug` | 读药品 | ✓ | ✓ | ✓ | ✓ |
| `create:drug` | 创建药品 / 新建分类 | ✓ | ✓ | | |
| `update:drug` | 更新药品 | ✓ | ✓ | | |
| `delete:drug` | 软删除药品 | ✓ | | | |
| `read:inventory` | 读库存视图 / 统计 / 预警列表 | ✓ | ✓ | ✓ | |
| `update:inventory` | 手动调整库存 | ✓ | ✓ | | |
| `batch:drug` | 批量导入 | ✓ | | | |

> 注：种子脚本未创建 `pharmacist` 用户；需测药师权限时可自行注册或改库中角色。

---

## 3. 响应格式

### 3.1 标准成功（单条 / 无分页）

```json
{
  "success": true,
  "data": { },
  "pagination": null,
  "error": null,
  "message": "可选说明"
}
```

### 3.2 标准成功（分页，`paginated_response`）

用于 `GET /categories?page=1&limit=20` 等：

```json
{
  "success": true,
  "data": [ ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "pages": 5,
    "has_next": true,
    "has_prev": false
  },
  "error": null
}
```

### 3.3 列表型接口（药品列表 / 搜索 / 库存视图等）

除 `data` 外还包含 `count`、`filters`；传 `page` 或 `limit` 时带 `pagination`：

```json
{
  "success": true,
  "data": [ ],
  "count": 10,
  "filters": { },
  "pagination": { "page": 1, "limit": 20, "total": 100, "pages": 5 },
  "error": null
}
```

### 3.4 业务错误（`common/utils/response.py`）

```json
{
  "success": false,
  "data": null,
  "pagination": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "参数错误: {\"name\": \"name 为必填项\"}"
  }
}
```

常见 HTTP 状态：`400` 参数错误、`401` 未登录、`403` 无权限、`404` 不存在、`409` 冲突、`500` 服务器错误。

### 3.5 认证中间件错误（格式略有不同）

```json
{
  "success": false,
  "error_code": "AUTH_001",
  "message": "未提供访问令牌"
}
```

---

## 4. 数据约定（测试必读）

| 字段 | 含义 |
|---|---|
| `quantity` | **当前库存数量**（主字段）；创建/更新药品时使用 |
| `stock` | 历史列，创建时写 0；**PUT 不可更新**；业务以 `quantity` 为准 |
| `expiry_date` | **剩余有效天数**（整数），非日历日期。`<= 0` 视为已过期 |
| `shelf_x`, `shelf_y`, `shelve_id` | 货架坐标与货架编号（机器人拣货用） |
| `indications` | 字符串数组，存于 `drug_indications` 表 |
| `category` | 字符串，与 `categories.name` 匹配（非外键 ID） |
| `is_deleted` | 软删除标记；已删药品在列表/详情中不可见 |

**创建药品必填字段**：`name`, `quantity`, `expiry_date`, `shelf_x`, `shelf_y`, `shelve_id`

**库存流水**（`inventory_transactions`）在以下场景写入：

- `POST /api/drugs/{id}/adjust` 手动调整
- 订单出库 / 发药 / 取药（`order_controller`，`transaction_type=out`，`quantity_change` 为负）

---

## 5. 接口总览

| 方法 | 路径 | 权限 | 说明 |
|---|---|---|---|
| GET | `/drugs` | `read:drug` | 药品列表（可筛选、排序、分页） |
| POST | `/drugs` | `create:drug` | 创建药品 |
| GET | `/drugs/{id}` | `read:drug` | 药品详情 |
| PUT | `/drugs/{id}` | `update:drug` | 更新药品 |
| DELETE | `/drugs/{id}` | `delete:drug` | 软删除 |
| GET | `/drugs/search` | `read:drug` | 关键词综合搜索 |
| GET | `/drugs/stats` | `read:inventory` | 库存统计 |
| GET | `/drugs/low-stock` | `read:inventory` | 低库存列表 |
| GET | `/drugs/expiring-soon` | `read:inventory` | 临期列表 |
| POST | `/drugs/{id}/adjust` | `update:inventory` | 调整库存并记流水 |
| POST | `/drugs/batch-import` | `batch:drug` | 批量创建 |
| GET | `/drugs/export` | `read:drug` | 导出 JSON / CSV |
| GET | `/inventory` | `read:inventory` | 拣货/库区视图（收窄字段） |
| GET | `/categories` | `read:drug` | 分类列表 |
| POST | `/categories` | `create:drug` | 新建分类 |

---

## 6. 接口详情

### 6.1 GET `/drugs` — 药品列表

**权限**：`read:drug`

**查询参数**

| 参数 | 类型 | 说明 |
|---|---|---|
| `name` | string | 名称子串过滤（≤100 字符） |
| `symptom` | string | 按适应症 / 同义词表匹配（≤100 字符） |
| `category` | string | 精确匹配分类名（≤200 字符） |
| `sort_by` | string | `drug_id`（默认）、`name`、`quantity`、`expiry_date`、`retail_price`、`category`、`shelve_id`、`created_at`、`updated_at` |
| `order` | string | `asc`（默认）或 `desc` |
| `page` | int | 页码，从 1 开始；与 `limit` 任传其一即启用分页 |
| `limit` | int | 每页条数，最大 100，默认 20 |

**说明**：不传 `page`/`limit` 时返回**全量**列表（兼容旧客户端）。

**curl 示例**

```bash
TOKEN=$(curl -sS -X POST http://127.0.0.1:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin1","password":"123456"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -sS "http://127.0.0.1:8001/api/drugs?page=1&limit=5&sort_by=name&order=asc" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

### 6.2 POST `/drugs` — 创建药品

**权限**：`create:drug`  
**状态码**：201

**请求体（JSON）**

| 字段 | 必填 | 类型 | 说明 |
|---|---|---|---|
| `name` | ✓ | string | 药品名称 |
| `quantity` | ✓ | int ≥0 | 初始库存 |
| `expiry_date` | ✓ | int | 剩余有效天数 |
| `shelf_x`, `shelf_y`, `shelve_id` | ✓ | int | 货位 |
| `category` | | string | 分类名，≤200 |
| `is_prescription` | | bool | 是否处方药 |
| `retail_price`, `cost_price`, `purchase_price` | | number | 价格 |
| `min_stock_alert`, `min_stock_level`, `max_stock_level` | | int ≥0 | 库存预警 |
| `indications` | | string[] | 适应症列表 |
| `generic_name`, `description`, `manufacturer`, … | | string | 其他可选文本字段（见 `validate_drug`） |

**请求示例**

```json
{
  "name": "维生素B",
  "quantity": 80,
  "expiry_date": 400,
  "shelf_x": 3,
  "shelf_y": 2,
  "shelve_id": 1,
  "category": "维生素矿物质",
  "is_prescription": false,
  "retail_price": 12.5,
  "indications": ["口角炎", "神经炎", "疲劳"]
}
```

**成功响应**

```json
{
  "success": true,
  "data": { "drug_id": 42 },
  "pagination": null,
  "error": null,
  "message": "Drug created"
}
```

---

### 6.3 GET `/drugs/{id}` — 药品详情

**权限**：`read:drug`

返回完整 `inventory` 行 + `indications` 数组。不存在或已软删 → 404。

---

### 6.4 PUT `/drugs/{id}` — 更新药品

**权限**：`update:drug`

**请求体**：任意可更新字段的子集（至少一项）。不可更新 `drug_id`、`stock`。

**示例**

```json
{
  "retail_price": 15.0,
  "indications": ["口角炎", "神经炎", "疲劳", "食欲不振"]
}
```

**成功响应**：`data` 为 `null`，`message`: `"Drug updated"`

---

### 6.5 DELETE `/drugs/{id}` — 软删除

**权限**：`delete:drug`

将 `is_deleted` 置 1，不物理删除。再次 GET → 404。

---

### 6.6 GET `/drugs/search` — 综合搜索

**权限**：`read:drug`

| 参数 | 说明 |
|---|---|
| `keyword` 或 `q` | 关键词；**为空时等价于 GET `/drugs`** |
| `category` | 可选，精确分类 |
| `sort_by`, `order`, `page`, `limit` | 同列表接口 |

匹配范围：`name`、`generic_name`、`description`、`drug_indications.indication`（LIKE 模糊）。

```bash
curl -sS "http://127.0.0.1:8001/api/drugs/search?keyword=维生素&page=1&limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

---

### 6.7 GET `/inventory` — 拣货/库区视图

**权限**：`read:inventory`

与 `/drugs` 相同的筛选、排序、分页，但：

- 默认只返回 `quantity > 0` 且未软删的记录（按 symptom 过滤时逻辑同实现）
- 每条记录为**收窄字段** + 运营标记

**额外查询参数**

| 参数 | 默认 | 说明 |
|---|---|---|
| `threshold` | 10 | 无 `min_stock_alert` 时的低库存兜底阈值 |
| `expiring_window` | 30 | 临期判定窗口（天） |

**单条 `data[]` 附加字段**

| 字段 | 类型 | 说明 |
|---|---|---|
| `location_label` | string | 如 `Shelf 1, Position (3, 2)` |
| `needs_restock` | bool | 是否需补货 |
| `is_expired_stock` | bool | `expiry_date <= 0` |
| `expiring_soon` | bool | `0 < expiry_date <= expiring_window` |

---

### 6.8 GET `/drugs/stats` — 库存统计

**权限**：`read:inventory`

**响应 `data` 字段**

| 字段 | 说明 |
|---|---|
| `total_drugs` | 未软删药品种数 |
| `total_quantity` | 库存数量合计 |
| `expired_count` | `expiry_date <= 0` |
| `low_stock_count` | `quantity < 10`（固定阈值） |
| `expiring_soon_count` | `0 < expiry_date <= 30` |

---

### 6.9 GET `/drugs/low-stock` — 低库存列表

**权限**：`read:inventory`

| 参数 | 说明 |
|---|---|
| `threshold` | 默认 10；仅对**未设置** `min_stock_alert` 的药品生效 |
| `page`, `limit` | 可选分页 |

规则：若药品配置了 `min_stock_alert`，则 `quantity <= min_stock_alert` 即入选；否则 `quantity < threshold`。

---

### 6.10 GET `/drugs/expiring-soon` — 临期列表

**权限**：`read:inventory`

| 参数 | 默认 | 说明 |
|---|---|---|
| `days` | 30 | 临期窗口：`0 < expiry_date <= days` |
| `page`, `limit` | | 可选分页 |

已过期（`expiry_date <= 0`）不在此列表。

---

### 6.11 POST `/drugs/{id}/adjust` — 调整库存

**权限**：`update:inventory`

**写法一（推荐，写流水规范字段）**

```json
{
  "quantity_change": 10,
  "transaction_type": "in",
  "reason": "采购入库",
  "operator": "admin1"
}
```

| 字段 | 必填 | 说明 |
|---|---|---|
| `quantity_change` | ✓ | 非零整数；正数增加、负数减少 |
| `transaction_type` | ✓ | `in` / `out` / `adjust` / `expire` |
| `reason` | | ≤500 字符 |
| `operator` | | ≤100 字符 |

**写法二（兼容）**：`quantity` 设为调整后的绝对库存  
**写法三（兼容）**：`delta` 相对增减  

`quantity_change` 等价结果为 0 时：不更新库存、不写流水。

**成功响应 `data`**

```json
{
  "drug_id": 42,
  "quantity": 90,
  "quantity_change": 10,
  "transaction_id": 7
}
```

**错误**：库存不足 → 400 `INVALID_ADJUST`；药品不存在 → 404 `DRUG_NOT_FOUND`

---

### 6.12 POST `/drugs/batch-import` — 批量导入

**权限**：`batch:drug`（通常仅 admin）  
**状态码**：201

**请求体**：非空 JSON 数组，每项字段同 POST `/drugs`。

```json
[
  {
    "name": "测试药A",
    "quantity": 50,
    "expiry_date": 180,
    "shelf_x": 1,
    "shelf_y": 1,
    "shelve_id": 1
  },
  {
    "name": "测试药B",
    "quantity": 30,
    "expiry_date": 90,
    "shelf_x": 2,
    "shelf_y": 1,
    "shelve_id": 1
  }
]
```

**响应**

```json
{
  "success": true,
  "data": { "drug_ids": [43, 44], "count": 2 },
  "message": "Batch import completed"
}
```

任一项校验失败则整批回滚，返回 400 并指明 `Item {index}`。

---

### 6.13 GET `/drugs/export` — 导出

**权限**：`read:drug`

| 参数 / 头 | 说明 |
|---|---|
| `format=json` | 默认；返回 `{ "drugs": [...], "count": N }` 包裹在标准 `data` 中 |
| `format=csv` 或 `Accept: text/csv` | 返回 CSV 文件（UTF-8 BOM），`Content-Disposition: attachment` |

```bash
curl -sS "http://127.0.0.1:8001/api/drugs/export?format=csv" \
  -H "Authorization: Bearer $TOKEN" -o drugs_export.csv
```

---

### 6.14 GET `/categories` — 分类列表

**权限**：`read:drug`

| 参数 | 说明 |
|---|---|
| `tree=1` 或 `tree=true` | 返回树形结构（`children` 嵌套） |
| `page`, `limit` | 启用分页（使用 `paginated_response`） |

每条分类含 `drug_count`（`inventory.category = name` 且未软删的计数）。

**单条字段**：`id`, `name`, `description`, `parent_id`, `sort_order`, `created_at`, `drug_count`

---

### 6.15 POST `/categories` — 新建分类

**权限**：`create:drug`  
**状态码**：201

```json
{
  "name": "感冒用药",
  "description": "OTC 感冒药",
  "parent_id": null,
  "sort_order": 0
}
```

| 字段 | 必填 | 说明 |
|---|---|---|
| `name` | ✓ | ≤50 字符，不可重复 |
| `description` | | ≤500 字符 |
| `parent_id` | | 父分类 ID；不存在 → 404 |
| `sort_order` | | 默认 0 |

名称重复 → 409 `DUPLICATE_NAME`

---

## 7. 组件3 测试建议

### 7.1 环境准备

```bash
cd agent_with_backend
python3 -m database.scripts.init_db
python3 -m database.scripts.seed_users
python3 main.py
```

### 7.2 推荐用例矩阵

| # | 场景 | 方法 | 预期 |
|---|---|---|---|
| 1 | 未带 Token 访问 `/drugs` | GET | 401 |
| 2 | patient 访问 `/inventory` | GET | 403 |
| 3 | admin 创建药品 | POST `/drugs` | 201，`data.drug_id` |
| 4 | 创建缺少必填项 | POST `/drugs` | 400 `VALIDATION_ERROR` |
| 5 | 按 symptom 列表过滤 | GET `/drugs?symptom=头痛` | 200，含匹配适应症 |
| 6 | 关键词搜索 | GET `/drugs/search?keyword=维` | 200 |
| 7 | 分页 | GET `/drugs?page=1&limit=2` | `pagination.total` 正确 |
| 8 | 详情 / 更新 / 软删 | GET → PUT → DELETE → GET | 最后 404 |
| 9 | 入库调整 | POST `/drugs/{id}/adjust` `in` | `quantity` 增加，`transaction_id` 非空 |
| 10 | 出库至 0 以下 | POST adjust `out` 超额 | 400 |
| 11 | 低库存 / 临期 | GET `/drugs/low-stock`、`/expiring-soon` | 与 seed 数据一致 |
| 12 | 统计 | GET `/drugs/stats` | 计数与 DB 一致 |
| 13 | 批量导入 | POST `/drugs/batch-import` | 201，多条 `drug_ids` |
| 14 | 导出 JSON / CSV | GET `/drugs/export` | 200，条数一致 |
| 15 | 分类 CRUD | GET/POST `/categories` | 树形 / 重复名 409 |

### 7.3 流水校验 SQL

调整或订单出库后：

```sql
SELECT drug_id, quantity_change, transaction_type, before_quantity, after_quantity, reason, operator
FROM inventory_transactions
WHERE drug_id = ? ORDER BY id DESC LIMIT 5;
```

### 7.4 现有脚本

`scripts/smoke_drug_api.sh` 覆盖 CRUD 主路径，**未含 JWT**；手测时请先按 §2.1 取 Token 并加入 `-H "Authorization: Bearer ..."`，或参考上文 curl 示例。

---

## 8. 已知限制 / 未实现项

| 项 | 说明 |
|---|---|
| OpenAPI / Swagger | 未集成；以本文档为准 |
| 缓存层 | 组件1 未提供，已跳过 |
| 文件上传（图片等） | 组件1 未提供，已跳过；`image_url` 仍为字符串 URL 字段 |
| `pharmacist` 演示账号 | 种子脚本未创建，需自行配置 |
| `GET /drugs/stats` 低库存阈值 | 固定 `quantity < 10`，与 `/drugs/low-stock?threshold=` 参数化行为略有差异 |

---

## 9. 变更记录

| 日期 | 说明 |
|---|---|
| 2026-05-19 | 初版：覆盖药品 CRUD、搜索、库存视图、预警、调整、批量、导出、分类；对齐 RBAC 与统一响应格式 |
