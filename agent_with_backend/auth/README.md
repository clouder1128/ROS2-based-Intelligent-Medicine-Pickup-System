# 权限认证模块（Auth）

基于 **JWT**、**RBAC（角色 / 权限）** 与 **审计日志** 的 HTTP API，与主 Flask 应用共用 **`DATABASE_PATH`** 指定的 SQLite 库（见 `auth/db.py` + `common.config.Config`）。


## 目录说明

| 文件 | 作用 |
|------|------|
| `__init__.py` | 对外导出 `auth_bp`、`require_auth`、`require_permission`、`require_permissions` 与各 `PERM_*` 常量 |
| `blueprint.py` | Flask Blueprint：`/api/auth/*`、`/api/users`、`/api/roles`、`/api/permissions`、`/api/audit/*` |
| `constants.py` | 角色代码、权限码、`ROLE_PERMISSION_MAP`、`PERMISSION_DESCRIPTIONS` |
| `db.py` | SQLite 连接（路径与主配置一致，`PRAGMA foreign_keys = ON`） |
| `schema.py` | 认证表、`ensure_auth_schema()`、RBAC 种子、可选默认管理员、迁移、**`users` 视图**、**`_sync_permissions_and_role_mappings`** |
| `tokens.py` | JWT 签发 / 解码、Access / Refresh TTL |
| `middleware.py` | `@require_auth`、`@require_permission` / `@require_permissions`；`get_bearer_token`、`get_current_user_from_token`、`user_has_any_permission` |
| `audit.py` | 审计写入封装 `write_audit()` |

蓝图挂载前缀：**`/api`**（在 `main.py` 中 `app.register_blueprint(auth_bp)`）。

## JWT 校验策略（为何不是「每个请求自动验」）

当前 **没有** 全局 `before_request` 对所有 URL 强制 JWT：登录、注册、`verify`、健康检查等需匿名可达；药品、订单、筛选、ROS HTTP 等路由通过 **`require_auth` / `require_permission`** 按需保护。

**Access Token 载荷**（`tokens.create_access_token`，算法 HS256）：

| 字段 | 说明 |
|------|------|
| `sub` | 用户 ID（字符串） |
| `username` | 用户名 |
| `role` | 角色 code |
| `permissions` | 权限码列表（签发时快照） |
| `type` | 固定 `"access"` |
| `iat` / `exp` | 签发 / 过期时间（UTC） |

**Refresh Token**：独立 JWT（`type: "refresh"`），`jti` 写入 `auth_refresh_tokens` 表；刷新时 **吊销旧 jti 并签发新 refresh**（轮换）。

**`require_auth` / `require_permissions` 行为**：解码 JWT 后 **从数据库重新加载权限**（`permission_codes_for_user`），不单纯信任 token 内嵌的 `permissions` 快照；用户 `status != 'active'` 时返回 `AUTH_003`。

**不要求 Access JWT（Bearer）即可调用的示例**（仍可能有 Body 内 token，如 refresh / logout）：

| 方法 | 路径 |
|------|------|
| GET | `/api/health`、`/api/health/ros2` |
| POST | `/api/auth/register`、`/api/auth/login`、`/api/auth/verify`、`/api/auth/logout`、`/api/auth/refresh` |
| OPTIONS | `/api/order`（CORS 预检） |

**需 Bearer 的补充说明**（装饰器定义在各业务蓝图，非本模块路由表）：

| 前缀 / 路径 | 策略 |
|-------------|------|
| `/api/screening/*` | 多数 **`read:drug`**；**`PUT /api/screening/config`** 为 **`update:drug`** |
| `/api/ros/*`（GET） | **`require_auth`**（任意有效 token） |
| `POST /api/ros/return-to-queue` | **`update:inventory`** |
| `/api/drugs*`、`/api/inventory` 等 | 对应 `PERM_*`（见 `api/drug_controller.py`） |
| `/api/orders`（GET） | **`read:order`** |
| `/api/order`、`/api/pickup`、`/api/dispense` 等 | **`require_auth`** |

其余本模块路由（如 `/api/auth/profile`、`/api/users`）及多数写操作需 **`Authorization: Bearer <access_token>`**。

## 环境变量

在 **`agent_with_backend/.env`** 或 shell 环境中配置（`.env.example` 未列出 AUTH 项，可按需追加）：

| 变量 | 说明 | 默认 |
|------|------|------|
| `AUTH_JWT_SECRET` | JWT 签名密钥（**生产必填**） | 空则回退 `FLASK_SECRET_KEY`，再不行为 `dev-insecure-change-me` |
| `AUTH_ACCESS_TTL_SEC` | Access 有效期（秒） | `86400`（24h） |
| `AUTH_REFRESH_TTL_SEC` | Refresh 有效期（秒） | `604800`（7d） |
| `AUTH_DEFAULT_ADMIN_PASSWORD` | 仅在 **`auth_users` 为空** 时创建默认管理员 | 空则不创建 |
| `AUTH_DEFAULT_ADMIN_USER` | 默认管理员用户名 | `admin` |
| `AUTH_DEFAULT_ADMIN_EMAIL` | 默认管理员邮箱 | `admin@local` |
| `AUTH_DEFAULT_ADMIN_DISPLAY_NAME` | 默认管理员展示名 | 未设置则用 `AUTH_DEFAULT_ADMIN_USER` |
| `DATABASE_PATH` | SQLite 路径（与业务表同库） | 见 `common/config.py`（默认 `agent_with_backend/pharmacy.db`） |
| `HOST` / `PORT` | Flask 监听（**由 `main.py` / `Config` 读取，非 auth 独占**） | `0.0.0.0` / `8001` |

## API 一览

JSON 请求需 `Content-Type: application/json`。分页 Query 默认 **`page=1`**、**`limit=20`**（上限 100）。

### 认证

| 方法 | 路径 | 鉴权 | 说明 |
|------|------|------|------|
| POST | `/api/auth/register` | 无 | Body：`username`（≥2 字符）、`password`（≥6 位）；可选 `email`、`display_name`（默认等于 username）。默认角色 **`patient`**。成功：`{success, user_id, message}` |
| POST | `/api/auth/login` | 无 | Body：`username`、`password`（用户名 **不区分大小写**）。成功返回 `access_token`、`refresh_token`、`token`（同 access）、`token_type: Bearer`、`expires_in`、`refresh_expires_in`、`user_info` |
| POST | `/api/auth/verify` | 无 | Header `Bearer` 或 Body `token` / `access_token`。成功：`{success, valid: true, user}`；失败含 `valid: false` |
| GET | `/api/auth/profile` | Bearer | 成功：`{success, user}`（含 `permissions`） |
| POST | `/api/auth/logout` | 无 | 可选 Body `refresh_token` 或 `token`（吊销 refresh）；可选 Header Bearer（记录 access 对应用户）。始终 `{success, message}` |
| POST | `/api/auth/refresh` | 无 | Body：`refresh_token` 或 `token`。成功：`new_token` / `access_token`、`refresh_token`（新）、`expires_in`、`user_info` |

`user` / `user_info` 字段：`id`、`username`、`email`、`display_name`、`role`、`permissions`。

### 用户与 RBAC

| 方法 | 路径 | 鉴权 | 说明 |
|------|------|------|------|
| GET | `/api/users` | `read:users` | Query：`role`、`status`、`page`、`limit`。返回 `users` + `pagination` |
| GET | `/api/users/<id>` | Bearer | 本人或具备 `read:users` |
| PUT | `/api/users/<id>` | Bearer | 本人可改 `email`、`display_name`、`password`；**`write:users`** 可改 `status`、`role`、他人密码 |
| GET | `/api/users/<id>/permissions` | Bearer | 本人或 `read:users`；返回 `[{code}, ...]` |
| GET | `/api/roles` | Bearer | 角色列表 `id, code, name, description` |
| GET | `/api/permissions` | Bearer | 全部权限；Query `role_id` 可筛某角色权限 |
| GET | `/api/audit/logs` | `read:audit` | Query：`user_id`、`action`（LIKE）、`date_from`、`date_to`、分页 |
| GET | `/api/audit/stats` | `read:audit` | Query `period`（默认 `7d`，如 `30d`）；按 action 聚合 |

请求头示例：

```http
Authorization: Bearer <access_token>
```

### 错误码（本模块）

| 码 | 含义 |
|----|------|
| `AUTH_VAL_001` | 用户名过短 |
| `AUTH_VAL_002` | 密码过短 |
| `AUTH_VAL_003` | 用户名已存在 |
| `AUTH_VAL_004` | 登录缺少用户名或密码 |
| `AUTH_VAL_005` | `role_id` 查询参数无效 |
| `AUTH_001` | 未提供访问令牌 |
| `AUTH_002` | 令牌无效或已过期 |
| `AUTH_003` | 用户不可用（非 active 或不存在） |
| `AUTH_005` | 用户名或密码错误 |
| `AUTH_006` | 缺少 refresh_token |
| `AUTH_007` | 刷新令牌无效 |
| `AUTH_008` | 刷新令牌已吊销或不存在 |
| `AUTH_403` | 权限不足（含审计 `forbidden`） |
| `AUTH_500` | 角色未初始化 |
| `USER_001` | 用户不存在 |
| `USER_VAL_001` | 无效角色 code |

## 数据模型与架构对齐

- **物理表**：`auth_users`、`auth_roles`、`auth_permissions`、`auth_role_permissions`、`auth_refresh_tokens`、`auth_audit_logs`。
- **`auth_users`**：`username`（UNIQUE NOCASE）、`email`、`password_hash`、`display_name`、`role_id`、`status`（默认 `active`）、`created_at`、`updated_at`。
- **视图 `users`**：`id, username, password_hash, role, display_name, created_at`（`role`：`admin` \| `doctor` \| `pharmacist` \| `patient`）。
- **迁移**：旧角色码 `user` → `patient`；补 `display_name` 列；**`doctor` 与 `pharmacist` 共用同一权限矩阵**（`constants._STAFF_PERMISSIONS`），仅存不同 `auth_roles.code`；缺行时 **`_ensure_auth_role_rows`** 会补角色；**`_sync_permissions_and_role_mappings`** 按 `ROLE_PERMISSION_MAP` 增删 `auth_role_permissions`。

**审计 `action` 示例**：`register`、`login`、`login_failed`、`logout`、`token_refresh`、`user_update`、`forbidden`。

## 角色与权限（RBAC）

权限码（完整定义见 `constants.py`）：

`read:drug`、`create:drug`、`update:drug`、`delete:drug`、`read:inventory`、`update:inventory`、`batch:drug`、`read:approval`、`approve:approval`、`reject:approval`、`read:order`、`read:users`、`write:users`、`read:audit`

默认映射概要：

- **admin**：`ALL_PERMISSION_CODES` 全部权限  
- **doctor** / **pharmacist**：`_STAFF_PERMISSIONS` — 药品读/建/改；库存读/改；审批读/通过/驳回；`read:order`（**不含** `delete:drug`、`batch:drug`、`read:users`、`write:users`、`read:audit`）  
- **patient**：仅 `read:drug`  

启动时 **`ensure_auth_schema()`** 顺序：建表 → **`_migrate_legacy_auth`** → **`_seed_rbac_if_empty`** → **`_ensure_auth_role_rows`** → **`_sync_permissions_and_role_mappings`** → **`_ensure_default_admin_if_configured`**。

## 与其它模块集成

- **`main.py`**：`app.register_blueprint(auth_bp)` + **`ensure_auth_schema()`**（失败仅打印 warning，不阻断启动）。
- **`database/scripts/init_db.py`**：仅建业务表；认证表 **不** 在此脚本中创建（注释已说明由 `ensure_auth_schema()` 负责）。
- **`database/scripts/seed_users.py`**：向 `auth_users` 插入演示账号（`INSERT` 遇重名跳过）；**`setup.sh`** 第五步会调用，也可手动 `python -m database.scripts.seed_users`。
- **业务蓝图**：`from auth import require_auth, require_permission, require_permissions` 及 **`PERM_*`**；或直接 `from auth.middleware import ...`。
- **单元测试**：`tests/unit/test_auth.py`（token 往返、schema 种子、`require_auth` 401）。

## 初始化与用户来源

| 方式 | 触发条件 | 说明 |
|------|----------|------|
| `ensure_auth_schema()` | `main.py` 启动（或测试显式调用） | 建表、RBAC 种子、迁移、`users` 视图 |
| `seed_users.py` | `setup.sh` 或手动执行 | 演示用户（见下表） |
| `AUTH_DEFAULT_ADMIN_*` | `auth_users` **为空** 且 env 设了密码 | 创建单个 admin（默认用户名 `admin`） |

**演示账号**（`seed_users.py`，密码均为 **`123456`**）：

| 用户名 | 角色 | 说明 |
|--------|------|------|
| `admin1` | admin | 全部权限 |
| `doctor1` / `doctor2` | doctor | 与 pharmacist 同源权限 |
| `patient1` / `patient2` | patient | 仅 `read:drug` |

首次环境配置见仓库根目录 **`setup.sh`**；日常启动 **`agent_with_backend/quick_start.sh`**（默认端口 **8001** / 前端 **8080**）。

## 本地验证与令牌

工作目录 **`agent_with_backend`**，服务默认 **`http://127.0.0.1:8001`**（若使用 **`PORT=9000`**，下列 URL 中的端口需改掉）。需先执行过 **`setup.sh`** 或至少 **`init_db` + `seed_users` + 启动 `main.py`**，否则无演示账号。

```bash
# 使用 seed 演示账号登录（admin1 具备药品写权限）
RESP=$(curl -sS -X POST http://127.0.0.1:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin1","password":"123456"}')
TOKEN=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -sS http://127.0.0.1:8001/api/auth/profile -H "Authorization: Bearer ${TOKEN}"
```

```bash
# 自行注册 patient（默认角色 patient；用户名已存在则 AUTH_VAL_003）
curl -sS -X POST http://127.0.0.1:8001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"newuser","password":"123456","email":"new@test.local"}'
```

- **`patient1`** 仅能访问 `read:drug` 类接口；药品 CRUD 请用 **`admin1`** 或 **`doctor1`** 登录取 token。
- 调用受保护 API 时加：`-H "Authorization: Bearer ${TOKEN}"`。
- **`scripts/smoke_drug_api.sh`** 当前 **未** 携带 Bearer；直接运行会因 `AUTH_001` / `AUTH_403` 失败，需先 `login` 取 token 再改脚本或手动 curl。

```bash
# 示例：admin1 token 查询药品列表
curl -sS "http://127.0.0.1:8001/api/drugs?page=1&limit=5" \
  -H "Authorization: Bearer ${TOKEN}"
```

勿在公开场合粘贴完整 JWT（等同于临时密码）。

## 常见问题

| 现象 | 处理 |
|------|------|
| `ModuleNotFoundError: No module named 'jwt'` | `pip install PyJWT`（已写入 **`agent_with_backend/requirements.txt`**） |
| `AUTH_005` 登录失败 | 用户名或密码错误；或未执行 `seed_users`（演示账号为 `admin1`/`doctor1`/`patient1`，密码 `123456`） |
| `AUTH_VAL_003` 注册失败 | 用户名已存在，更换 `username` 或使用已有账号登录 |
| `AUTH_403` 调药品写接口 | 当前角色无对应 `PERM_*`，换 admin 或 doctor/pharmacist 账号 |
| `AUTH_008` 刷新失败 | refresh 已用过（轮换后旧 token 失效）或已 logout 吊销 |
| `Port ... is in use` | `PORT=9000 python3 main.py` 或结束占用端口的进程 |
| 无演示用户 / 表为空 | 仓库根目录 `./setup.sh`，或 `python -m database.scripts.seed_users` |

无 ROS2 时可能出现 `rclpy` 相关告警；HTTP 服务仍可在 fallback 下启动（详见 `ros_integration`）。

## 依赖

**`PyJWT`**、`Flask`、`werkzeug.security`（密码哈希）；**`flask-cors`** 等在 **`agent_with_backend/requirements.txt`**。

```bash
pip install -r requirements.txt
```
