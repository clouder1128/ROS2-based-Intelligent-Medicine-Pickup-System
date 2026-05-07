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

### 已有文件（需要扩展/完善）


| 文件路径                             | 当前状态                                          | 需要做                                         |
| -------------------------------- | --------------------------------------------- | ------------------------------------------- |
| `api/drug_controller.py`         | 仅实现了 `GET /api/drugs` 和 `GET /api/drugs/{id}` | 补充 POST/PUT/DELETE、分页、排序、筛选；搜索与批量可落在本文件或子模块 |
| `api/order_controller.py`        | 已有基础订单/取药/配药功能                                | 完善库存管理相关能力（低库存预警、效期提醒等）                     |
| `database/models/drug.py`        | Drug dataclass，字段较少                           | 扩展到 30+ 字段的完整药品模型                           |
| `database/pharmacy_client.py`    | HTTP 客户端封装                                    | 补充新 API 的客户端方法                              |
| `database/scripts/seed_drugs.py` | 100+ 种种子药品数据                                  | 随字段扩展更新种子数据                                 |
| `common/utils/drug_helpers.py`   | 药品验证辅助工具                                      | 扩展验证逻辑以支持更多字段                               |


### 需要新建的文件


| 文件路径                           | 功能          | 对应接口                                                   |
| ------------------------------ | ----------- | ------------------------------------------------------ |
| `api/inventory_controller.py`  | 库存管理 API    | `GET /api/inventory`，`POST /api/drugs/{id}/adjust`     |
| `api/category_controller.py`   | 分类管理 API    | `GET /api/categories`，`POST /api/categories`           |
| `api/batch_controller.py`      | 批量操作 API    | `POST /api/drugs/batch-import`，`GET /api/drugs/export` |
| `database/models/category.py`  | 药品分类模型      | 分类树形结构                                                 |
| `database/models/inventory.py` | 库存变化记录模型    | 库存事务记录                                                 |
| `tests/test_drug_api.py`       | 药品 API 测试套件 | CRUD + 搜索测试（**接口文档由组件2提供，测试由组件3实施**）                   |
| `tests/test_inventory_api.py`  | 库存 API 测试套件 | 库存调整、低库存预警测试                                           |


### 需要修改的共享文件（需协调其他角色）


| 文件路径                          | 修改内容                                                       | 负责角色 |
| ----------------------------- | ---------------------------------------------------------- | ---- |
| `main.py`                     | 注册新 Blueprint（`inventory_bp`, `category_bp`, `batch_bp` 等） | 组件2  |
| `common/utils/database.py`    | 添加新表结构（`categories` 表、`inventory_transactions` 表）          | 组件1  |
| `database/scripts/init_db.py` | 添加新表的初始化 SQL                                               | 组件1  |


## 四、组件2需要调用的外部 API

### 来自组件1（数据库与基础架构）


| 接口                         | 用途                                       | 当前状态           |
| -------------------------- | ---------------------------------------- | -------------- |
| `get_db_connection()`      | 获取 SQLite 数据库连接                          | ✅ 已实现          |
| `init_database()`          | 数据库初始化                                   | ✅ 已实现          |
| 数据库 Schema（`inventory` 表等） | 所有查询的基础                                  | ✅ 已实现，字段已扩展    |
| 缓存层接口                      | 热门药品查询缓存                                 | 🔴 未实现，需组件1 提供 |
| 文件上传存储接口                   | 药品图片上传管理                                 | 🔴 未实现         |
| 统一响应格式模板                   | `{ success, data, message, pagination }` | ⚠ 部分实现         |
| 统一错误处理格式                   | `{ success, error_code, message }`       | ⚠ 部分实现         |


### 来自组件4（权限认证系统）


| 接口/能力                             | 用途                | 当前状态   |
| --------------------------------- | ----------------- | ------ |
| JWT 认证中间件                         | 验证每个请求的 token     | 🔴 未实现 |
| `GET /api/users/{id}/permissions` | 检查用户是否有药品 CRUD 权限 | 🔴 未实现 |
| 权限装饰器                             | 在 API 端点上添加权限检查   | 🔴 未实现 |
| RBAC 角色检查                         | 区分管理员/医生/药剂师/普通用户 | 🔴 未实现 |


## 五、组件2提供给外部的 API

### 提供给组件3（智能筛选系统）


| API 端点                  | 用途                        | 当前状态                                     |
| ----------------------- | ------------------------- | ---------------------------------------- |
| `GET /api/drugs`        | 获取药品列表（含筛选）               | ✅ 已实现，支持 name/symptom/category 筛选 + 分页排序 |
| `GET /api/drugs/{id}`   | 获取单个药品详情                  | ✅ 已实现                                    |
| `GET /api/drugs/search` | 综合搜索药品（keyword + filters） | 🔴 未实现                                   |


### 提供给组件5（前端界面）


| API 端点                         | 方法     | 用途             | 当前状态   |
| ------------------------------ | ------ | -------------- | ------ |
| `GET /api/drugs`               | GET    | 药品列表（分页+排序+筛选） | ✅ 已实现  |
| `GET /api/drugs/{id}`          | GET    | 药品详情           | ✅ 已实现  |
| `POST /api/drugs`              | POST   | 创建新药品          | ✅ 已实现  |
| `PUT /api/drugs/{id}`          | PUT    | 更新药品信息         | ✅ 已实现  |
| `DELETE /api/drugs/{id}`       | DELETE | 软删除药品          | ✅ 已实现  |
| `GET /api/inventory`           | GET    | 库存信息展示         | 🔴 未实现 |
| `POST /api/drugs/{id}/adjust`  | POST   | 库存调整           | 🔴 未实现 |
| `GET /api/categories`          | GET    | 分类列表           | 🔴 未实现 |
| `POST /api/categories`         | POST   | 创建分类           | 🔴 未实现 |
| `GET /api/drugs/search`        | GET    | 综合搜索           | 🔴 未实现 |
| `POST /api/drugs/batch-import` | POST   | 批量导入           | 🔴 未实现 |
| `GET /api/drugs/export`        | GET    | 批量导出           | 🔴 未实现 |


### 权限访问控制矩阵（需组件4 配合）


| 资源                             | 操作权限码              | 角色要求    |
| ------------------------------ | ------------------ | ------- |
| `GET /api/drugs`               | `read:drug`        | 所有角色    |
| `POST /api/drugs`              | `create:drug`      | 管理员、药剂师 |
| `PUT /api/drugs/{id}`          | `update:drug`      | 管理员、药剂师 |
| `DELETE /api/drugs/{id}`       | `delete:drug`      | 管理员     |
| `GET /api/inventory`           | `read:inventory`   | 管理员、药剂师 |
| `POST /api/drugs/{id}/adjust`  | `update:inventory` | 管理员、药剂师 |
| `POST /api/drugs/batch-import` | `batch:drug`       | 管理员     |


## 六、当前代码与目标差距


| 接口                                                       | 目标                              | 当前状态       | 优先级 |
| -------------------------------------------------------- | ------------------------------- | ---------- | --- |
| `GET /api/drugs`（分页+排序）                                  | 支持 `page` / `limit` / `sort_by` | ✅ 已实现      | 高   |
| `POST /api/drugs`                                        | 创建新药品                           | ✅ 已实现      | 高   |
| `PUT /api/drugs/{id}`                                    | 更新药品                            | ✅ 已实现      | 高   |
| `DELETE /api/drugs/{id}`                                 | 删除药品                            | ✅ 已实现（软删除） | 高   |
| `GET /api/inventory`                                     | 库存查看                            | 🔴 未实现     | 高   |
| `POST /api/drugs/{id}/adjust`                            | 库存调整                            | 🔴 未实现     | 高   |
| `GET` / `POST /api/categories`                           | 分类管理                            | 🔴 未实现     | 中   |
| `GET /api/drugs/search`                                  | 综合搜索                            | 🔴 未实现     | 中   |
| `POST /api/drugs/batch-import` / `GET /api/drugs/export` | 批量操作                            | 🔴 未实现     | 中   |
| JWT 认证集成                                                 | 所有 API 加权限验证                    | 🔴 依赖组件4   | 高   |


## 七、开发计划

**第 1 周：药品 CRUD + 药品模型** ✅ 已完成

- 扩展 `inventory` 表字段（28 个新列）
- 扩展 `Drug` 数据类到 35 字段
- 实现 `POST /api/drugs`、`PUT /api/drugs/{id}`、`DELETE /api/drugs/{id}`
- 给 `GET /api/drugs` 加分页 + 排序 + category 筛选
- 更新 `seed_drugs.py` 匹配新字段
- `main.py` 无需改（CRUD 全在已有 `drug_bp` 里）

**第 2 周：批量操作 + 分类管理**

- 实现 `POST /api/drugs/batch-import`（CSV/JSON 批量导入）
- 实现 `GET /api/drugs/export`（导出全部药品为 JSON 等）
- 新建 `api/category_controller.py`、`database/models/category.py`
- 实现 `GET /api/categories`、`POST /api/categories`

**第 3 周：库存管理 API**

- 新建 `api/inventory_controller.py`
- 实现 `GET /api/inventory`、`POST /api/drugs/{id}/adjust`
- 新建 `database/models/inventory.py`，添加 `inventory_transactions` 表（与组件1 协调落库）
- 实现 `GET /api/drugs/low-stock`（低库存预警）、`GET /api/drugs/expiring-soon`（过期预警）

**第 4–5 周：搜索增强 + 集成联调**

- 实现 `GET /api/drugs/search`（多条件组合搜索）
- 缓存层集成（依赖组件1 缓存接口）
- JWT 认证集成交接（配合组件4）
- 编写 API 接口文档，提供给组件3 写测试
- 与组件5 前端联调，修复接口不匹配问题

## 八、关键交付物

1. 药品完整 CRUD API（`POST/PUT/DELETE /api/drugs` + 分页排序）
2. 批量导入/导出 API（CSV/JSON）
3. 分类管理 API（categories 相关接口）
4. 库存管理 API（查询、调整、低库存预警、过期预警）
5. 综合搜索 API（`GET /api/drugs/search`）
6. Drug / Category / Inventory 数据模型
7. API 接口文档（供测试与前端联调）
8. 各 API 端点的权限矩阵配置（与组件4 对齐实现方式）

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
- **组件4**：当前 API **无鉴权**，所有端点开放；待组件4 提供 JWT 中间件 / 权限装饰器后组件2 将挂载。
- **软删除**：`DELETE` 不物理删除行，`is_deleted=1` 的记录在列表/详情中不返回，但数据仍在库中。适应症表 `drug_indications` 当前未随之删除。

---

*说明：A 部分与组长提供的 `组件2.pdf` 内容对齐；代码路径以 `agent_with_backend/` 为前缀，便于直接定位文件。*
