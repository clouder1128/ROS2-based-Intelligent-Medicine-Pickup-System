# 权限认证模块（Auth）

基于 **JWT**、**RBAC（角色 / 权限）** 与 **审计日志** 的 HTTP API，与主 Flask 应用共用 **`DATABASE_PATH`** 指定的 SQLite 库（见 `auth/db.py` + `common.config.Config`）。

## 目录说明

| 文件 | 作用 |
|------|------|
| `__init__.py` | 对外导出 `auth_bp`、`require_auth`、`require_permissions` 与各权限常量 |
| `blueprint.py` | Flask Blueprint：`/api/auth/*`、`/api/users`、`/api/roles`、`/api/permissions`、`/api/audit/*` |
| `constants.py` | 角色代码、权限码、角色 → 权限映射 |
| `db.py` | SQLite 连接（路径与主配置一致） |
| `schema.py` | 认证相关表结构、`ensure_auth_schema()`、RBAC 种子、可选默认管理员、兼容迁移与 **`users` 视图** |
| `tokens.py` | JWT 签发 / 解码、访问令牌与刷新令牌 TTL |
| `middleware.py` | `@require_auth`、`@require_permissions(...)`、`get_bearer_token`、`get_current_user_from_token` |
| `audit.py` | 审计写入封装 |

蓝图挂载前缀：**`/api`**（例如在应用中注册为 `app.register_blueprint(auth_bp)`）。

## JWT 校验策略（为何不是「每个请求自动验」）

当前 **没有** 注册 Flask 全局 `before_request` 对所有请求强制 JWT。原因是：

- **匿名接口**（登录、注册、`verify`、健康检查等）不能与「全员验 token」并存，除非维护一份较大的路径白名单。
- **业务蓝图**（药品、订单等）可按需在路由上使用 `require_auth` / `require_permissions`，逐步收紧权限。

需要「除白名单外一律 Bearer」时，可在 `main.py` 自行增加 `before_request` 钩子（与本模块的装饰器逻辑对齐即可）。

## 环境变量

在 **`agent_with_backend/.env`** 或环境中配置：

| 变量 | 说明 | 默认 |
|------|------|------|
| `AUTH_JWT_SECRET` | JWT 签名密钥（生产必填） | 若为空则回退 `FLASK_SECRET_KEY`，再不行则用不安全占位 |
| `AUTH_ACCESS_TTL_SEC` | 访问令牌有效期（秒） | `86400`（24h） |
| `AUTH_REFRESH_TTL_SEC` | 刷新令牌有效期（秒） | `604800`（7d） |
| `AUTH_DEFAULT_ADMIN_PASSWORD` | 仅在库中 **尚无用户** 时创建默认管理员密码 | 空则不创建 |
| `AUTH_DEFAULT_ADMIN_USER` | 默认管理员用户名 | `admin` |
| `AUTH_DEFAULT_ADMIN_EMAIL` | 默认管理员邮箱 | `admin@local` |
| `AUTH_DEFAULT_ADMIN_DISPLAY_NAME` | 默认管理员展示名 | 未设置则用 `AUTH_DEFAULT_ADMIN_USER` |
| `DATABASE_PATH` | 与业务库同一 SQLite 文件（认证表与库存等业务表共存） | 见 `common/config.py` |

## API 一览（均需 JSON 时注明）

### 认证

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/register` | 注册；默认角色 **`patient`**；可选 `display_name`（缺省为 `username`）；可选 `email` |
| POST | `/api/auth/login` | 用户名 + 密码 → `access_token`、`refresh_token`、`user_info`（含 `display_name`、`permissions`） |
| POST | `/api/auth/verify` | 校验 access token（Header `Bearer` 或 JSON `token` / `access_token`）；返回 `valid` 与 `user` |
| GET | `/api/auth/profile` | **Bearer** 必填；当前登录用户信息（与 `verify` 成功后的 `user` 结构一致） |
| POST | `/api/auth/logout` | 登出（可携带 refresh 作废对应会话） |
| POST | `/api/auth/refresh` | 使用 `refresh_token` 换新 access / refresh |

### 用户与 RBAC（多数需 Bearer；权限按路由装饰器）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/users` | 需 `read:users` |
| GET / PUT | `/api/users/<id>` | 按路由内逻辑：本人或 `read:users` / `write:users` 等 |
| GET | `/api/users/<id>/permissions` | **Bearer**；返回该用户权限码列表（本人或具备 `read:users`）；是否具备药品 CRUD 可由是否包含 `create:drug`、`update:drug`、`delete:drug`、`read:drug` 判断 |
| GET | `/api/roles` | 需登录 `@require_auth` |
| GET | `/api/permissions` | 需登录；Query `role_id` 可选 |
| GET | `/api/audit/logs`、`/api/audit/stats` | 需 `read:audit` |

请求头示例：

```http
Authorization: Bearer <access_token>
```

## 数据模型与架构文档对齐

- **物理表**：`auth_users`（含 `display_name`、`role_id` 等）、`auth_roles`、`auth_permissions`、`auth_role_permissions`、`auth_refresh_tokens`、`auth_audit_logs`。
- **视图 `users`**：`schema.py` 在迁移中创建，列与分工文档中的 **`users` 逻辑表** 对齐：`id, username, password_hash, role, display_name, created_at`（`role` 为四选一：`admin` | `doctor` | `pharmacist` | `patient`）。
- **旧库迁移**：若存在角色码 `user`，启动时会改为 **`patient`**；并为缺失的 `display_name` 补列、用 `username` 回填。

## 角色与权限（RBAC）

角色代码（`auth_roles.code`）：**`admin`**、**`pharmacist`**、**`doctor`**、**`patient`**（定义见 `constants.py`）。其中 **`patient`** 对应文档中的普通终端用户。

权限码示例：`read:drug`、`create:drug`、`update:drug`、`delete:drug`、`read:inventory`、`update:inventory`、`read:users`、`write:users`、`read:audit`。

默认映射概要：

- **admin**：上述全部权限  
- **pharmacist**：`read/create/update:drug`，库存 `read/update:inventory`（**不含** `delete:drug`）  
- **doctor**：`read:drug`  
- **patient**：`read:drug`  

首次调用会执行 **`ensure_auth_schema()`**：建表、**`_migrate_legacy_auth`**（视图 / 列 / 角色码迁移）、**`_seed_rbac_if_empty`** 写入角色与权限矩阵。

## 与其它模块集成

- 主入口：`main.py` 中 `register_blueprint(auth_bp)`，并在启动时调用 **`ensure_auth_schema()`**（失败仅告警时可查看控制台）。
- 业务路由可使用：`from auth import require_auth, require_permissions` 及 `PERM_*` 常量保护接口。**药品等业务蓝图是否已挂载装饰器以仓库内对应路由为准。**

## 本地验证示例

启动后端（工作目录 `agent_with_backend`，且已通过配置校验）后：

```bash
# 注册（可选 display_name）
curl -s -X POST http://localhost:8001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"secret12","email":"demo@test.local","display_name":"演示用户"}'

# 登录（取出 access_token）
curl -s -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"secret12"}'

# 携带令牌（请将 TOKEN 设为登录响应中的 access_token）
TOKEN='<access_token>'
curl -s http://localhost:8001/api/auth/profile -H "Authorization: Bearer ${TOKEN}"

# 校验 token（也可用 Header Bearer，此处演示 JSON）
curl -s -X POST http://localhost:8001/api/auth/verify \
  -H "Content-Type: application/json" \
  -d "{\"token\":\"${TOKEN}\"}"

curl -s http://localhost:8001/api/roles -H "Authorization: Bearer ${TOKEN}"

# patient 无 read:users 时列表接口应被拒（例如 403）
curl -s http://localhost:8001/api/users -H "Authorization: Bearer ${TOKEN}"
```

Shell 中务必 **`TOKEN='...'` 单独一行赋值**，再执行带 `$TOKEN` 的 `curl`，避免空令牌。

## 依赖

项目级：`PyJWT`、`Flask`、`werkzeug.security`（密码哈希）。安装见上一级 **`requirements.txt`**。
