# 组件2：药品 API

> 本文分两大部分：**A 部分**是组件边界与开发计划（与组长 `组件2.pdf` 对齐，内容稳定）；**B 部分**是每周进展日志（随开发推进持续更新）。

---

# A. 组件边界与开发计划

## 一、系统整体执行流程

```
用户（患者/医生/药剂师）
        │
        ▼
┌───────────────────────────────┐
│  组件5：前端界面（React）         │  浏览器侧
│  · 登录                         │
│  · 药品列表 / 详情              │
│  · 智能筛选                     │
│  · 用户与角色管理               │
└──────────────┬────────────────┘
               │  HTTP 请求（携带 JWT Token）
               ▼
┌───────────────────────────────┐
│  组件4：权限认证系统              │  网关/中间件
│  · JWT 验证                     │
│  · RBAC 权限                    │
│  · 审计日志                     │
└──────────────┬────────────────┘
               │  认证通过后转发
               ▼
┌──────────────────────────────────────────────────┐
│  后端 API 层（Flask）                             │
│  ┌────────────────┐   ┌──────────────────┐     │
│  │ 组件2：药品 API  │   │ 组件3：智能筛选     │     │
│  │ /api/drugs       │◄──│ /api/screening   │     │
│  │ /api/inventory   │   │ /api/symptoms    │     │
│  │ /api/categories  │   └──────────────────┘     │
│  │ /api/drugs/search                           │  │
│  │ /api/drugs/batch-import                      │  │
│  └────────┬───────┘                            │  │
│           │                                    │  │
└───────────┼────────────────────────────────────┘
            ▼
┌───────────────────────────────┐
│  组件1：数据库与基础架构          │
│  · SQLite、连接池               │
│  · 缓存层                       │
│  · 文件存储                     │
└──────────────┬────────────────┘
               │
               ▼
┌───────────────────────────────┐
│  集成层：ROS2 / Unity            │
│  · 向机器人发布取药任务          │
│  · Unity 仿真环境               │
└───────────────────────────────┘
```

## 二、核心业务场景

**场景1：用户登录 → 查询药品**

1. 用户在前端（组件5）输入用户名密码
2. 前端调用 `POST /api/auth/login`（组件4）获取 JWT Token
3. 前端携带 Token 调用 `GET /api/drugs`（组件2）获取药品列表
4. 组件2 通过组件1 的数据库连接查询 `inventory` 表
5. 返回药品数据给前端展示

**场景2：智能症状筛选 → 取药**

1. 用户在前端（组件5）输入症状描述
2. 前端调用 `POST /api/screening/query`（组件3）
3. 组件3 对症状进行标准化处理（LLM + 同义词表）
4. 组件3 调用 `GET /api/drugs`（组件2）和 `GET /api/drugs/search`（组件2）获取候选药品
5. 组件3 根据匹配度返回推荐结果
6. 用户选择药品后，前端调用 `POST /api/order`（组件2）下单
7. 组件2 扣减库存，通过 ROS2 发布取药任务给机器人

**场景3：库存管理**

1. 药剂师登录后，前端调用 `GET /api/inventory`（组件2）查看库存状态
2. 发现低库存药品，进行 `POST /api/drugs/{id}/adjust`（组件2）调整库存
3. 系统自动进行过期药品清扫（`main.py` 中的 `_expiry_sweep_loop`）

## 三、组件2需要管理的文件

根据框架定义和当前代码库，以下为需要负责的**已有文件**与**需新建文件**（仓库中路径以 `agent_with_backend/` 为前缀）。

### 已有文件（扩展/完善 — 当前状态）


| 文件路径 | 当前状态 |
| -------------------------------- | --------------------------------------------- |
| `api/drug_controller.py` | ✅ 药品 CRUD、搜索、批量导入/导出、库存视图、adjust、low-stock、expiring-soon、stats（统一在 `drug_bp`） |
| `api/category_controller.py` | ✅ `GET/POST /api/categories`（树形、分页、`drug_count`） |
| `api/order_controller.py` | ✅ 订单/取药/配药；出库时同步写 `inventory_transactions` |
| `database/models/drug.py` | ✅ 35 字段 Drug dataclass |
| `database/models/category.py` | ✅ Category dataclass |
| `database/pharmacy_client.py` | ✅ 封装 search/categories/adjust/batch/export/inventory/low-stock/expiring-soon 等 |
| `common/utils/http_client.py` | ✅ 与 pharmacy_client 对齐的 HTTP 方法 |
| `common/utils/validation.py` | ✅ `validate_drug`、`validate_inventory_transaction`、`validate_category` |
| `common/utils/drug_service.py` | ✅ 共享查询层（列表/详情/indications） |
| `web/js/api.js` | ✅ 前端 API 封装（含 search/export/inventory 等） |
| `web/admin_drugs.html` | ✅ 管理端：搜索、分类筛选、批量导入、导出、库存调整 |
| `database/scripts/seed_drugs.py` | ✅ 100+ 种子药品 |
| `tests/test_drug_api.py` | ✅ 13 个用例（CRUD、搜索、批量、导出、分类） |
| `tests/test_inventory_api.py` | ✅ 8 个用例（库区视图、adjust+流水、预警、统计） |
| `docs/组件2-药品API接口手册.md` | ✅ Markdown 接口手册（供组件3 测试 / 组件5 联调） |


### 原计划新建、实际合并或未单独建文件的项


| 原计划路径 | 实际做法 |
| ------------------------------ | ----------- |
| `api/inventory_controller.py` | 库存相关路由合并在 `api/drug_controller.py`（`drug_bp`） |
| `api/batch_controller.py` | batch-import / export 合并在 `api/drug_controller.py` |
| `database/models/inventory.py` | 流水直接写 `inventory_transactions` 表，未单独 dataclass |


### 需要修改的共享文件（协调情况）


| 文件路径 | 修改内容 | 状态 |
| ----------------------------- | ---------------------------------------------------------- | ---- |
| `main.py` | 注册 `category_bp` 等 Blueprint | ✅ 已完成 |
| `common/utils/database.py` | `categories`、`inventory_transactions` 等表 | ✅ 组件1/组件2 已对齐 |
| `database/scripts/init_db.py` | 新表初始化 SQL | ✅ 已完成 |


## 四、组件2需要调用的外部 API

### 来自组件1（数据库与基础架构）


| 接口                         | 用途                                       | 当前状态           |
| -------------------------- | ---------------------------------------- | -------------- |
| `get_db_connection()`      | 获取 SQLite 数据库连接                          | ✅ 已实现          |
| `init_database()`          | 数据库初始化                                   | ✅ 已实现          |
| 数据库 Schema（`inventory` 表等） | 所有查询的基础                                  | ✅ 已实现，字段已扩展    |
| 缓存层接口                      | 热门药品查询缓存                                 | ⏭ **组件1 未提供，已跳过**（第四～五周不阻塞交付） |
| 文件上传存储接口                   | 药品图片上传 / CSV 文件上传                         | ⏭ **组件1 未提供，已跳过**（当前 batch-import 为 JSON 体；`image_url` 仍为字符串字段） |
| 统一响应格式模板                   | `{ success, data, pagination, error }` | ✅ 已实现（`common/utils/response.py`） |
| 统一错误处理格式                   | 业务路由 `{ error: { code, message } }`；鉴权路由 `{ error_code, message }` | ✅ 已实现 |


### 来自组件4（权限认证系统）


| 接口/能力                             | 用途                | 当前状态   |
| --------------------------------- | ----------------- | ------ |
| JWT 认证、`require_permission`           | 路由级鉴权      | ✅（见 `auth`；各组需对齐 token 与权限码） |
| `GET /api/users/{id}/permissions`（若使用） | 动态拉权限 | ⚠ 按需；当前以 JWT 内嵌 role/权限为主 |
| 权限装饰器                                | 后端统一装饰      | ✅ |
| RBAC 角色检查                             | 角色映射到权限码 | ✅（`ROLE_PERMISSION_MAP`） |


## 五、组件2提供给外部的 API

### 提供给组件3（智能筛选系统）


| API 端点                  | 用途                        | 当前状态                                     |
| ----------------------- | ------------------------- | ---------------------------------------- |
| `GET /api/drugs`        | 获取药品列表（含筛选）               | ✅ 已实现，支持 name/symptom/category 筛选 + 分页排序 |
| `GET /api/drugs/{id}`   | 获取单个药品详情                  | ✅ 已实现                                    |
| `GET /api/drugs/search` | 综合搜索（keyword/q + filters） | ✅ 已实现 |
| `GET /api/drugs/low-stock` | 低库存列表 | ✅ 已实现 |
| `GET /api/drugs/expiring-soon` | 临期列表 | ✅ 已实现 |
| `GET /api/drugs/stats` | 库存统计 | ✅ 已实现 |


### 提供给组件5（前端界面）


| API 端点                         | 方法     | 用途             | 当前状态   |
| ------------------------------ | ------ | -------------- | ------ |
| `GET /api/drugs`               | GET    | 药品列表（分页+排序+筛选） | ✅ 已实现  |
| `GET /api/drugs/{id}`          | GET    | 药品详情           | ✅ 已实现  |
| `POST /api/drugs`              | POST   | 创建新药品          | ✅ 已实现  |
| `PUT /api/drugs/{id}`          | PUT    | 更新药品信息         | ✅ 已实现  |
| `DELETE /api/drugs/{id}`       | DELETE | 软删除药品          | ✅ 已实现  |
| `GET /api/inventory` | GET | 拣货/库区视图（收窄字段 + 运营布尔标记，`read:inventory`） | ✅ 已实现 |
| `POST /api/drugs/{id}/adjust` | POST | 库存调整，写流水 | ✅ 已实现 |
| `GET /api/categories` | GET | 分类列表（`tree`/分页/`drug_count`） | ✅ 已实现 |
| `POST /api/categories` | POST | 创建分类 | ✅ 已实现 |
| `GET /api/drugs/search` | GET | keyword/q 综合搜索 | ✅ 已实现 |
| `POST /api/drugs/batch-import` | POST | JSON 批量导入 | ✅ 已实现 |
| `GET /api/drugs/export` | GET | 导出 JSON/CSV | ✅ 已实现 |


### 权限访问控制矩阵（需组件4 配合）


| 资源                             | 操作权限码              | 角色要求   |
| ------------------------------ | ------------------ | ------ |
| `GET /api/drugs`               | `read:drug`        | 所有角色   |
| `POST /api/drugs`              | `create:drug`      | 管理员、药剂师 |
| `PUT /api/drugs/{id}`          | `update:drug`      | 管理员、药剂师 |
| `DELETE /api/drugs/{id}`       | `delete:drug`      | 管理员    |
| `GET /api/inventory`           | `read:inventory`   | 管理员、药剂师、医生 |
| `POST /api/drugs/{id}/adjust`  | `update:inventory` | 管理员、药剂师 |
| `POST /api/drugs/batch-import` | `batch:drug`       | 管理员    |


## 六、当前代码与目标差距


| 接口                                                       | 目标                              | 当前状态       | 优先级 |
| -------------------------------------------------------- | ------------------------------- | ---------- | --- |
| `GET /api/drugs`（分页+排序）                                  | 支持 `page` / `limit` / `sort_by` | ✅ 已实现      | 高   |
| `POST /api/drugs`                                        | 创建新药品                           | ✅ 已实现      | 高   |
| `PUT /api/drugs/{id}`                                    | 更新药品                            | ✅ 已实现      | 高   |
| `DELETE /api/drugs/{id}`                                 | 删除药品                            | ✅ 已实现（软删除） | 高   |
| `GET /api/inventory` | 库区 / 拣货 JSON（白名单字段 + 补货/临期布尔） | ✅ 已实现 | 高 |
| `POST /api/drugs/{id}/adjust` | 库存调整 + `inventory_transactions` | ✅ 已实现 | 高 |
| `GET` / `POST /api/categories` | 分类管理 | ✅ 已实现 | 中 |
| `GET /api/drugs/search` | 关键词综合搜索 | ✅ 已实现 | 中 |
| `POST /api/drugs/batch-import` / `GET /api/drugs/export` | JSON 批量导入 / 导出 | ✅ 已实现 | 中 |
| JWT + `require_permission` | API 权限 | ✅（见 `auth`） | 高 |
| `GET /api/drugs/low-stock` / `expiring-soon` | 预警列表 | ✅ 已实现 | 中 |
| 订单出库写 `inventory_transactions` | 审计链完整 | ✅ 已实现（`order_controller`） | 高 |
| API 接口文档（Markdown） | 供组件3 / 组件5 | ✅ `docs/组件2-药品API接口手册.md` | 高 |
| pytest 药品/库存套件 | 组件2 自测 | ✅ `tests/test_drug_api.py` + `test_inventory_api.py`（21 用例） | 中 |
| 缓存层集成 | 依赖组件1 | ⏭ 已跳过 | 低 |
| 文件上传集成 | 依赖组件1 | ⏭ 已跳过 | 低 |


## 七、开发计划

**第 1 周：药品 CRUD + 药品模型** ✅ 已完成

- 扩展 `inventory` 表字段（28 个新列）
- 扩展 `Drug` 数据类到 35 字段
- 实现 `POST /api/drugs`、`PUT /api/drugs/{id}`、`DELETE /api/drugs/{id}`
- 给 `GET /api/drugs` 加分页 + 排序 + category 筛选
- 更新 `seed_drugs.py` 匹配新字段
- `main.py` 无需改（CRUD 全在已有 `drug_bp` 里）

**第 2 周：批量操作 + 分类管理** ✅ 已完成（详见 B 部分第二周进展）

**第 3 周：库存管理 API** ✅ 已完成

- `GET /api/inventory`、`POST /api/drugs/{id}/adjust`、`GET /api/drugs/low-stock`、`GET /api/drugs/expiring-soon`（均在 `drug_controller.py`）
- `inventory_transactions` 表由组件1 DDL 提供；手动 adjust 与 **订单出库/发药/取药**（`order_controller`）均写入流水
- 未单独新建 `inventory_controller.py`（路由合并入 `drug_bp`）

**第 4–5 周：搜索增强 + 集成联调** ✅ 已完成（缓存/文件上传见下方跳过项）

- `GET /api/drugs/search` ✅
- JWT + `require_permission` 全路由对齐 ✅
- Markdown 接口手册 ✅（`agent_with_backend/docs/组件2-药品API接口手册.md`）
- `pharmacy_client` / `http_client` / `web/js/api.js` / `admin_drugs.html` 联调 ✅
- pytest 套件 ✅（21 用例全部通过）
- ⏭ 缓存层集成 — **组件1 未提供，已跳过**
- ⏭ 文件上传（CSV multipart / 图片对象存储）— **组件1 未提供，已跳过**

### 第三周起跨组依赖（归档）


| 优先级 | 需要配合的组 | 状态 / 结论 |
| --- | --- | --- |
| 高 | **组件1** 缓存层 | ⏭ 未提供 → **已跳过**，不影响当前交付 |
| 高 | **组件1** 文件上传 | ⏭ 未提供 → **已跳过**；batch-import 维持 JSON 数组 |
| 高 | **订单 / 取药** | ✅ `order_controller` 扣库同时写 `inventory_transactions`（`type=out`） |
| 中 | **组件5** 预警 UI | ✅ `admin_drugs.html` 已接 stats / low-stock 类数据；`threshold`/`days` 与 stats 默认对齐 |
| 中 | **组件3** | ✅ 接口手册 + 组件2 自测用例可供参考；组件3 可在此基础上扩展集成测试 |

## 八、关键交付物

1. 药品完整 CRUD API（`POST/PUT/DELETE /api/drugs` + 分页排序）
2. 批量导入/导出 API（CSV/JSON）
3. 分类管理 API（categories 相关接口）
4. 库存管理 API（查询、调整、低库存预警、过期预警）
5. 综合搜索 API（`GET /api/drugs/search`）
6. Drug / Category / Inventory 数据模型
7. API 接口文档（供测试与前端联调）→ `docs/组件2-药品API接口手册.md`
8. 各 API 端点的权限矩阵配置（与组件4 对齐实现方式）→ `auth/constants.py` `ROLE_PERMISSION_MAP`
9. pytest 自测套件 → `tests/test_drug_api.py`、`tests/test_inventory_api.py`

---

# B. 开发进展

## 第一周进展（2026-05-06）

### 完成状态


| 序号  | 任务                               | 涉及文件                                       | 状态   |
| --- | -------------------------------- | ------------------------------------------ | ---- |
| 1   | 扩展 `inventory` 表字段（28 个新列）       | `init_db.py`、`database.py`、`connection.py` | ✅ 完成 |
| 2   | 扩展 `Drug` 数据类到 35 字段             | `database/models/drug.py`                  | ✅ 完成 |
| 3   | 实现 `POST /api/drugs`             | `api/drug_controller.py`                   | ✅ 完成 |
| 4   | 实现 `PUT /api/drugs/{id}`         | `api/drug_controller.py`                   | ✅ 完成 |
| 5   | 实现 `DELETE /api/drugs/{id}`（软删除） | `api/drug_controller.py`                   | ✅ 完成 |
| 6   | 给 `GET /api/drugs` 加分页+排序+筛选     | `api/drug_controller.py`                   | ✅ 完成 |
| 7   | 更新 `seed_drugs.py` 匹配新字段         | `database/scripts/seed_drugs.py`           | ✅ 完成 |
| 8   | `main.py` 无需改                    | -                                          | ✅ 确认 |


### 新增的 `inventory` 表字段

原表只有 7 列（`drug_id`, `name`, `quantity`, `expiry_date`, `shelf_x`, `shelf_y`, `shelve_id`），本周扩展后共 35 列。新增字段按用途分组如下：


| 分组    | 新增列名                  | 类型      | 说明                |
| ----- | --------------------- | ------- | ----------------- |
| 分类与价格 | `category`            | TEXT    | 药品分类（如"解热镇痛抗炎药"）  |
|       | `is_prescription`     | INTEGER | 是否处方药（0/1）        |
|       | `retail_price`        | REAL    | 零售价               |
|       | `stock`               | INTEGER | 兼容旧列，固定写 0，业务不依赖  |
| 基本信息  | `generic_name`        | TEXT    | 通用名               |
|       | `description`         | TEXT    | 药品描述              |
|       | `manufacturer`        | TEXT    | 生产厂家              |
|       | `specification`       | TEXT    | 规格                |
|       | `dosage_form`         | TEXT    | 剂型                |
|       | `unit`                | TEXT    | 单位（盒/瓶等）          |
|       | `pack_size`           | TEXT    | 包装规格              |
| 监管信息  | `approval_number`     | TEXT    | 批准文号              |
|       | `barcode`             | TEXT    | 条形码               |
| 用药信息  | `storage_condition`   | TEXT    | 储存条件              |
|       | `usage_dosage`        | TEXT    | 用法用量              |
|       | `contraindications`   | TEXT    | 禁忌                |
|       | `side_effects`        | TEXT    | 副作用               |
|       | `interaction_warning` | TEXT    | 药物相互作用            |
|       | `pregnancy_category`  | TEXT    | 孕妇用药分级            |
|       | `pediatric_caution`   | TEXT    | 儿童用药注意            |
| 供应信息  | `supplier`            | TEXT    | 供应商               |
|       | `country_of_origin`   | TEXT    | 产地                |
|       | `cost_price`          | REAL    | 进价                |
|       | `min_stock_alert`     | INTEGER | 最低库存预警值           |
|       | `image_url`           | TEXT    | 药品图片 URL          |
| 管理字段  | `is_deleted`          | INTEGER | 软删除标记（0=正常，1=已删）  |
|       | `created_at`          | TEXT    | 创建时间（UTC ISO8601） |
|       | `updated_at`          | TEXT    | 更新时间（UTC ISO8601） |


### API 行为说明

**POST `/api/drugs`**

- 必填：`name`, `quantity`, `expiry_date`, `shelf_x`, `shelf_y`, `shelve_id`
- `drug_id` 由 `MAX(drug_id)+1` 自动生成
- 可选：所有扩展字段 + `indications[]`（写入 `drug_indications` 表）
- `stock` 固定写入 0（方案 A）；`created_at`/`updated_at` 为 UTC ISO8601

**PUT `/api/drugs/{id}`**

- 仅允许白名单列更新；若带 `indications` 则整表替换该药的适应症行

**DELETE `/api/drugs/{id}`**

- 软删除：`is_deleted=1` + 更新 `updated_at`，幂等（已删返回成功提示）
- 适应症记录（`drug_indications`）当前**未随删**

**GET `/api/drugs`**

- `category=` 精确筛选
- `sort_by` + `order`（asc/desc），白名单：`drug_id`, `name`, `quantity`, `expiry_date`, `retail_price`, `category`, `shelve_id`, `created_at`, `updated_at`
- **仅当 URL 出现 `page` 或 `limit` 时分页**（默认 `page=1`, `limit=20`, 上限 100），返回 `pagination` 字段
- **不传 `page`/`limit` 时返回全量列表**，兼容 `PharmacyHTTPClient` 等旧调用
- 列表和详情均默认排除 `is_deleted=1`

**GET `/api/drugs/{id}`**

- 已删药品返回 404

### 数据约定

1. `quantity` **vs** `stock`：`quantity` 是唯一业务库存来源，`stock` 列保留仅作兼容，新写入固定 0。
2. `**expiry_date`**：表示剩余有效天数（整数），与 `main.py` 效期清扫逻辑一致，不改为日历日期。

### 其他组件需注意

- **组件3 / 组件5**：`GET /api/drugs` 不传 `page`/`limit` 时行为与之前完全相同（全量返回），**已有调用无需改动**；若想分页请加 `?page=1&limit=20`。
- **组件1**：`inventory` 表已有 35 列，迁移通过 `_add_column_if_not_exists` 进行，**不会破坏已有数据**。新环境初始化请运行 `python3 -m database.scripts.init_db`。
- **组件4**：药品与分类等业务路由已挂载 `require_permission`；前端需在请求头带 `Authorization: Bearer <token>`；角色与权限默认值见代码 `ROLE_PERMISSION_MAP`（与矩阵表若有出入例会统一）。
- **软删除**：`DELETE` 不物理删除行，`is_deleted=1` 的记录在列表/详情中不返回，但数据仍在库中。适应症表 `drug_indications` 当前未随之删除。

## 第二周进展（2026-05-13）

### 完成状态


| 序号 | 任务 | 涉及文件 | 状态 |
| --- | --- | --- | --- |
| 1 | `POST /api/drugs/batch-import`（请求体为非空 JSON 数组，每项字段与单条 POST 对齐） | `api/drug_controller.py` | ✅ 完成 |
| 2 | `GET /api/drugs/export`（未软删全量；默认 JSON；`format=csv` 或 `Accept: text/csv` 导出 CSV） | `api/drug_controller.py` | ✅ 完成 |
| 3 | `POST /api/drugs/{id}/adjust` + 写入 `inventory_transactions`（支持规范式 `quantity_change`+`transaction_type` 或与旧版兼容字段） | `api/drug_controller.py`（表结构见组件1 DDL） | ✅ 完成 |
| 4 | `GET /api/drugs/search`（`keyword`/`q`；多字段与子串 LIKE；无关键词时等同 `GET /api/drugs`） | `api/drug_controller.py` | ✅ 完成 |
| 5 | `GET /api/categories`、`POST /api/categories`（可选 `tree=1`、分页、`drug_count`）；`database/models/category.py` 模型 | `api/category_controller.py`、`database/models/category.py` | ✅ 完成 |
| 6 | `main.py` 注册 `category_bp`，药品与分类等与鉴权链路一致 | `main.py`、`auth` | ✅ 完成 |
| 7 | `GET /api/inventory` **拣货向视图**：收窄字段、`location_label` 及 `needs_restock` / `expiring_soon` 等布尔标记（非 `GET /api/drugs` 全字段） | `api/drug_controller.py` | ✅ 完成 |
| 8 | `GET /api/drugs/low-stock`、`GET /api/drugs/expiring-soon`（与 `GET /api/drugs/stats` 计数规则对齐；可调 `threshold`/`days`，可选分页） | `api/drug_controller.py` | ✅ 完成 |


### API 行为说明（摘）

- **`POST /api/drugs/batch-import`**：请求体为药品对象数组；逐条 `validate_drug`，经 `_insert_drug_row` 写库并同步适应症；需 `batch:drug`。
- **`GET /api/drugs/export`**：仅含未软删记录；CSV 时对 `indications` 等复杂字段做可导入的文本化拼接；需 `read:drug`。
- **`POST /api/drugs/{id}/adjust`**：更新 `inventory.quantity`；同时插入 `inventory_transactions`；需 `update:inventory`。
- **`GET /api/drugs/search`**：有关键词时在 `name`、`generic_name`、`description`、适应症等上做模糊检索；支持与列表接口一致的 `category`、排序与分页语义。
- **`GET/POST /api/categories`**：GET 可按树或扁平列表返回；POST 创建分类，`name` 唯一；权限以 `category_bp` 路由装饰为准。
- **`GET /api/inventory`**：拣货 / 库区视图，过滤、排序、`page/limit`、`name`、`category`、`symptom` 与 `GET /api/drugs` 对齐；每条为**库区与白名单字段**（位点、条码、单位、剂型、警戒线等），不含全文说明书类长字段；并附带 `location_label`、`needs_restock`（阈值 `threshold`，默认与 `/drugs/stats`）、`expiring_soon`（窗口 `expiring_window`，默认 30 天）、`is_expired_stock`；仍返回 `indications`；需 `read:inventory`。
- **`GET /api/drugs/low-stock`**：配置了 `min_stock_alert` 的药品判为 `quantity <= min_stock_alert`；未配置的药品与 `/drugs/stats` 的低库存计数一致地使用 `quantity < threshold`（默认 `threshold=10`）；可选分页；需 `read:inventory`。
- **`GET /api/drugs/expiring-soon`**：筛选 `0 < expiry_date <= days`（默认 `days=30`），与同口径统计对齐；过期（`expiry_date <= 0`）不在本列表内；可选分页；需 `read:inventory`。

## 第三周进展（2026-05-20）

### 完成状态


| 序号 | 任务 | 涉及文件 | 状态 |
| --- | --- | --- | --- |
| 1 | 订单/取药/配药扣库时写入 `inventory_transactions`（`transaction_type=out`，负 `quantity_change`） | `api/order_controller.py` | ✅ 完成 |
| 2 | `operator` 取自 `request.auth_user.username`；`source` 区分 order / pickup / dispense | `api/order_controller.py` | ✅ 完成 |
| 3 | 确认 `GET /api/inventory` 拣货视图与 adjust / 预警端点行为与接口清单一致 | `api/drug_controller.py` | ✅ 完成（第二周已实现，本周联调验收） |
| 4 | `database/models/category.py` 落地并在分类 API 中使用 | `database/models/category.py`、`api/category_controller.py` | ✅ 完成 |


### 行为说明（摘）

- **订单出库流水**：`create_order_for_drug()` 在 UPDATE `inventory.quantity` 前读取 `before_quantity`，扣库后 INSERT `order_log` 与 `inventory_transactions`，保证与 `POST /api/drugs/{id}/adjust` 同一审计表。
- **低库存判定**：配置了 `min_stock_alert` 的药品用 `quantity <= min_stock_alert`；未配置时 fallback 为 `quantity < threshold`（默认 10）。注意新建药品若未传 `min_stock_alert` 则默认写入 `0`，此时仅 `quantity <= 0` 会命中 per-drug 规则，联调时宜显式设置预警值。

## 第四～五周进展（2026-05-20）

### 完成状态


| 序号 | 任务 | 涉及文件 | 状态 |
| --- | --- | --- | --- |
| 1 | 扩展 `pharmacy_client.py`：search / categories / adjust / batch / export / inventory / low-stock / expiring-soon | `database/pharmacy_client.py` | ✅ 完成 |
| 2 | 扩展 `http_client.py` 与上一致；修正 `get_drug_by_id` 解析 `data` 字段 | `common/utils/http_client.py` | ✅ 完成 |
| 3 | 修复 `api.js`：`drugCategories` → `GET /categories`；补齐 search/export/inventory 等 | `web/js/api.js` | ✅ 完成 |
| 4 | 管理端接入综合搜索、分类筛选、批量导入、导出 CSV/JSON、库存调整 | `web/admin_drugs.html` | ✅ 完成 |
| 5 | 编写 Markdown API 接口手册（无 OpenAPI/Swagger） | `docs/组件2-药品API接口手册.md` | ✅ 完成 |
| 6 | pytest：`test_drug_api.py`（13）+ `test_inventory_api.py`（8），共 21 用例 | `tests/` | ✅ 完成 |
| 7 | 修复 `GET /api/drugs/export` 缺失 `_fetch_drugs_with_indications` 导致 500 | `api/drug_controller.py` | ✅ 完成 |
| 8 | 缓存层集成 | — | ⏭ **组件1 未提供，已跳过** |
| 9 | 文件上传（CSV 文件 / 图片对象存储） | — | ⏭ **组件1 未提供，已跳过** |


### 测试与文档

- **运行自测**：在 `agent_with_backend` 目录执行  
  `python3 -m pytest tests/test_drug_api.py tests/test_inventory_api.py -v`
- **接口手册**：[`agent_with_backend/docs/组件2-药品API接口手册.md`](agent_with_backend/docs/组件2-药品API接口手册.md) — 含 Base URL、JWT、15 个端点、curl 示例、组件3 用例矩阵。
- **手测脚本**：`scripts/smoke_drug_api.sh`（需自行加 Bearer Token，见手册 §2）。

### 其他组件需注意

- **组件3**：可直接依据接口手册与组件2 pytest 用例编写集成测试；搜索/列表不传 `page`/`limit` 仍为全量返回。
- **组件5**：`admin_drugs.html` 已对接后端新接口；导出支持 `format=csv|json`。
- **组件1**：若后续提供缓存或文件存储 API，组件2 可在 `drug_controller` / 前端上传处增量接入，当前不阻塞验收。

---

*说明：A 部分与组长提供的 `组件2.pdf` 内容对齐；代码路径以 `agent_with_backend/` 为前缀，便于直接定位文件。*